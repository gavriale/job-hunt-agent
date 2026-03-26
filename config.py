import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
MAX_DAILY_TOKENS = int(os.getenv("MAX_DAILY_TOKENS", 50000))

CANDIDATE_PROFILE = """
Name: Gavri Ale
Role: Backend Software Engineer (4 years experience)
Education: BSc Computer Science, Open University Israel
Location: Israel (Tel Aviv area preferred)
Open to: Backend Engineer, Full Stack, AI Engineer, Platform Engineer
Not interested in: Frontend-only, QA, DevOps-only roles

Skills: Python, backend systems, APIs, databases
Strong interest in: AI/ML engineering roles
"""

RSS_FEEDS = [
    # Secret Tel Aviv Jobs — Israel-focused, English-speaking market
    "https://jobs.secrettelaviv.com/feed/",
    # RemoteOK — remote roles (backend, Python, AI); Claude filters for relevance
    "https://remoteok.com/remote-backend-jobs.rss",
    "https://remoteok.com/remote-python-jobs.rss",
    "https://remoteok.com/remote-ai-jobs.rss",
]

RSS_POLL_INTERVAL_HOURS = 3
DAILY_TIP_HOUR = 9  # 9am Israel time (Asia/Jerusalem)
FOLLOW_UP_DAYS = 7
