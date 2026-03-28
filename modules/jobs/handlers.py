import re
import logging
from telegram import Update
from telegram.ext import ContextTypes, Application, CommandHandler, MessageHandler, filters

from core.db.database import save_application, get_all_applications
from modules.jobs.agent.enricher import enrich_job_url

logger = logging.getLogger(__name__)

URL_RE = re.compile(r"https?://\S+")
_last_job: dict[int, dict] = {}


async def _cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 *Tasq Agent — Jobs*\n\n"
        "I scan LinkedIn Israel daily and push matching backend/full-stack jobs here.\n\n"
        "*Commands:*\n"
        "• Paste any job URL → full Claude analysis\n"
        "• /track — log current job as applied\n"
        "• /pipeline — view tracked applications\n",
        parse_mode="Markdown",
    )


async def _cmd_track(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    job = _last_job.get(chat_id)
    if not job:
        await update.message.reply_text("No recent job to track. Paste a job URL first.")
        return
    save_application(
        url=job["url"],
        title=job.get("title", "Unknown"),
        company=job.get("company", "Unknown"),
        location=job.get("location", ""),
        fit_score=job.get("fit_score", 0),
    )
    await update.message.reply_text(
        f"✅ Logged *{job.get('title', 'Job')}* at *{job.get('company', '?')}* as applied.",
        parse_mode="Markdown",
    )


async def _cmd_pipeline(update: Update, context: ContextTypes.DEFAULT_TYPE):
    apps = get_all_applications()
    if not apps:
        await update.message.reply_text("No applications tracked yet.")
        return
    lines = ["📋 *Your Application Pipeline*\n"]
    for app in apps:
        emoji = {"applied": "📤", "interviewing": "🔄", "offer": "🎉", "rejected": "❌"}.get(app["status"], "📤")
        lines.append(
            f"{emoji} *{app['title']}* — {app['company']}\n"
            f"   📍 {app['location']}  |  Score: {app['fit_score']}/10  |  {app['status'].capitalize()}\n"
            f"   Applied: {app['applied_at'][:10]}\n"
        )
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


async def _handle_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text or ""
    match = URL_RE.search(text)
    if not match:
        return

    url = match.group(0)
    chat_id = update.effective_chat.id
    await update.message.reply_text("🔍 Analyzing job posting...")

    try:
        result = enrich_job_url(url)
    except RuntimeError as e:
        await update.message.reply_text(f"⚠️ {e}")
        return
    except Exception as e:
        logger.error(f"Enrichment failed for {url}: {e}")
        await update.message.reply_text(f"❌ Could not analyze that URL: {e}")
        return

    fit_score = 0
    score_match = re.search(r"Fit Score:\s*(\d+)/10", result)
    if score_match:
        fit_score = int(score_match.group(1))

    company_match = re.search(r"Company:\s*(.+)", result)
    role_match = re.search(r"Role:\s*(.+)", result)
    location_match = re.search(r"Location:\s*(.+)", result)

    _last_job[chat_id] = {
        "url": url,
        "title": role_match.group(1).strip() if role_match else "Unknown",
        "company": company_match.group(1).strip() if company_match else "Unknown",
        "location": location_match.group(1).strip() if location_match else "",
        "fit_score": fit_score,
    }

    await update.message.reply_text(result, parse_mode="Markdown")


def register_handlers(app: Application):
    """Register all jobs-module handlers onto the shared bot application."""
    app.add_handler(CommandHandler("start", _cmd_start))
    app.add_handler(CommandHandler("track", _cmd_track))
    app.add_handler(CommandHandler("pipeline", _cmd_pipeline))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex(r"https?://"), _handle_url))
