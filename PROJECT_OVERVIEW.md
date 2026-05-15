# 🏇 Horse Racing Betting Analyzer — Complete Project Deep Dive

## 1. THE PROMPT / ORIGINAL CONCEPT

The app was built to operationalize a **disciplined, statistically-driven horse racing betting strategy** — replacing gut-feel betting with a rule-based system. The core thesis:

> "Most punters lose because they bet too often, chase losses, and rely on tipsters. A small, criteria-filtered, bankroll-controlled approach turns horse racing from gambling into a high-probability decision system."

Key product asks from the user:
- Live racecards + analysis (no manual data entry)
- **8-criteria scoring algorithm** that decides if a race is even worth betting
- Strict **bankroll management with discipline rules** (stop-loss, 2-loss rule, % staking)
- **No login** — single user, frictionless
- **"Today's Best Bets"** — auto-scan every race and rank top picks
- **Results page** — track what you bet on and how it settled

---

## 2. THE BETTING STRATEGY (The "Why")

The strategy is a **filter-first, value-second approach** rooted in three pillars:

### A. Selectivity over volume
Most races every day are unbettable. The algorithm rejects ~80% of races/horses outright before any stake is sized. Default daily limit: **5 bets max**.

### B. Approved tracks only
The system only bets at tracks where data quality, going consistency, and field competitiveness are reliable — **UK (all-weather + turf)**, **Ireland**, and **major US dirt tracks**. Random low-tier tracks are auto-rejected (Criterion 1). The whitelist contains ~70 tracks (Wolverhampton, Kempton, Lingfield, Cheltenham, Aintree, Curragh, Churchill Downs, Saratoga, etc.)

### C. Discipline rules (hard-coded, cannot be overridden)
1. **Stop-loss**: default $60 floor on a $250 bankroll. If hit, betting stops.
2. **2-consecutive-loss rule**: 2 losses in a row → **mandatory stop for the day**.
3. **Max stake**: 3% of bankroll, scaled by score.
4. **Daily bet limit**: 5 bets/day.
5. **Cushion warnings**: <50% above stop-loss → "be selective"; <20% → "critical, reduce stakes".

---

## 3. THE 8-CRITERIA ALGORITHM (The Heart)

Every horse in every race is scored out of **8 points**. Two hard gates must be passed first.

### Hard gates (rejection before scoring)
- **Track must be in the approved whitelist** → else REJECTED
- **Horse must have ≥3 career runs** (no first-timers, no maidens with thin form) → else REJECTED

### The 8 criteria

| # | Criterion | Points | Logic |
|---|---|---|---|
| 1 | Track Type | gate | Must be approved track |
| 2 | Form Completeness | gate | ≥3 runs + official rating |
| 3 | Form & Consistency | 0–2 | +1 if win rate ≥20%, +1 if place rate ≥50% |
| 4 | Recent Trend | 0–2 | +1 if trend = "improving", +1 if last position 1–3 |
| 5 | Official Rating Value | 0–1 | OR ≥70 = pass, ≥90 = strong |
| 6 | Weight & Class | 0–1 | ≤150 lbs in handicap = pass (lighter advantage) |
| 7 | Fitness | 0–1 | 7–42 days since last run = fit window |
| 8 | Positive Angle | 0–1 | First-time headgear, improving + good rating, recent podium + upward trend, well-handicapped |

### Score → Recommendation Mapping

| Score | Confidence | Stars | Verdict |
|---|---|---|---|
| 7–8 | 90–95% | ★★★★★ | **EXCELLENT BET** — Strong recommend |
| 6 | 80–90% | ★★★★ | **STRONG BET** — Recommend |
| 5 | 70–80% | ★★★★ | **GOOD BET** — Acceptable |
| 4 | 60–70% | ★★★ | BORDERLINE — Proceed with caution |
| 3 | 50–60% | ★★ | WEAK — Not recommended |
| <3 | <50% | ★ | AVOID |

### Stake sizing (Kelly-ish, capped)

```
Score 7+  → 3.0% of bankroll
Score 6   → 2.5%
Score 5   → 2.0%
Score 4   → 1.5%
Score <4  → 1.0%
```
Rounded to nearest $0.50, hard min $2, hard max 3% of bankroll.

