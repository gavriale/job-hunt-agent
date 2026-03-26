import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from telegram import Bot

from config import RSS_POLL_INTERVAL_HOURS, DAILY_TIP_HOUR, FOLLOW_UP_DAYS
from db.database import init_db, get_stale_applications
from sources.rss_linkedin import fetch_new_jobs
from agent.relevance import score_job, format_job_alert

logger = logging.getLogger(__name__)


async def poll_rss_and_notify(bot: Bot, chat_id: int):
    """Fetch new jobs from RSS, score each, push matches to Telegram."""
    logger.info("[Scheduler] Polling RSS feeds...")
    try:
        jobs = fetch_new_jobs()
    except Exception as e:
        logger.error(f"[Scheduler] RSS fetch failed: {e}")
        return

    sent = 0
    for job in jobs:
        try:
            result = score_job(job)
        except RuntimeError as e:
            # Daily token cap hit
            await bot.send_message(chat_id=chat_id, text=f"⚠️ {e}")
            return
        except Exception as e:
            logger.error(f"[Scheduler] Scoring failed for {job.url}: {e}")
            continue

        if result.get("send"):
            msg = format_job_alert(job, result)
            await bot.send_message(chat_id=chat_id, text=msg, parse_mode="Markdown")
            sent += 1

    logger.info(f"[Scheduler] Sent {sent} job alerts out of {len(jobs)} new jobs.")


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
    """
    Create and configure the APScheduler instance.
    Call scheduler.start() after the bot application is running.
    """
    init_db()
    scheduler = AsyncIOScheduler(timezone="Asia/Jerusalem")

    # Poll RSS every N hours
    scheduler.add_job(
        poll_rss_and_notify,
        trigger=IntervalTrigger(hours=RSS_POLL_INTERVAL_HOURS),
        args=[bot, chat_id],
        id="rss_poll",
        replace_existing=True,
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
