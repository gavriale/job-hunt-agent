import logging
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from telegram import Bot

from core.config import POLL_INTERVAL_HOURS, DAILY_TIP_HOUR, FOLLOW_UP_DAYS
from core.db.database import get_stale_applications
from modules.jobs.scrapers.linkedin import fetch_new_jobs

logger = logging.getLogger(__name__)

INCLUDE_KEYWORDS = [
    "backend", "back-end", "back end",
    "full stack", "fullstack", "full-stack",
    "software engineer", "software developer",
    "python", "java ", "java developer", "java engineer",
    "spring", "fastapi", ".net", "c# ",
    "platform engineer", "platform developer",
    "api developer", "api engineer",
    "server side", "server-side",
]

EXCLUDE_KEYWORDS = [
    "principal", "staff engineer", "distinguished", "vp ", "director",
    "embedded", "firmware", "kernel", "driver", "c++ ", "c/c++",
    "data scientist", "ml engineer", "machine learning engineer", "research engineer",
    "devops engineer", "sre ", "site reliability", "infrastructure engineer",
    "frontend", "front-end", "front end",
    "qa ", "quality assurance", "test engineer", "automation engineer",
    "designer", "ux ", "ui/ux",
    "marketing", "sales", "recruiter", "hr ", "talent",
    "finance", "accounting", "legal", "analyst",
    "manager", "team lead", "tech lead",
]


def _is_relevant(title: str) -> bool:
    t = title.lower()
    if any(kw in t for kw in EXCLUDE_KEYWORDS):
        return False
    return any(kw in t for kw in INCLUDE_KEYWORDS)


def _format_alert(job) -> str:
    return (
        f"💼 *{job.title}*\n"
        f"🏢 {job.company}\n"
        f"📍 {job.location}\n"
        f"🔗 [View Job]({job.url})\n\n"
        f"_Paste the URL for a full Claude analysis._"
    )


async def _poll_and_notify(bot: Bot, chat_id: int):
    logger.info("[Jobs] Scraping LinkedIn Israel...")
    try:
        jobs = fetch_new_jobs()
    except Exception as e:
        logger.error(f"[Jobs] Scrape failed: {e}")
        return

    relevant = [j for j in jobs if _is_relevant(j.title)]
    logger.info(f"[Jobs] {len(relevant)} relevant out of {len(jobs)} new jobs.")

    if not relevant:
        return

    await bot.send_message(
        chat_id=chat_id,
        text=f"🔎 *{len(relevant)} new job{'s' if len(relevant) > 1 else ''} found*",
        parse_mode="Markdown",
    )
    for job in relevant:
        await bot.send_message(chat_id=chat_id, text=_format_alert(job), parse_mode="Markdown")


async def _send_follow_up_reminders(bot: Bot, chat_id: int):
    for app in get_stale_applications(days=FOLLOW_UP_DAYS):
        await bot.send_message(
            chat_id=chat_id,
            text=(
                f"⏰ *Follow-up reminder*\n\n"
                f"You applied to *{app['title']}* at *{app['company']}* "
                f"{FOLLOW_UP_DAYS} days ago with no update.\n\n"
                f"Consider sending a follow-up email!"
            ),
            parse_mode="Markdown",
        )


def register_jobs(scheduler: AsyncIOScheduler, bot: Bot, chat_id: int):
    """Register all jobs-module scheduled tasks onto the shared scheduler."""
    scheduler.add_job(
        _poll_and_notify,
        trigger=IntervalTrigger(hours=POLL_INTERVAL_HOURS),
        args=[bot, chat_id],
        id="jobs_poll",
        replace_existing=True,
        next_run_time=datetime.now(),
    )
    scheduler.add_job(
        _send_follow_up_reminders,
        trigger=CronTrigger(hour=DAILY_TIP_HOUR, minute=0, timezone="Asia/Jerusalem"),
        args=[bot, chat_id],
        id="jobs_follow_up",
        replace_existing=True,
    )