---

## 4. WHERE THE DATA COMES FROM

### Primary source: **The Racing API** (theracingapi.com)
- Plan: **Free tier**
- Auth: HTTP Basic (username + password in backend `.env`)
- Coverage: UK + Ireland racecards (live, today + tomorrow)
- Rate limit: ~30 req/min → handled by a **2-minute in-memory cache** in `racing_api.py`

### What the API provides (per horse, per race)
- Horse name, jockey, trainer, draw, weight
- Career form string (e.g., "82113-")
- Win rate, place rate, recent trend (computed locally from form)
- Official rating (OR), age, headgear
- Last position, days since last run
- Race meta: course, off-time, race name, class, distance, going, surface, race type (Flat/Chase/Hurdle/NH Flat)

### What's **NOT** available on the free tier
- Bookmaker odds (we fall back to "Estimated odds" derived from score: `max(2.0, 12 - score)` for WIN, `(12 - score)/3 + 1` for PLACE)
- Live race results (returns 401 → Results page gracefully shows local bet outcomes instead)
- Expert tipster consensus
- Betfair Exchange market data
- Timeform pace ratings / sectional times

### Failed integration attempt
- **The Odds API** (`the-odds-api.com`): does NOT support horse racing — only traditional sports. Returns `UNKNOWN_SPORT`. Key sits unused in `.env`.

---

## 5. WHAT THE APP DOES (Feature by Feature)

### Dashboard (`/`)
- Welcome banner with quick actions
- **Today's Best Bets widget** — auto-scans every UK/IRE race today, applies 8-criteria to every horse, sorts by score descending, shows top 5 picks
- **Bankroll widget** — current balance, today's P/L, stop-loss, cushion
- Quick tiles: Analyze Race · Results · Statistics
- Recent bets list

### Race Analysis (`/analyze`)
- Choose course → choose race → run 8-criteria analysis
- LIVE badge confirms real Racing API data
- Returns: **WIN**, **PLACE**, **BOX TRIFECTA** (top 3, $12 stake, 6 combos), **SAFETY PLACE**
- Each recommendation shows criteria breakdown, confidence %, star rating, suggested stake, potential return/profit
- **Warnings panel**: low cushion, consecutive losses, no qualifying bets

### Results (`/results`)
- **Pending Bets** — settle as WIN/LOSS
- **Settled Bets** — full history with P/L
- **Race Results** — live results (graceful empty state on free tier)

### Bet History (`/bets`)
- Full ledger, filter by status, settle bets

### Statistics (`/stats`)
- Overall ROI, win rate, total profit/loss
- **Performance by score bucket** (backtest your strategy)
- Recent form charts (Recharts)

### Settings (`/settings`)
- Edit bankroll, stop-loss, daily bet limit
- View discipline rules

---

## 6. THE BANKROLL ENGINE

### Default config
```
starting_bankroll  = $250
current_bankroll   = $250
stop_loss          = $60
max_daily_bets     = 5
max_stake_percent  = 3%
consecutive_losses = 0
```

### Lifecycle of a bet
1. **Place bet** (`POST /api/bets`) → stake deducted immediately
2. **Settle bet** (`POST /api/bets/{id}/settle`)
   - **WIN** → `current_bankroll += stake * odds`; `consecutive_losses = 0`
   - **LOSS** → `profit_loss = -stake`; `consecutive_losses += 1`
3. **2 consecutive losses** → backend flags `STOP_FOR_DAY` warning
4. **Cushion check** → warnings cascade as cushion shrinks toward stop-loss

### Hard validations
- Stake > 3% of bankroll → 400
- Double-settle → 400
- Non-existent bet → 404

---

## 7. ARCHITECTURE

### Backend — FastAPI + MongoDB
```
/app/backend/
├── server.py         # 998 lines — all endpoints, 8-criteria algo, bankroll
├── racing_api.py     # The Racing API client + 2-min cache + transforms
├── tests/            # pytest suite (20 tests, all passing)
├── requirements.txt  # fastapi, motor, httpx, pydantic, python-dotenv
└── .env              # MONGO_URL, DB_NAME, RACING_API_USERNAME, RACING_API_PASSWORD
```

