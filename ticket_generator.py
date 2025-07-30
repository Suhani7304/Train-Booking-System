from fpdf import FPDF
from io import BytesIO

def generate_ticket_pdf(data):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    for key, value in data.items():
        pdf.cell(200, 10, txt=f"{key.capitalize()}: {value}", ln=True)

    pdf_output = pdf.output(dest='S').encode('latin1')
    return BytesIO(pdf_output)