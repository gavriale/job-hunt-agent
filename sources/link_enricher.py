import requests
from bs4 import BeautifulSoup

import anthropic

from config import ANTHROPIC_API_KEY, CANDIDATE_PROFILE, MAX_DAILY_TOKENS
from db.database import get_tokens_used_today, increment_token_usage


client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

ENRICH_PROMPT = """You are a job fit analyzer. Given the job posting content and candidate profile below, return ONLY the following structured message — no extra text, no markdown code blocks:

🏢 Company: <name>
💼 Role: <title>
📍 Location: <location + remote/hybrid/onsite>
💰 Salary: <if listed, else "Not listed">

✅ Fit Score: X/10
Why: <2-3 sentence reasoning against candidate profile>

⚠️ Watch out: <any red flags, overqualification, missing skills>

🎯 Recommended: Apply / Skip / Maybe

---
Candidate Profile:
{profile}

---
Job Posting:
{job_content}
"""


def _fetch_page_text(url: str) -> str:
    """Fetch a job URL and return cleaned text content."""
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
    except requests.RequestException as e:
        raise RuntimeError(f"Failed to fetch URL: {e}")

    soup = BeautifulSoup(response.text, "html.parser")

    # Remove noise
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()

    text = soup.get_text(separator="\n", strip=True)
    # Truncate to avoid blowing token budget
    return text[:8000]


def enrich_job_url(url: str) -> str:
    """
    Fetch a job URL, send content to Claude, return a formatted Telegram message.
    Raises RuntimeError if daily token cap is exceeded.
    """
    tokens_used = get_tokens_used_today()
    if tokens_used >= MAX_DAILY_TOKENS:
        raise RuntimeError(
            f"Daily token cap of {MAX_DAILY_TOKENS} reached. No more Claude calls today."
        )

    job_content = _fetch_page_text(url)

    prompt = ENRICH_PROMPT.format(profile=CANDIDATE_PROFILE, job_content=job_content)

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=512,
        messages=[{"role": "user", "content": prompt}],
    )

    tokens = message.usage.input_tokens + message.usage.output_tokens
    increment_token_usage(tokens)

    return message.content[0].text.strip()


if __name__ == "__main__":
    import sys
    from db.database import init_db
    init_db()
    url = sys.argv[1] if len(sys.argv) > 1 else None
    if not url:
        print("Usage: python -m sources.link_enricher <job_url>")
        sys.exit(1)
    print(enrich_job_url(url))
