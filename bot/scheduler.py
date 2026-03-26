import logging
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from telegram import Bot

from config import RSS_POLL_INTERVAL_HOURS, DAILY_TIP_HOUR, FOLLOW_UP_DAYS
from db.database import init_db, get_stale_applications
from sources.rss_feeds import fetch_new_jobs

logger = logging.getLogger(__name__)

# Keywords that suggest a relevant role
INCLUDE_KEYWORDS = [
    "backend", "back-end", "back end",
    "python", "software engineer", "software developer",
    "full stack", "fullstack", "full-stack",
    "ai engineer", "ml engineer", "machine learning",
    "platform engineer", "infrastructure engineer",
    "api", "node", "django", "fastapi", "flask",
]

# Keywords that disqualify a role immediately
EXCLUDE_KEYWORDS = [
    "frontend", "front-end", "front end",
    "qa ", "quality assurance", "test engineer",
    "devops", "sre ", "site reliability",
    "designer", "ux ", "ui ", "graphic",
    "marketing", "sales", "hr ", "recruiter",
    "finance", "accounting", "legal", "analyst",
    "data analyst", "business analyst",
]


def _is_relevant(title: str) -> bool:
    t = title.lower()
    if any(kw in t for kw in EXCLUDE_KEYWORDS):
        return False
    return any(kw in t for kw in INCLUDE_KEYWORDS)


def _format_job_alert(job) -> str:
    return (
        f"💼 *{job.title}*\n"
        f"🏢 {job.company}\n"
        f"📍 {job.location}\n"
        f"🔗 [View Job]({job.url})\n\n"
        f"_Paste the URL for a full Claude analysis._"
    )


async def poll_and_notify(bot: Bot, chat_id: int):
    """Scrape new jobs, apply keyword filter, push matches to Telegram."""
    logger.info("[Scheduler] Scraping Secret Tel Aviv Jobs...")
    try:
        jobs = fetch_new_jobs()
    except Exception as e:
        logger.error(f"[Scheduler] Scrape failed: {e}")
        return

    relevant = [j for j in jobs if _is_relevant(j.title)]
    logger.info(f"[Scheduler] {len(relevant)} relevant out of {len(jobs)} new jobs.")

    if not relevant:
        return

    await bot.send_message(
        chat_id=chat_id,
        text=f"🔎 *{len(relevant)} new job{'s' if len(relevant) > 1 else ''} found*",
        parse_mode="Markdown",
    )

    for job in relevant:
        await bot.send_message(
            chat_id=chat_id,
            text=_format_job_alert(job),
            parse_mode="Markdown",
        )


async def send_follow_up_reminders(bot: Bot, chat_id: int):
    """Nudge user about applications with no update in FOLLOW_UP_DAYS days."""
    stale = get_stale_applications(days=FOLLOW_UP_DAYS)
    for app in stale:
        msg = (
            f"⏰ *Follow-up reminder*\n\n"
            f"You applied to *{app['title']}* at *{app['company']}* "
            f"{FOLLOW_UP_DAYS} days ago with no update.\n\n"
            f"Consider sending a follow-up email!"
        )
        await bot.send_message(chat_id=chat_id, text=msg, parse_mode="Markdown")


def build_scheduler(bot: Bot, chat_id: int) -> AsyncIOScheduler:
    init_db()
    scheduler = AsyncIOScheduler(timezone="Asia/Jerusalem")

    # Scrape every 24h — fire immediately on startup
    scheduler.add_job(
        poll_and_notify,
        trigger=IntervalTrigger(hours=RSS_POLL_INTERVAL_HOURS),
        args=[bot, chat_id],
        id="job_poll",
        replace_existing=True,
        next_run_time=datetime.now(),
    )

    # Follow-up reminders daily at 9am Israel time
    scheduler.add_job(
        send_follow_up_reminders,
        trigger=CronTrigger(hour=DAILY_TIP_HOUR, minute=0, timezone="Asia/Jerusalem"),
        args=[bot, chat_id],
        id="follow_up_reminders",
        replace_existing=True,
    )

    return scheduler
