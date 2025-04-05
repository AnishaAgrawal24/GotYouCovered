import streamlit as st
import requests
from docx import Document
from fpdf import FPDF
import fitz  # PyMuPDF
import os
from io import BytesIO
import unicodedata

# API Setup
API_URL = 'https://openrouter.ai/api/v1/chat/completions'

headers = {
    'Authorization': f'Bearer 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',
    'Content-Type': 'application/json'
}

# Utility functions
def extract_text(file):
    if file.name.endswith(".pdf"):
        doc = fitz.open(stream=file.read(), filetype="pdf")
        return " ".join(page.get_text() for page in doc)
    elif file.name.endswith(".docx"):
        doc = Document(file)
        return "\n".join(p.text for p in doc.paragraphs)
    return ""

def generate_docx(text):
    doc = Document()
    doc.add_paragraph(text)
    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

def sanitize_text(text):
    return unicodedata.normalize("NFKD", text).encode("latin-1", "ignore").decode("latin-1")

def generate_pdf(text):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    safe_text = sanitize_text(text)
    for line in safe_text.split("\n"):
        pdf.cell(200, 10, txt=line, ln=True)

    pdf_bytes = pdf.output(dest='S').encode('latin-1')  # Get PDF as bytes
    buffer = BytesIO(pdf_bytes)                         # Put bytes into buffer
    buffer.seek(0)
    return buffer

# App UI
st.title("📝 AutoCoverLetter")

resume_file = st.file_uploader("Upload your resume (.pdf or .docx)", type=["pdf", "docx"])
job_title = st.text_input("Enter the job title or description")
tone = st.selectbox("Choose a tone", ["Professional", "Friendly", "Enthusiastic"])

# Initialize session state
if 'final_text' not in st.session_state:
    st.session_state.final_text = None

if resume_file and job_title and st.button("Generate Cover Letter"):
    resume_text = extract_text(resume_file)

    prompt = f"""
    Write a {tone.lower()} cover letter for the following job:
    Job: {job_title}
    Resume: {resume_text[:4000]}
    """

    with st.spinner("Generating..."):
        data = {
            "model": "deepseek/deepseek-chat:free",
            "messages": [
                {
                    "role": "system",
                    "content": "You are a cover letter generator. Extract the candidate's name, email, and any contact info "
                               "from the resume and include it in the letter. Only return the final cover letter text. "
                               "Do not explain, apologize, or output anything else."
                },
                {"role": "user", "content": prompt}
            ]
        }

        os.environ['NO_PROXY'] = 'openrouter.ai'
        response = requests.post(API_URL, json=data, headers=headers)

        if response.status_code == 200:
            st.session_state.final_text = response.json()["choices"][0]["message"]["content"]
        else:
            st.error(f"Failed to fetch data from API. Status Code: {response.status_code}")

# Display output and download options
if st.session_state.final_text:
    st.subheader("Generated Cover Letter")
    st.text_area("Output", st.session_state.final_text, height=300)

    file_format = st.selectbox("Choose format to download", ["TXT", "DOCX", "PDF"])

    save_text = st.session_state.final_text

    if file_format == "TXT":
        txt_buffer = BytesIO(save_text.encode("utf-8"))
        st.download_button("📄 Download TXT", txt_buffer, file_name="Cover_Letter.txt")

    elif file_format == "DOCX":
        file = generate_docx(save_text)
        st.download_button("📄 Download DOCX", file, file_name="Cover_Letter.docx")

    elif file_format == "PDF":
        file = generate_pdf(save_text)
        st.download_button("📄 Download PDF", file, file_name="Cover_Letter.pdf")
