# Tasq Agent — Project Context

## What this is
A modular autonomous agent platform delivered via Telegram bot.
Built by @gavriale — Backend Engineer based in Israel.

Each module is self-contained and handles a specific domain (jobs, cars, apartments, etc.).
The core layer wires everything together — one bot, one scheduler, one DB.

---

## Architecture

```
tasq-agent/
├── modules/
│   ├── jobs/
│   │   ├── scrapers/
│   │   │   └── linkedin.py       # Scrapes LinkedIn Israel job searches
│   │   ├── agent/
│   │   │   ├── enricher.py       # Claude analysis for pasted job URLs
│   │   │   └── relevance.py      # Claude scoring (unused in proactive flow)
│   │   ├── handlers.py           # Telegram handlers — exposes register_handlers(app)
│   │   └── scheduler.py          # Scheduled tasks — exposes register_jobs(scheduler, bot, chat_id)
│   ├── cars/                     # Placeholder — not yet implemented
│   │   ├── scrapers/
│   │   ├── agent/
│   │   ├── handlers.py
│   │   └── scheduler.py
│   └── apartments/               # Placeholder — not yet implemented
│       └── .gitkeep
├── core/
│   ├── db/
│   │   └── database.py           # Shared SQLite — seen items, applications, token usage
│   ├── bot/
│   │   └── main.py               # Single entry point — auto-registers all module handlers
│   ├── scheduler.py              # Master scheduler — imports each module's register_jobs()
│   └── config.py                 # Shared config, env vars, candidate profile
├── CLAUDE.md
├── requirements.txt
└── .env
```

---

## Architecture Rules
- Each module in `modules/` is fully self-contained
- Modules only import from `core/` — never from each other
- Adding a new module = create folder in `modules/`, implement `register_handlers(app)` and `register_jobs(scheduler, bot, chat_id)`, uncomment in `core/bot/main.py` and `core/scheduler.py`
- Deleting a module = delete its folder + comment out its lines in core — nothing else breaks

---

## Candidate Profile (Jobs Module)
- 4 years Backend Software Engineer
- Languages: Java, Python, C#, TypeScript
- Frameworks: Spring Boot, FastAPI, .NET Core, Angular
- Databases: PostgreSQL, MySQL, Redis
- Cloud: AWS (basic), Docker, Kafka (basic), Azure Service Bus
- Target: Mid/Senior Backend, Full Stack, Platform Engineer in Israel (Tel Aviv area)
- Exclude: Principal/Staff, Embedded, C++, DevOps-only, Frontend-only, QA, ML Research

---

## How the Jobs Module Works

### Proactive (every 24h)
1. Scrapes 5 LinkedIn Israel searches (backend, python, software engineer, full stack, java)
2. Deduplicates via `seen_jobs` table
3. Keyword filter (no Claude API) — pushes matching jobs to Telegram
4. Format: title, company, location, link

### Reactive (user pastes URL)
1. Fetches the job page
2. Claude Haiku analyzes against candidate profile
3. Returns structured summary: company, role, location, salary, fit score, recommendation

---

## Telegram Commands
| Command | What it does |
|---|---|
| (paste any job URL) | Full Claude analysis + fit score |
| `/start` | Welcome + instructions |
| `/track` | Log current job as applied |
| `/pipeline` | View all tracked applications |

---

## Running the Bot
```bash
python -m core.bot.main
```

---

## Environment Variables (.env)
```
TELEGRAM_BOT_TOKEN=
ANTHROPIC_API_KEY=
TELEGRAM_CHAT_ID=
MAX_DAILY_TOKENS=50000
```

---

## Git Flow
- Single branch: `main`
- Push directly to main

---

## Safety Rules
- Never commit `.env`
- All Claude API calls check + increment daily token counter against `MAX_DAILY_TOKENS`
- SQLite deduplication — never send the same item twice per module
