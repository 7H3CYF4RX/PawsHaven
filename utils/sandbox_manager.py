"""
Sandbox Manager — Creates, seeds, and manages per-user isolated environments.
Each user gets their own SQLite database, file directories, and pre-seeded data.
"""
import os
import uuid
import json
import sqlite3
from config import Config
from utils.password_utils import hash_password
from fpdf import FPDF


def create_sandbox(user_data):
    """Create a new sandbox for a user and return the sandbox_id."""
    sandbox_id = str(uuid.uuid4())[:12]
    sandbox_dir = os.path.join(Config.SANDBOX_DIR, sandbox_id)

    # Create directory structure
    os.makedirs(sandbox_dir, exist_ok=True)
    os.makedirs(os.path.join(sandbox_dir, 'uploads', 'avatars'), exist_ok=True)
    os.makedirs(os.path.join(sandbox_dir, 'receipts'), exist_ok=True)
    os.makedirs(os.path.join(sandbox_dir, 'documents'), exist_ok=True)
    os.makedirs(os.path.join(sandbox_dir, 'exports'), exist_ok=True)
    os.makedirs(os.path.join(sandbox_dir, 'admin_queue'), exist_ok=True)

    # Create and seed database
    db_path = os.path.join(sandbox_dir, 'db.sqlite')
    _init_database(db_path, user_data, sandbox_id)

    # Create seed documents for LFI
    _create_seed_documents(sandbox_dir)

    # Create seed receipts for forced browsing
    _create_seed_receipts(sandbox_dir)

    # Determine role based on email domain (VULN: Auto-promotion)
    role = 'admin' if user_data['email'].lower().endswith('@pawshaven.org') else 'user'

    # Save profile JSON (mass assignment target)
    profile = {
        'name': user_data['name'],
        'email': user_data['email'],
        'role': role,
        'phone': '',
        'address': '',
        'bio': '',
        'sandbox_id': sandbox_id
    }
    with open(os.path.join(sandbox_dir, 'profile.json'), 'w') as f:
        json.dump(profile, f, indent=2)

    return sandbox_id


