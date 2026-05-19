import os
import requests
import schedule
import time
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv(".env.example")

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)

KEYWORDS = [
    "CRA", "CTA", "Clinical Trial Assistant",
    "Clinical Research", "Study Coordinator",
    "Clinical Operations", "In-house CRA",
    "Clinical Research Associate",
    "Clinical Trial Associate",
    "Site Management Associate",
    "Regulatory Affairs Assistant",
    "Pharmacovigilance"
]

URLS = [
    "https://www.infojobs.net/jobsearch/search-results/list.xhtml?keyword=clinical",
    "https://www.indeed.com/jobs?q=clinical+research",
]

seen_jobs = set()

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    
    payload = {
        "chat_id": CHAT_ID,
        "text": message
    }

    requests.post(url, data=payload)

def analyze_job(title, snippet):
    prompt = f"""
    Analiza esta oferta para un perfil junior con máster en monitorización y gestión de ensayos clínicos y experiencia en CRO.

    Oferta:
    Título: {title}
    Descripción: {snippet}

    Devuelve:
    - Encaje del 0 al 100
    - Motivo
    - Si parece junior o no
    """

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    return response.choices[0].message.content

def search_jobs():
    for url in URLS:
        try:
            response = requests.get(url)
            soup = BeautifulSoup(response.text, "lxml")

            jobs = soup.find_all("a")

            for job in jobs[:20]:
                title = job.get_text(strip=True)

                if any(keyword.lower() in title.lower() for keyword in KEYWORDS):

                    link = job.get("href")

                    if not link:
                        continue

                    if link in seen_jobs:
                        continue

                    seen_jobs.add(link)

                    analysis = analyze_job(title, title)

                    message = f"""
🚨 Nueva oferta clínica

📌 {title}

🔗 {link}

🤖 IA:
{analysis}
"""

                    send_telegram(message)

        except Exception as e:
            print(e)

schedule.every(1).hours.do(search_jobs)

print("Bot funcionando...")

search_jobs()

while True:
    schedule.run_pending()
    time.sleep(60)