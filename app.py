import streamlit as st
import pandas as pd
from datetime import date
import openai
from PyPDF2 import PdfReader
import docx
import os
from dotenv import load_dotenv  # NEW

# =============================
# LOAD ENV VARIABLES
# =============================
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# =============================
# CONFIGURATION
# =============================
st.set_page_config(page_title="Trackfolio")

# HELPER FUNCTIONS

# Extract text from PDF
def extract_text_from_pdf(file):
    try:
        reader = PdfReader(file)
        return "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])
    except Exception as e:
        return f"Error reading PDF: {e}"

# Extract text from DOCX
def extract_text_from_docx(file):
    try:
        doc = docx.Document(file)
        return "\n".join([para.text for para in doc.paragraphs])
    except Exception as e:
        return f"Error reading DOCX: {e}"

# Detect file type and extract text
def get_cv_text(uploaded_file):
    if uploaded_file.name.endswith(".pdf"):
        return extract_text_from_pdf(uploaded_file)
    elif uploaded_file.name.endswith(".docx"):
        return extract_text_from_docx(uploaded_file)
    else:
        return ""

# Compare CV with Job Description
def analyze_cv_fit(cv_text, jd_text):
    prompt = f"""
    Compare this candidate's CV with the following job description.
    CV:\n{cv_text}\n
    Job Description:\n{jd_text}\n
    Provide:
    1. Strengths relevant to the job.
    2. Missing skills/experience.
    3. Overall match score out of 10.
    """
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        )
        return response['choices'][0]['message']['content']
    except Exception as e:
        return f"Error analyzing CV: {e}"

# Generate AI Interview Questions
def generate_interview_questions(jd_text, role):
    prompt = f"""
    Generate 5 job-specific interview questions with suggested answers for a {role}.
    Job Description:\n{jd_text}
    """
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        )
        return response['choices'][0]['message']['content']
    except Exception as e:
        return f"Error generating questions: {e}"

# File where applications are stored
DATA_FILE = "data/job_tracker.csv"

# Load tracker data
def load_tracker():
    if not os.path.exists(DATA_FILE) or os.path.getsize(DATA_FILE) == 0:
        return pd.DataFrame(columns=["Company", "Position", "Date Applied", "Status", "Notes"])
    return pd.read_csv(DATA_FILE)

def save_tracker(df):
    df.to_csv(DATA_FILE, index=False)

# UI ELEMENTS

st.title("Trackfolio")
st.markdown("Your personal AI assistant for tracking applications, analyzing CV-job matches, and preparing for interviews.")

# Input fields
cv_file = st.file_uploader("📄 Upload Your CV (.pdf or .docx)", type=["pdf", "docx"])
job_desc = st.text_area("📝 Paste Job Description Here", height=200)
role = st.text_input("💼 Job Role")
company = st.text_input("🏢 Company")
expected_salary = st.number_input("💰 Expected Salary (KES)", step=1000)
application_date = st.date_input("📅 Date Applied", value=date.today())
status = st.selectbox("📌 Application Status", ["Applied", "Interview", "Offer Accepted", "Offer Rejected"])

# Analyze & Save Button
if st.button("🔍 Analyze & Save Job Application"):
    if not openai.api_key:
        st.error("❌ Missing OpenAI API Key. Please set it in your .env file.")
    elif cv_file and job_desc:
        with st.spinner("Analyzing your CV..."):
            cv_text = get_cv_text(cv_file)
            fit_summary = analyze_cv_fit(cv_text, job_desc)

            row = {
                "Role": role,
                "Company": company,
                "Date Applied": application_date,
                "Expected Salary": expected_salary,
                "Status": status,
                "Fit Summary": fit_summary
            }
            save_tracker(pd.DataFrame([row]))

            st.success("✅ Application saved and analyzed!")
            st.subheader("📊 Fit Summary:")
            st.write(fit_summary)

            if status == "Interview":
                st.subheader("🎤 AI-Generated Interview Questions")
                st.write(generate_interview_questions(job_desc, role))
    else:
        st.warning("⚠️ Please upload your CV and paste the job description.")

# Display Tracker
st.header("📂 My Job Applications")
df = load_tracker()
st.dataframe(df)

# Download CSV
if not df.empty:
    st.download_button("📥 Download Tracker as CSV", df.to_csv(index=False), "job_tracker.csv", "text/csv")
