from fpdf import FPDF
from io import BytesIO

def generate_ticket_pdf(data):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    for key, value in data.items():
        pdf.cell(200, 10, txt=f"{key.capitalize()}: {value}", ln=True)

    # Output to BytesIO
    pdf_bytes = BytesIO()
    pdf.output(pdf_bytes)
    pdf_bytes.seek(0)  # reset pointer to start
    return pdf_bytes
