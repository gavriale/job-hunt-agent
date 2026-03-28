import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
MAX_DAILY_TOKENS = int(os.getenv("MAX_DAILY_TOKENS", 50000))

CANDIDATE_PROFILE = """
Name: Gavri Ale
Experience: 4 years — Backend Software Engineer
Education: BSc Computer Science, Open University Israel
Location: Israel (Tel Aviv area preferred)

Languages: Java, Python, C#, TypeScript
Frameworks: Spring Boot, FastAPI, .NET Core, Angular
Databases: PostgreSQL, MySQL, Redis
Cloud & DevOps: AWS (basic), Docker, Apache Kafka (basic), Azure Service Bus
Patterns: Microservices, REST APIs, ETL pipelines, Design Patterns (Strategy, Saga)

Target roles: Backend Engineer, Full Stack Engineer, Platform Engineer, Backend-focused automation
Target level: Mid-level or Senior (NOT Principal, Staff, Distinguished, or Lead)
Target industries: Product companies, Fintech, SaaS, Enterprise software

Exclude: C/C++, embedded systems, Linux kernel, drivers, heavy DevOps/infrastructure,
         Data Science, ML research, Principal/Staff/Distinguished titles, frontend-only, QA
"""

POLL_INTERVAL_HOURS = 24
DAILY_TIP_HOUR = 9  # 9am Israel time (Asia/Jerusalem)
FOLLOW_UP_DAYS = 7
