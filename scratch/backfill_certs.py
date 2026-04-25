import os
import sqlite3
import sys

# Add current directory to path
sys.path.append(os.getcwd())
from config import Config
from utils.certificate_gen import generate_adoption_certificate

def backfill():
    sandbox_dir = Config.SANDBOX_DIR
    if not os.path.exists(sandbox_dir):
        return
    
    for sandbox_id in os.listdir(sandbox_dir):
        db_path = os.path.join(sandbox_dir, sandbox_id, 'db.sqlite')
        if os.path.exists(db_path):
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Find approved adoptions
            adoptions = cursor.execute("""
                SELECT a.*, u.name as user_name, an.name as animal_name, an.breed, an.species 
                FROM adoptions a
                JOIN users u ON a.user_id = u.id
                JOIN animals an ON a.animal_id = an.id
                WHERE a.status = 'approved'
            """).fetchall()
            
            for a in adoptions:
                cert_filename = f"receipt_{a['id']:03d}.pdf"
                cert_dir = os.path.join(sandbox_dir, sandbox_id, 'receipts')
                cert_path = os.path.join(cert_dir, cert_filename)
                
                # Overwrite existing for backfill
                print(f"Generating cert for {sandbox_id} - Adoption {a['id']}")
                generate_adoption_certificate(
                    output_path=cert_path,
                    user_name=a['user_name'],
                    animal_name=a['animal_name'],
                    breed=a['breed'],
                    species=a['species'],
                    adoption_date=a['approved_at'] or a['applied_at'],
                    cert_id=f"PH-{a['id']:05d}"
                )
                cursor.execute("UPDATE adoptions SET certificate_path = ? WHERE id = ?", [cert_filename, a['id']])
            
            conn.commit()
            conn.close()

if __name__ == "__main__":
    backfill()
