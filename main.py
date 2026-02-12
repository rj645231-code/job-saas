# ==============================
# 🚀 SMART MULTI USER JOB SAAS
# ==============================

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, date
from dotenv import load_dotenv
import os
from supabase import create_client

load_dotenv()

# ==============================
# 🔐 ENV VARIABLES
# ==============================
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ==============================
# SETTINGS
# ==============================
TARGET_SKILLS = ["python","sql","power bi","excel","tableau","machine learning"]
HISTORY_FILE = "seen_jobs.txt"

# ==============================
# CHROME SETUP
# ==============================
options = Options()
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--window-size=1920,1080")

driver = webdriver.Chrome(options=options)

# ==============================
# BUILD URL
# ==============================
def build_linkedin_url(keyword, location):
    return f"https://www.linkedin.com/jobs/search/?keywords={quote_plus(keyword)}&location={quote_plus(location)}"

# ==============================
# SCROLL
# ==============================
def scroll_page():
    last_height = driver.execute_script("return document.body.scrollHeight")
    for _ in range(50):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

# ==============================
# FETCH JOB DETAILS
# ==============================
def fetch_job_details(job_url):
    try:
        driver.get(job_url)
        time.sleep(2)
        soup = BeautifulSoup(driver.page_source,"html.parser")
        return soup.get_text(" ",strip=True).lower()
    except:
        return ""

# ==============================
# SEND EMAIL
# ==============================
def send_email(receiver, jobs):
    if not jobs:
        print("No jobs for", receiver)
        return False

    html = ""
    for job in jobs:
        html += f"""
        <div style="padding:10px;margin:10px;border-left:4px solid blue;">
        <b>{job['title']}</b><br>
        {job['company']} - {job['location']}<br>
        Skills: {job['skills']}<br>
        <a href="{job['link']}">Apply Now</a>
        </div>
        """

    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL
    msg['To'] = receiver
    msg['Subject'] = f"🔥 {len(jobs)} New Jobs Found"
    msg.attach(MIMEText(html,"html"))

    try:
        with smtplib.SMTP('smtp.gmail.com',587) as server:
            server.starttls()
            server.login(SENDER_EMAIL,EMAIL_PASSWORD)
            server.send_message(msg)
        print("✅ Email sent:",receiver)
        return True
    except Exception as e:
        print("Email error:",e)
        return False

# ==============================
# LOAD HISTORY
# ==============================
if os.path.exists(HISTORY_FILE):
    with open(HISTORY_FILE,"r") as f:
        seen_urls=set(line.strip() for line in f)
else:
    seen_urls=set()

# ==============================
# MAIN START
# ==============================
print("🚀 Smart Job SaaS Running...")

try:
    users = supabase.table("users").select("*").execute().data
except Exception as e:
    print("Database error:",e)
    driver.quit()
    exit()

today = date.today()

# ==============================
# LOOP USERS
# ==============================
for user in users:

    email = user["email"]
    keyword = user["keywords"]
    location = user["location"]
    last_sent = user.get("last_email_sent")

    # 🛑 skip if already emailed today
    if last_sent:
        try:
            last_sent_date = date.fromisoformat(last_sent)
            if last_sent_date == today:
                print(f"⛔ Already emailed today: {email}")
                continue
        except:
            pass

    print(f"\n👤 User: {email}")
    print(f"🔍 Searching: {keyword} | {location}")

    user_jobs = []

    try:
        url = build_linkedin_url(keyword,location)
        driver.get(url)
        time.sleep(5)
        scroll_page()

        soup = BeautifulSoup(driver.page_source,"html.parser")
        cards = soup.find_all("div",class_="base-card")

        for card in cards[:25]:

            a_tag = card.find("a",class_="base-card__full-link")
            if not a_tag: continue

            job_url = a_tag["href"].split("?")[0]
            if job_url in seen_urls:
                continue

            title = a_tag.text.strip()
            company = card.find("h4")
            company = company.text.strip() if company else ""
            loc = card.find("span",class_="job-search-card__location")
            loc = loc.text.strip() if loc else ""

            print("Checking:",title)

            desc = fetch_job_details(job_url)
            matched = [s for s in TARGET_SKILLS if s in desc]

            if matched:
                seen_urls.add(job_url)
                with open(HISTORY_FILE,"a") as f:
                    f.write(job_url+"\n")

                user_jobs.append({
                    "title":title,
                    "company":company,
                    "location":loc,
                    "link":job_url,
                    "skills":",".join(matched)
                })

    except Exception as e:
        print("Scraping error:",e)

    # ==========================
    # SEND EMAIL + UPDATE DATE
    # ==========================
    sent = send_email(email,user_jobs)

    if sent:
        supabase.table("users").update({
            "last_email_sent": str(today)
        }).eq("email", email).execute()

    time.sleep(10)

driver.quit()
print("\n✅ ALL USERS COMPLETED")
