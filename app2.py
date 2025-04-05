import streamlit as st
import requests

from docx import Document
from fpdf import FPDF

import fitz  # PyMuPDF
# from face import generator
from salmon import generate_cover_letter
import secrets as s

import os
# client = OpenAI(api_key=st.secrets["api_keys"]["OPENAI_API_KEY"])
# client  = OpenAI(api_key="sk-cd9eda74d5804f918597dabcd8e32f87", base_url = "https://api.deepseek.com")

# Define the headers for the API request
API_URL = 'https://openrouter.ai/api/v1/chat/completions'

headers = {
    'Authorization': f'Bearer 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',
    'Content-Type': 'application/json'
}



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

def generate_pdf(text):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    for line in text.split("\n"):
        pdf.cell(200, 10, txt=line, ln=True)
    buffer = BytesIO()
    pdf.output(buffer)
    buffer.seek(0)
    return buffer
st.title("📝 AutoCoverLetter")

resume_file = st.file_uploader("Upload your resume (.pdf or .docx)", type=["pdf", "docx"])
job_title = st.text_input("Enter the job title or description")
tone = st.selectbox("Choose a tone", ["Professional", "Friendly", "Enthusiastic"])

if st.button("Generate Cover Letter") and resume_file and job_title:
    resume_text = extract_text(resume_file)


    prompt = f"""
    Write a {tone.lower()} cover letter for the following job:
    Job: {job_title}
    Resume: {resume_text[:4000]}
    """
    with st.spinner("Generating..."):
        # Define the request payload (data)
        data = {
            "model": "deepseek/deepseek-chat:free",
            "messages": [
                {"role": "system", "content": "You are a cover letter generator. Extract the candidate's name, email, and any contact info "
            "from the resume and include it in the letter. Only return the final cover letter text. "
            "Do not explain, apologize, or output anything else."},

                {"role": "user", "content": prompt}
                ]
        }
        
        os.environ['NO_PROXY'] = 'openrouter.ai'

        response = requests.post(API_URL, json=data, headers=headers)

        if response.status_code == 200:
            final_text =  response.json()["choices"][0]["message"]["content"]
            st.session_state.final_text = final_text

            print("API Response:", response.json())
            st.subheader("Generated Cover Letter")
            st.text_area("Output", st.session_state.final_text, height=300)
            
            file_format = st.selectbox("Choose format", ["TXT", "DOCX", "PDF"])

            if st.button("Generate File"):
                save_text = st.session_state.final_text
                if file_format == "TXT":
                    st.download_button("Download as .txt", save_text, file_name="Cover Letter.txt")
                if file_format == "DOCX":
                    file = generate_docx(save_text)
                    st.download_button("Download DOCX", file, "Cover Letter.docx")
                else:
                    file = generate_pdf(save_text)
                    st.download_button("Download PDF", file, "Cover Letter.pdf")
        else:
            print("Failed to fetch data from API. Status Code:", response.status_code)