def _init_database(db_path, user_data, sandbox_id):
    """Initialize and seed the sandbox SQLite database."""
    conn = sqlite3.connect(db_path)

    # Create tables
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT DEFAULT 'user',
            phone TEXT DEFAULT '',
            address TEXT DEFAULT '',
            bio TEXT DEFAULT '',
            sandbox_id TEXT,
            two_factor_enabled INTEGER DEFAULT 0,
            otp_code TEXT DEFAULT '',
            avatar_url TEXT DEFAULT '',
            sent_emails INTEGER DEFAULT 0,
            is_premium INTEGER DEFAULT 0,
            active_theme TEXT DEFAULT 'default',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS animals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            species TEXT NOT NULL,
            breed TEXT DEFAULT '',
            age TEXT DEFAULT '',
            gender TEXT DEFAULT '',
            description TEXT DEFAULT '',
            medical_notes TEXT DEFAULT '',
            status TEXT DEFAULT 'available',
            image_url TEXT DEFAULT '',
            added_by INTEGER DEFAULT 1,
            added_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS medical_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            animal_id INTEGER,
            record_type TEXT,
            diagnosis TEXT,
            treatment TEXT,
            vet_name TEXT,
            date TEXT,
            notes TEXT DEFAULT '',
            FOREIGN KEY (animal_id) REFERENCES animals(id)
        );

        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            animal_id INTEGER,
            date TEXT,
            time TEXT,
            type TEXT DEFAULT 'checkup',
            notes TEXT DEFAULT '',
            status TEXT DEFAULT 'scheduled',
            FOREIGN KEY (user_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS adoptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            animal_id INTEGER,
            status TEXT DEFAULT 'pending',
            reason TEXT DEFAULT '',
            admin_notes TEXT DEFAULT '',
            applied_at TEXT DEFAULT CURRENT_TIMESTAMP,
            reviewed_at TEXT,
            approved_at TEXT,
            certificate_path TEXT
        );

        CREATE TABLE IF NOT EXISTS donations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            amount REAL,
            coupon_code TEXT DEFAULT '',
            discount REAL DEFAULT 0,
            final_amount REAL,
            receipt_path TEXT DEFAULT '',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS coupons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE,
            discount_percent INTEGER,
            max_uses INTEGER DEFAULT 1,
            times_used INTEGER DEFAULT 0,
            active INTEGER DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS stray_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            reporter_id INTEGER,
            location TEXT,
            description TEXT,
            animal_type TEXT DEFAULT 'unknown',
            urgency TEXT DEFAULT 'normal',
            image_path TEXT DEFAULT '',
            status TEXT DEFAULT 'pending',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            animal_id INTEGER DEFAULT NULL,
            content TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS contact_submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT,
            subject TEXT,
            message TEXT,
            ip_address TEXT DEFAULT '',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS password_reset_tokens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            token TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            used INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS newsletter (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT,
            name TEXT DEFAULT '',
            template TEXT DEFAULT '',
            subscribed_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # Seed the registering user (VULN: Auto-promotion based on domain)
    role = 'admin' if user_data['email'].lower().endswith('@pawshaven.org') else 'user'
    conn.execute(
        "INSERT INTO users (name, email, password_hash, role, sandbox_id) VALUES (?, ?, ?, ?, ?)",
        [user_data['name'], user_data['email'], user_data['password_hash'], role, sandbox_id]
    )

    # Seed fake users for IDOR
    fake_users = [
        ('Dr. Sarah Mitchell', 'dr.mitchell@pawshaven.org', hash_password('sarah2024'), 'vet', sandbox_id),
        ('James Cooper', 'j.cooper@email.com', hash_password('james123'), 'adopter', sandbox_id),
        ('Maria Garcia', 'm.garcia@email.com', hash_password('maria456'), 'volunteer', sandbox_id),
        ('Admin Account', 'admin@pawshaven.org', hash_password('admin2024'), 'admin', sandbox_id),
        ('Emily Watson', 'e.watson@email.com', hash_password('emily789'), 'donor', sandbox_id),
    ]
    conn.executemany(
        "INSERT INTO users (name, email, password_hash, role, sandbox_id) VALUES (?, ?, ?, ?, ?)",
        fake_users
    )

    # Seed animals
    animals = [
        ('Luna', 'Dog', 'Golden Retriever', '2 years', 'Female', 'Friendly and playful golden retriever rescued from a puppy mill. Loves belly rubs and long walks.', 'Vaccinated, spayed, microchipped', 'available', '/static/img/animals/dog1.jpg'),
        ('Milo', 'Cat', 'Tabby', '1 year', 'Male', 'Affectionate tabby who loves to cuddle. Great with children and other cats.', 'Vaccinated, neutered', 'available', '/static/img/animals/cat1.jpg'),
        ('Rocky', 'Dog', 'German Shepherd', '4 years', 'Male', 'Recovering from leg surgery. Needs a patient and loving home with a yard.', 'Ongoing treatment for leg injury', 'medical_hold', '/static/img/animals/dog2.jpg'),
        ('Bella', 'Cat', 'Persian', '3 years', 'Female', 'Elegant persian cat with a calm temperament. Prefers quiet environments.', 'Vaccinated, spayed, dental cleaning done', 'available', '/static/img/animals/cat2.jpg'),
        ('Max', 'Dog', 'Labrador', '1 year', 'Male', 'Energetic lab puppy who loves swimming and playing fetch. Great family dog.', 'Vaccinated, neutered, microchipped', 'available', '/static/img/animals/dog3.jpg'),
        ('Whiskers', 'Cat', 'Siamese', '5 years', 'Male', 'Talkative siamese with striking blue eyes. Bonds deeply with one person.', 'Vaccinated, neutered, kidney diet', 'available', '/static/img/animals/cat3.jpg'),
        ('Daisy', 'Dog', 'Beagle', '3 years', 'Female', 'Sweet beagle who was found as a stray. Excellent nose and gentle disposition.', 'Vaccinated, spayed', 'available', '/static/img/animals/dog4.jpg'),
        ('Shadow', 'Cat', 'Black Domestic', '2 years', 'Male', 'Sleek black cat who is shy at first but incredibly loyal once he trusts you.', 'Vaccinated, neutered', 'available', '/static/img/animals/cat4.jpg'),
        ('Buddy', 'Dog', 'Mixed Breed', '6 years', 'Male', 'Calm and well-trained mixed breed. Perfect for seniors or apartment living.', 'Vaccinated, neutered, on heart medication', 'available', '/static/img/animals/dog5.jpg'),
        ('Cleo', 'Cat', 'Maine Coon', '4 years', 'Female', 'Majestic maine coon with a fluffy tail. Loves being brushed and playing with feather toys.', 'Vaccinated, spayed', 'available', '/static/img/animals/cat5.jpg'),
        ('Rex', 'Dog', 'Boxer', '2 years', 'Male', 'High-energy boxer who needs lots of exercise. Great with active families.', 'Vaccinated, neutered', 'available', '/static/img/animals/dog6.jpg'),
        ('Olive', 'Cat', 'Calico', '1 year', 'Female', 'Playful calico kitten with beautiful tri-color markings. Gets along with dogs.', 'Vaccinated, to be spayed', 'available', '/static/img/animals/cat6.jpg'),
        ('Duke', 'Dog', 'Husky', '3 years', 'Male', 'Stunning husky with heterochromia. Needs experienced owner and cold-weather environment.', 'Vaccinated, neutered, eye exam clear', 'available', '/static/img/animals/dog7.jpg'),
        ('Mittens', 'Cat', 'Ragdoll', '2 years', 'Female', 'Loves being held like a baby. True to ragdoll nature — goes limp when picked up.', 'Vaccinated, spayed', 'adopted', '/static/img/animals/cat7.jpg'),
        ('Charlie', 'Dog', 'Poodle', '5 years', 'Male', 'Hypoallergenic standard poodle. Very intelligent and easy to train.', 'Vaccinated, neutered, allergy-friendly', 'available', '/static/img/animals/dog8.jpg'),
        ('Patches', 'Rabbit', 'Holland Lop', '1 year', 'Female', 'Adorable lop-eared bunny. Litter trained and loves fresh vegetables.', 'Spayed, healthy', 'available', '/static/img/animals/rabbit1.jpg'),
        ('Kiwi', 'Bird', 'Cockatiel', '3 years', 'Male', 'Talkative cockatiel who can whistle popular tunes. Comes with cage and supplies.', 'Healthy, regular wing clip', 'available', '/static/img/animals/bird1.jpg'),
        ('Thor', 'Dog', 'Pit Bull', '2 years', 'Male', 'Gentle giant who was surrendered by previous owner. Loves kids and cuddles.', 'Vaccinated, neutered, behavior assessed', 'available', '/static/img/animals/dog9.jpg'),
        ('Princess', 'Cat', 'Scottish Fold', '4 years', 'Female', 'Charming scottish fold with folded ears. Indoor cat who loves window perching.', 'Vaccinated, spayed', 'available', '/static/img/animals/cat8.jpg'),
        ('Cooper', 'Dog', 'Corgi', '1 year', 'Male', 'Adorable corgi puppy with stubby legs and big personality. House-trained.', 'Vaccinated, neutered, microchipped', 'available', '/static/img/animals/dog10.jpg'),
    ]
    conn.executemany(
        "INSERT INTO animals (name, species, breed, age, gender, description, medical_notes, status, image_url) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        animals
    )

    # Seed medical records
    medical_records = [
        (1, 'vaccination', 'Routine vaccination', 'Rabies + DHPP administered', 'Dr. Sarah Mitchell', '2024-03-15', 'Next booster in 12 months'),
        (1, 'checkup', 'Annual wellness exam', 'All vitals normal', 'Dr. Sarah Mitchell', '2024-03-15', 'Weight: 65 lbs, healthy'),
        (3, 'surgery', 'Fractured right hind leg', 'Surgical repair with titanium plate', 'Dr. Sarah Mitchell', '2024-02-20', 'Recovery estimated 8 weeks. Physical therapy recommended.'),
        (3, 'followup', 'Post-surgery checkup', 'Healing well, reduced inflammation', 'Dr. Sarah Mitchell', '2024-03-10', 'Continue antibiotics for 2 more weeks'),
        (5, 'vaccination', 'Puppy vaccination series', 'DHPP dose 2 of 3', 'Dr. James Wilson', '2024-04-01', 'Final dose due in 4 weeks'),
        (9, 'prescription', 'Heart murmur detected', 'Enalapril 5mg daily', 'Dr. Sarah Mitchell', '2024-01-10', 'Monitor breathing rate at home'),
    ]
    conn.executemany(
        "INSERT INTO medical_records (animal_id, record_type, diagnosis, treatment, vet_name, date, notes) VALUES (?, ?, ?, ?, ?, ?, ?)",
        medical_records
    )

    # Seed appointments
    appointments = [
        (1, 1, '2024-04-20', '10:00', 'checkup', 'Annual wellness check for Luna', 'scheduled'),
        (2, 5, '2024-04-22', '14:30', 'vaccination', 'Final puppy vaccination for Max', 'scheduled'),
        (3, 3, '2024-04-18', '09:00', 'followup', 'Post-surgery checkup for Rocky', 'completed'),
        (1, 9, '2024-04-25', '11:00', 'prescription', 'Heart medication refill for Buddy', 'scheduled'),
        (4, 10, '2024-04-19', '15:00', 'grooming', 'Full grooming session for Cleo', 'completed'),
    ]
    conn.executemany(
        "INSERT INTO appointments (user_id, animal_id, date, time, type, notes, status) VALUES (?, ?, ?, ?, ?, ?, ?)",
        appointments
    )

    # Seed coupons
    coupons = [
        ('RESCUE25', 25, 1, 0, 1),
        ('PAWSFRIEND10', 10, 3, 1, 1),
        ('ADOPT2024', 50, 1, 1, 1),
    ]
    conn.executemany(
        "INSERT INTO coupons (code, discount_percent, max_uses, times_used, active) VALUES (?, ?, ?, ?, ?)",
        coupons
    )

    # Seed stray reports
    stray_reports = [
        (2, 'Oak Street Park, near the fountain', 'Spotted a limping dog near the park. Medium-sized, brown fur, no collar.', 'Dog', 'high', '', 'pending'),
        (3, 'Downtown alley behind 5th Ave Market', 'Several kittens found in a cardboard box. Appear to be about 4 weeks old.', 'Cat', 'urgent', '', 'in_progress'),
        (5, 'Riverside Trail, mile marker 3', 'Injured bird with broken wing on the trail path. Appears to be a hawk.', 'Bird', 'normal', '', 'resolved'),
    ]
    conn.executemany(
        "INSERT INTO stray_reports (reporter_id, location, description, animal_type, urgency, image_path, status) VALUES (?, ?, ?, ?, ?, ?, ?)",
        stray_reports
    )

    # Seed donations
    donations = [
        (5, 100.00, '', 0, 100.00, 'receipt_001.pdf', '2024-03-01'),
        (2, 50.00, 'PAWSFRIEND10', 10, 45.00, 'receipt_002.pdf', '2024-03-15'),
    ]
    conn.executemany(
        "INSERT INTO donations (user_id, amount, coupon_code, discount, final_amount, receipt_path, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        donations
    )

    conn.commit()
    conn.close()


def _create_seed_documents(sandbox_dir):
    """Create seed documents for LFI testing."""
    docs_dir = os.path.join(sandbox_dir, 'documents')

    with open(os.path.join(docs_dir, 'vaccination_template.html'), 'w') as f:
        f.write("""<h2>PawsHaven Vaccination Certificate</h2>
<p>This certifies that the animal has received all required vaccinations.</p>
<p>Issued by: PawsHaven Veterinary Clinic</p>""")

    with open(os.path.join(docs_dir, 'diagnosis_report.html'), 'w') as f:
        f.write("""<h2>Veterinary Diagnosis Report</h2>
<p>Patient information and diagnosis details are confidential.</p>
<p>Internal reference: VET-2024-CONF</p>""")


def _create_seed_receipts(sandbox_dir):
    """Create seed receipt PDFs for forced browsing."""
    receipts_dir = os.path.join(sandbox_dir, 'receipts')

    for i in range(1, 4):
        filepath = os.path.join(receipts_dir, f'receipt_{i:03d}.pdf')
        donor_name = 'Emily Watson' if i != 2 else 'James Cooper'
        amount = [100, 45, 250][i-1]
        
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font('helvetica', 'B', 16)
        pdf.cell(0, 10, f'PAWSHAVEN DONATION RECEIPT #{i:03d}', align='C', new_x='LMARGIN', new_y='NEXT')
        pdf.set_font('helvetica', '', 12)
        pdf.cell(0, 10, f'Date: 2024-0{i}-{10+i}', new_x='LMARGIN', new_y='NEXT')
        pdf.cell(0, 10, f'Donor: {donor_name}', new_x='LMARGIN', new_y='NEXT')
        pdf.cell(0, 10, f'Transaction ID: TXN-2024-{1000+i}', new_x='LMARGIN', new_y='NEXT')
        pdf.cell(0, 10, f'Amount: ${amount:.2f}', new_x='LMARGIN', new_y='NEXT')
        pdf.cell(0, 10, 'Thank you for your generous donation!', new_x='LMARGIN', new_y='NEXT')
        pdf.cell(0, 10, 'PawsHaven is a registered 501(c)(3) nonprofit. EIN: 84-1234567', new_x='LMARGIN', new_y='NEXT')
        pdf.output(filepath)
