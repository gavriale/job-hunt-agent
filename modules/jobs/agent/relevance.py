from modules.jobs.scrapers.linkedin import Job
from core.config import CANDIDATE_PROFILE, MAX_DAILY_TOKENS
from core.db.database import get_tokens_used_today, increment_token_usage
import anthropic
import json

from core.config import ANTHROPIC_API_KEY

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

RELEVANCE_PROMPT = """You are a job relevance filter. Given a job listing and a candidate profile, decide if this job is worth sending to the candidate.

Respond with ONLY a JSON object in this exact format:
{{"score": <integer 1-10>, "reason": "<one sentence>", "send": <true or false>}}

Rules:
- score >= 6 means send = true
- Penalize: frontend-only, QA, DevOps-only, embedded, C++, ML research, Principal/Staff titles
- Reward: backend, Java, Python, .NET, full-stack roles in Israel/Tel Aviv

Candidate Profile:
{profile}

Job Title: {title}
Company: {company}
Location: {location}
"""


def score_job(job: Job) -> dict:
    if get_tokens_used_today() >= MAX_DAILY_TOKENS:
        raise RuntimeError(f"Daily token cap of {MAX_DAILY_TOKENS} reached.")

    prompt = RELEVANCE_PROMPT.format(
        profile=CANDIDATE_PROFILE,
        title=job.title,
        company=job.company,
        location=job.location,
    )

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=128,
        messages=[{"role": "user", "content": prompt}],
    )

    increment_token_usage(message.usage.input_tokens + message.usage.output_tokens)

    try:
        return json.loads(message.content[0].text.strip())
    except json.JSONDecodeError:
        return {"score": 0, "reason": "Could not parse response.", "send": False}
