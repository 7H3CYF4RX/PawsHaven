import os
from fpdf import FPDF
from datetime import datetime

class AdoptionCertificate(FPDF):
    def header(self):
        # Draw a nice border
        self.set_line_width(2)
        self.rect(5, 5, 200, 287)
        self.set_line_width(0.5)
        self.rect(7, 7, 196, 283)
        
        # Logo placeholder (Paw Icon)
        self.set_font('Arial', 'B', 40)
        self.set_text_color(45, 106, 79) # Brand Primary
        self.cell(0, 40, 'PAWSHAVEN', ln=True, align='C')
        
        self.set_font('Arial', 'I', 12)
        self.set_text_color(100, 100, 100)
        self.cell(0, 10, 'Where Every Life Finds a Forever Home', ln=True, align='C')
        self.ln(20)

    def footer(self):
        self.set_y(-30)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f'Certificate ID: {self.cert_id} | Issued on {datetime.now().strftime("%Y-%m-%d")}', align='C')

def generate_adoption_certificate(output_path, user_name, animal_name, breed, species, adoption_date, cert_id):
    pdf = AdoptionCertificate()
    pdf.cert_id = cert_id
    pdf.set_auto_page_break(auto=False, margin=0)
    pdf.add_page()
    
    # Title
    pdf.set_font('Times', 'B', 28)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(5)
    pdf.cell(0, 15, 'OFFICIAL CERTIFICATE', ln=True, align='C')
    pdf.set_font('Times', 'B', 22)
    pdf.cell(0, 15, 'OF ADOPTION', ln=True, align='C')
    pdf.ln(10)
    
    # Main Content
    pdf.set_font('Arial', '', 14)
    pdf.multi_cell(0, 8, f'This certifies that the lovely {species}', align='C')
    pdf.ln(4)
    
    pdf.set_font('Arial', 'B', 24)
    pdf.set_text_color(45, 106, 79)
    pdf.cell(0, 18, animal_name.upper(), ln=True, align='C')
    pdf.ln(4)
    
    pdf.set_font('Arial', '', 14)
    pdf.set_text_color(0, 0, 0)
    pdf.multi_cell(0, 8, f'a beautiful {breed}, has been officially adopted by', align='C')
    pdf.ln(4)
    
    pdf.set_font('Arial', 'B', 22)
    pdf.set_text_color(224, 122, 47) # Brand Secondary
    pdf.cell(0, 18, user_name.upper(), ln=True, align='C')
    pdf.ln(10)
    
    pdf.set_font('Arial', '', 12)
    pdf.set_text_color(0, 0, 0)
    pdf.multi_cell(0, 8, f'on this day, {adoption_date}.', align='C')
    pdf.ln(8)
    
    pdf.set_font('Arial', 'I', 11)
    pdf.multi_cell(0, 7, 'By signing this certificate, the new owner promises to provide a safe, loving, and healthy environment for their new companion.', align='C')
    
    # Signatures
    pdf.ln(20)
    y_pos = pdf.get_y()
    
    # Left Signature
    pdf.line(30, y_pos, 90, y_pos)
    pdf.set_xy(30, y_pos + 2)
    pdf.set_font('Arial', '', 10)
    pdf.cell(60, 10, 'Platform Administrator', align='C')
    
    # Right Signature
    pdf.line(120, y_pos, 180, y_pos)
    pdf.set_xy(120, y_pos + 2)
    pdf.cell(60, 10, 'New Guardian', align='C')
    
    # Paw Print decoration
    pdf.set_draw_color(45, 106, 79)
    pdf.set_fill_color(45, 106, 79)
    cx, cy = 105, 250
    pdf.ellipse(cx-10, cy-10, 20, 15, 'F') # Pad
    pdf.ellipse(cx-15, cy-20, 8, 10, 'F')  # Toes
    pdf.ellipse(cx-5, cy-25, 8, 10, 'F')
    pdf.ellipse(cx+7, cy-20, 8, 10, 'F')

    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    pdf.output(output_path)
