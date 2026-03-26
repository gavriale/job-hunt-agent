import anthropic

from config import ANTHROPIC_API_KEY, CANDIDATE_PROFILE, MAX_DAILY_TOKENS
from db.database import get_tokens_used_today, increment_token_usage
from sources.rss_feeds import Job


client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

RELEVANCE_PROMPT = """You are a job relevance filter. Given a job listing and a candidate profile, decide if this job is worth sending to the candidate.

Respond with ONLY a JSON object in this exact format:
{{"score": <integer 1-10>, "reason": "<one sentence>", "send": <true or false>}}

Rules:
- score >= 6 means send = true
- Penalize: frontend-only, QA, DevOps-only, no-tech roles
- Reward: backend, Python, AI/ML, platform, full-stack roles in Israel/Tel Aviv
- If location is clearly outside Israel with no remote option, send = false

Candidate Profile:
{profile}

Job Title: {title}
Company: {company}
Location: {location}
Description snippet:
{summary}
"""


def score_job(job: Job) -> dict:
    """
    Score a job for relevance against the candidate profile.
    Returns dict: {score, reason, send}
    Raises RuntimeError if daily token cap exceeded.
    """
    tokens_used = get_tokens_used_today()
    if tokens_used >= MAX_DAILY_TOKENS:
        raise RuntimeError(
            f"Daily token cap of {MAX_DAILY_TOKENS} reached. No more Claude calls today."
        )

    prompt = RELEVANCE_PROMPT.format(
        profile=CANDIDATE_PROFILE,
        title=job.title,
        company=job.company,
        location=job.location,
        summary=job.summary[:2000],
    )

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=128,
        messages=[{"role": "user", "content": prompt}],
    )

    tokens = message.usage.input_tokens + message.usage.output_tokens
    increment_token_usage(tokens)

    import json
    raw = message.content[0].text.strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # Fallback: if Claude didn't return clean JSON, default to not sending
        return {"score": 0, "reason": "Could not parse response.", "send": False}


def format_job_alert(job: Job, score_result: dict) -> str:
    """Format a new job alert message for Telegram."""
    score = score_result.get("score", "?")
    reason = score_result.get("reason", "")
    return (
        f"🆕 *New Job Match*\n\n"
        f"💼 *{job.title}*\n"
        f"🏢 {job.company}\n"
        f"📍 {job.location}\n\n"
        f"✅ Fit Score: {score}/10\n"
        f"_{reason}_\n\n"
        f"🔗 [View Job]({job.url})\n\n"
        f"Paste the URL to get a full analysis."
    )


if __name__ == "__main__":
    from db.database import init_db
    from sources.rss_feeds import Job

    init_db()
    # Smoke test with a fake job
    test_job = Job(
        url="https://example.com/job/123",
        title="Backend Engineer",
        company="Acme Corp",
        location="Tel Aviv, Israel",
        summary="We are looking for a Python backend engineer to build APIs and data pipelines. AI/ML experience is a plus.",
    )
    result = score_job(test_job)
    print("Score result:", result)
    print()
    print(format_job_alert(test_job, result))