**Endpoints (all prefixed `/api`):**
- `GET /racecards/today` — live racecards (cached)
- `POST /analyze` — 8-criteria on a race (race_id or track+race_number)
- `GET /best-bets` — auto-scan today, top picks across all races
- `GET /results` — settled + pending bets + live race results
- `GET/PUT /bankroll`, `POST /bankroll/reset`
- `GET/POST /bets`, `POST /bets/{bet_id}/settle`
- `GET /statistics`, `GET /tracks`, `GET /scraper/status`

**MongoDB collections:**
- `bankroll_settings` — `{user_id, current_bankroll, starting_bankroll, stop_loss, max_daily_bets, consecutive_losses}`
- `bets` — `{bet_id, user_id, track, race_number, horse_name, draw_number, bet_type, stake, odds, score, result, profit_loss, timestamp}`

### Frontend — React + Tailwind + Shadcn
```
/app/frontend/src/
├── pages/
│   ├── Dashboard.jsx
│   ├── RaceAnalysis.jsx
│   ├── BetHistory.jsx
│   ├── Results.jsx
│   ├── Statistics.jsx
│   └── Settings.jsx
├── components/
│   ├── dashboard/   # BankrollWidget, RecommendationCard, WarningBanner
│   ├── layout/      # DashboardLayout, Sidebar
│   └── ui/          # Shadcn primitives (~40 components)
├── App.js           # Router (no auth)
└── .env             # REACT_APP_BACKEND_URL
```

**Design:**
- Dark mode by default (financial/racing aesthetic)
- Green-accented (profit / live data signals)
- Fonts: Chivo (headings), Manrope (body), JetBrains Mono (data)
- Icons: lucide-react · Toasts: sonner

---

## 8. THE CACHING TRICK

The Racing API rate-limits to ~30 req/min. The solution: simple in-memory dict in `racing_api.py` with **120 sec TTL**. A single user can browse freely — 52 races scanned + 216 horses analyzed = 1 API call within the 2-min window.

---

## 9. KEY BUGS FIXED ALONG THE WAY

1. **Racing API auth failure** — was sending Bearer token, fixed to HTTP Basic.
2. **`NR` (non-runner) parsing crash** — integer fields contained "NR" strings; safe conversion added.
3. **429 rate limiting** — solved with 2-min cache.
4. **The Odds API** — discovered no horse racing support.
5. **`/api/analyze` KeyError** — rejected horses (insufficient form / unapproved track) returned a stripped dict missing `confidence_rating` / `star_rating` / `recommendation`. Downstream `build_recommendations()` crashed. Fixed by adding `REJECTED` defaults to both early-return paths.
6. **React hydration warning** — Badge nested inside `<p>` (invalid HTML). Fixed in RaceAnalysis.

---

## 10. ROADMAP

### P1
- Real odds source (RapidAPI horse racing odds, Betfair Exchange paid, or scraping)
- Trifecta/Parlay recommendations from 8-criteria scores
- Pace Map visualization (front-runner / stalker / closer)

### P2
- Premium data (Timeform pace ratings, Betfair market confidence)
- Push notifications for high-score qualifying bets
- Historical backtesting — does the 8-criteria actually print ROI > 0?

### P3
- Multi-user auth (Emergent Google login)
- Mobile-optimized UI
- Auto-bet execution via Betfair API

---

## 11. ONE-PARAGRAPH SUMMARY

A FastAPI + React app that pulls live UK/IRE racecards from The Racing API every 2 minutes, scores every horse against an 8-criteria filter (track quality, form completeness, win/place rates, recent trend, official rating, weight, fitness, positive angles), generates WIN / PLACE / Box Trifecta / Safety recommendations with confidence ratings and Kelly-style stake sizing, enforces hard bankroll discipline (stop-loss, 2-loss rule, 3% max stake, 5 bets/day), and tracks every bet end-to-end with auto-computed P/L. No login. Dark UI. 20/20 tests passing.
