# ==============================
# 🚀 SMART MULTI USER JOB SAAS
# ==============================

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
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

# ==============================
# CONNECT SUPABASE
# ==============================
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ==============================
# SETTINGS
# ==============================
TARGET_SKILLS = ["python","sql","power bi","excel","tableau","machine learning"]
HISTORY_FILE = "seen_jobs.txt"

MAX_SCROLL_ATTEMPTS = 80
SCROLL_PAUSE = 4
DETAIL_PAUSE = 2

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
# BUILD LINKEDIN URL
# ==============================
def build_linkedin_url(keyword, location):
    return f"https://www.linkedin.com/jobs/search/?keywords={quote_plus(keyword)}&location={quote_plus(location)}"

# ==============================
# SCROLL PAGE
# ==============================
def scroll_page():
    last_height = driver.execute_script("return document.body.scrollHeight")

    for _ in range(MAX_SCROLL_ATTEMPTS):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(SCROLL_PAUSE)

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
        time.sleep(DETAIL_PAUSE)

        soup = BeautifulSoup(driver.page_source,"html.parser")
        desc = soup.get_text(" ",strip=True).lower()
        return desc
    except:
        return ""

# ==============================
# SEND EMAIL
# ==============================
def send_email(receiver, jobs):
    if not jobs:
        print("No jobs for", receiver)
        return

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
    except Exception as e:
        print("Email error:",e)

# ==============================
# LOAD HISTORY
# ==============================
if os.path.exists(HISTORY_FILE):
    with open(HISTORY_FILE,"r") as f:
        seen_urls=set(line.strip() for line in f)
else:
    seen_urls=set()

# ==============================
# 🚀 MAIN SYSTEM START
# ==============================
print("🚀 Smart Job SaaS Running...")

try:
    users = supabase.table("users").select("*").execute().data
except Exception as e:
    print("Database error:",e)
    driver.quit()
    exit()

# ==============================
# LOOP EACH USER
# ==============================
for user in users:

    email = user["email"]
    keyword = user["keywords"]
    location = user["location"]

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

    # send email per user
    send_email(email,user_jobs)
    time.sleep(10)

driver.quit()
print("\n✅ ALL USERS COMPLETED")
