# Job Hunt Agent — Project Context

## What this is
An autonomous job hunting agent delivered via Telegram bot.
Built by @gavriale — Backend Engineer who just relocated to Israel.

The bot does two things:
1. **Proactively** polls Indeed RSS + Secret Tel Aviv Jobs every 3 hours, scores relevance via Claude, and pushes only matching jobs to Telegram
2. **Reactively** — user pastes any job URL into Telegram, bot fetches the page, Claude extracts and scores it, returns a decision-ready summary

---

## Candidate Profile
- 4 years Backend Software Engineer
- Strong interest in AI/ML engineering roles
- BSc Computer Science, Open University Israel
- Recently relocated to Israel, looking for jobs in Tel Aviv area
- Open to: Backend Engineer, Full Stack, AI Engineer, Platform Engineer
- Not interested in: Frontend-only, QA, DevOps-only roles

---

## Job Sources

| Source | Method |
|---|---|
| Secret Tel Aviv Jobs | RSS feed polled every 3 hours (`https://jobs.secrettelaviv.com/feed/`) |
| RemoteOK | RSS feeds polled every 3 hours (backend, python, AI categories) |
| Any job URL | User pastes link into Telegram → bot fetches → Claude enriches |

### Notes on sources
- **LinkedIn RSS** — killed by LinkedIn, no longer works
- **Indeed RSS** — blocked (403/404), no longer accessible
- **Secret Tel Aviv** — live WordPress RSS, updated hourly, English-speaking Israel market
- **RemoteOK** — live RSS, remote roles worldwide; Claude's relevance scorer filters for fit

---

## What "Enrich" means
When user pastes a job URL, the bot:
1. Fetches the page content
2. Sends it to Claude with the candidate profile
3. Claude returns a structured Telegram message:

```
🏢 Company: <name>
💼 Role: <title>
📍 Location: <location + remote/hybrid/onsite>
💰 Salary: <if listed, else "Not listed">

✅ Fit Score: X/10
Why: <2-3 sentence reasoning against candidate profile>

⚠️  Watch out: <any red flags, overqualification, missing skills>

🎯 Recommended: Apply / Skip / Maybe

Reply /track to log this application
Reply /prep <company> to generate interview prep
```

---

## Architecture

```
job-hunt-agent/
├── bot/
│   ├── main.py              # Telegram bot entry point + command registration
│   ├── handlers.py          # /start, /pipeline, /prep, /quiz, URL paste handler
│   └── scheduler.py         # APScheduler — polls RSS every 3 hours
├── sources/
│   ├── rss_feeds.py         # Fetches + parses Indeed + Secret Tel Aviv RSS feeds
│   └── link_enricher.py     # Fetches job URL, sends to Claude, returns summary
├── agent/
│   ├── relevance.py         # Claude scores job fit against candidate profile
│   └── prep.py              # Claude generates interview prep plan + quiz questions
├── db/
│   └── database.py          # SQLite — seen jobs (dedup) + application tracking
├── config.py                # Loads .env, defines CANDIDATE_PROFILE + constants
├── requirements.txt
├── .env.example
├── CLAUDE.md                # This file — always read before doing anything
└── README.md
```

---

## Tech Stack
- `python-telegram-bot==20.7` — Telegram bot framework
- `requests` — HTTP fetching for RSS + job URLs
- `beautifulsoup4` — HTML parsing for job page content
- `feedparser` — RSS feed parsing
- `APScheduler==3.10.4` — scheduled RSS polling
- `anthropic` — Claude API for relevance scoring + enrichment + prep
- `SQLite` — built into Python, no install needed
- `python-dotenv` — .env loading

---

## Telegram Bot Commands
| Command | What it does |
|---|---|
| (paste any URL) | Enriches the job URL and scores fit |
| `/start` | Welcome message + instructions |
| `/track` | Log current job as applied |
| `/pipeline` | Show all tracked applications with status |
| `/prep <company>` | Generate full interview prep plan for a company |
| `/quiz` | Claude quizzes you — DS&A + system design questions |

---

## Git Flow
- `main` — stable, working code only
- `dev` — integration branch, all features merge here first
- `feature/phase1-scanner` — current branch
- `feature/phase2-tracker`
- `feature/phase3-interview-prep`

**Always commit to feature branch → PR to dev → merge to main when stable.**

---

## Environment Variables (.env)
```
TELEGRAM_BOT_TOKEN=
ANTHROPIC_API_KEY=
MAX_DAILY_TOKENS=50000
```

---

## Safety Rules
- Never commit `.env` — it's in `.gitignore`
- All Claude API calls must check + increment a daily token counter against `MAX_DAILY_TOKENS`
- If daily token cap is hit, stop making Claude API calls and notify user via Telegram
- SQLite deduplication — never send the same job URL twice

---

## Build Order

### Phase 1 — Core scanner (START HERE)
Build in this exact order, one file at a time:
1. `requirements.txt`
2. `config.py`
3. `db/database.py`
4. `sources/rss_linkedin.py`
5. `sources/link_enricher.py`
6. `agent/relevance.py`
7. `bot/scheduler.py`
8. `bot/handlers.py`
9. `bot/main.py`

After each file: run it if possible, fix any errors, then move to the next.

### Phase 2 — Application tracker
- `/track` saves job to SQLite with status "applied"
- `/pipeline` renders a clean list grouped by status
- Auto reminder after 7 days of no response: "Follow up on X at Y?"

### Phase 3 — Interview prep
- `/prep <company>` — Claude generates: company research, likely questions, suggested answers, things to read
- Daily tip pushed at 9am Israel time (Asia/Jerusalem timezone)
- `/quiz` — Claude generates 3 questions (1 DS&A, 1 system design, 1 behavioral), user answers, Claude gives feedback