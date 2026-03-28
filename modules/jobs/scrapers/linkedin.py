import requests
from bs4 import BeautifulSoup
from dataclasses import dataclass
from typing import List

from core.db.database import is_job_seen, mark_job_seen

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

LINKEDIN_SEARCHES = [
    "https://www.linkedin.com/jobs/search/?keywords=backend+engineer&location=Israel&f_TPR=r86400&sortBy=DD",
    "https://www.linkedin.com/jobs/search/?keywords=python+developer&location=Israel&f_TPR=r86400&sortBy=DD",
    "https://www.linkedin.com/jobs/search/?keywords=software+engineer&location=Tel+Aviv&f_TPR=r86400&sortBy=DD",
    "https://www.linkedin.com/jobs/search/?keywords=full+stack+developer&location=Israel&f_TPR=r86400&sortBy=DD",
    "https://www.linkedin.com/jobs/search/?keywords=java+developer&location=Israel&f_TPR=r86400&sortBy=DD",
]


@dataclass
class Job:
    url: str
    title: str
    company: str
    location: str
    summary: str


def _scrape_search(search_url: str) -> List[Job]:
    try:
        response = requests.get(search_url, headers=HEADERS, timeout=15)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"[LinkedIn] Failed to fetch {search_url}: {e}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    jobs = []

    for card in soup.select("div.base-card"):
        link = card.select_one("a.base-card__full-link")
        if not link:
            continue
        url = link.get("href", "").split("?")[0].strip()

        title_tag = card.select_one("h3.base-search-card__title")
        title = title_tag.get_text(strip=True) if title_tag else ""

        company_tag = card.select_one("h4.base-search-card__subtitle")
        company = company_tag.get_text(strip=True) if company_tag else ""

        location_tag = card.select_one("span.job-search-card__location")
        location = location_tag.get_text(strip=True) if location_tag else ""

        if url and title:
            jobs.append(Job(url=url, title=title, company=company, location=location, summary=""))

    return jobs


def fetch_new_jobs() -> List[Job]:
    """Scrape LinkedIn Israel searches, return only unseen jobs."""
    new_jobs = []
    seen_urls: set = set()

    for search_url in LINKEDIN_SEARCHES:
        for job in _scrape_search(search_url):
            if job.url in seen_urls:
                continue
            seen_urls.add(job.url)
            if not is_job_seen(job.url):
                mark_job_seen(job.url, title=job.title, company=job.company)
                new_jobs.append(job)

    print(f"[LinkedIn] Found {len(new_jobs)} new jobs.")
    return new_jobs
