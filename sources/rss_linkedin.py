import feedparser
import requests
from dataclasses import dataclass
from typing import List

from config import LINKEDIN_RSS_FEEDS
from db.database import is_job_seen, mark_job_seen


@dataclass
class Job:
    url: str
    title: str
    company: str
    location: str
    summary: str


def _parse_feed(feed_url: str) -> List[Job]:
    """Fetch and parse a single LinkedIn RSS feed URL."""
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }
    try:
        response = requests.get(feed_url, headers=headers, timeout=15)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"[RSS] Failed to fetch feed {feed_url}: {e}")
        return []

    feed = feedparser.parse(response.content)
    jobs = []

    for entry in feed.entries:
        url = entry.get("link", "").strip()
        title = entry.get("title", "").strip()
        summary = entry.get("summary", "").strip()

        company = ""
        location = ""
        if " at " in title:
            parts = title.split(" at ", 1)
            title = parts[0].strip()
            company = parts[1].strip()
        if hasattr(entry, "location"):
            location = entry.location

        if url:
            jobs.append(Job(url=url, title=title, company=company, location=location, summary=summary))

    return jobs


def fetch_new_jobs() -> List[Job]:
    """
    Poll all configured LinkedIn RSS feeds.
    Returns only jobs not yet seen (deduped via DB).
    Marks new jobs as seen before returning.
    """
    new_jobs = []

    for feed_url in LINKEDIN_RSS_FEEDS:
        jobs = _parse_feed(feed_url)
        for job in jobs:
            if not is_job_seen(job.url):
                mark_job_seen(job.url, title=job.title, company=job.company)
                new_jobs.append(job)

    print(f"[RSS] Found {len(new_jobs)} new jobs across {len(LINKEDIN_RSS_FEEDS)} feeds.")
    return new_jobs


if __name__ == "__main__":
    from db.database import init_db
    init_db()
    jobs = fetch_new_jobs()
    for job in jobs:
        print(f"  - {job.title} @ {job.company} | {job.url[:60]}")
