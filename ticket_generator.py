from fpdf import FPDF
import os

def generate_ticket_pdf(data):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    for key, value in data.items():
        pdf.cell(200, 10, txt=f"{key.capitalize()}: {value}", ln=True)

    if not os.path.exists("static"):
        os.mkdir("static")
    pdf.output("static/ticket.pdf")
