import streamlit as st
from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="Smart Job Alert System", page_icon="🚀")
st.title("🚀 Smart Automated Job Alert System")

st.write("Get daily job alerts directly to your email")

with st.form("signup_form"):
    email = st.text_input("Enter your Email")
    keywords = st.text_input("Job Keywords (Example: Data Analyst, Python)")
    location = st.text_input("Location (Example: India, Remote)")
    
    submit = st.form_submit_button("Subscribe")

if submit:
    if email and keywords and location:
        try:
            data = {
                "email": email,
                "keywords": keywords,
                "location": location
            }
            supabase.table("users").insert(data).execute()
            st.success("✅ Successfully subscribed! You will receive daily job alerts.")
        except Exception as e:
            st.error(f"Database error: {e}")
    else:
        st.warning("⚠️ Please fill all fields")

st.markdown("---")
st.write("Made with ❤️ by Rishabh")
