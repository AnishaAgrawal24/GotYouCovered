import streamlit as st
from openai import OpenAI
from docx import Document
import fitz  # PyMuPDF

client = OpenAI(api_key=st.secrets["api_keys"]["OPENAI_API_KEY"])

def extract_text(file):
    if file.name.endswith(".pdf"):
        doc = fitz.open(stream=file.read(), filetype="pdf")
        return " ".join(page.get_text() for page in doc)
    elif file.name.endswith(".docx"):
        doc = Document(file)
        return "\n".join(p.text for p in doc.paragraphs)
    return ""

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
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
        )
        letter = response.choices[0].message.content
        st.subheader("Generated Cover Letter")
        st.text_area("Output", letter, height=300)
        st.download_button("Download as .txt", letter, file_name="cover_letter.txt")
