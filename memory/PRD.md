# Horse Racing Betting Analyzer - PRD

## Original Problem Statement
Build a comprehensive, professional-grade horse racing betting analysis web application that implements a proven statistical betting strategy. The system applies an 8-criteria scoring algorithm and provides actionable betting recommendations with confidence ratings and bankroll management.

## User Choices
- Dark mode default
- No login required (removed per user request)
- Full MVP with all features
- Default bankroll $250, Stop-loss $60
- Live data via The Racing API (theracingapi.com)

## Architecture

### Backend (FastAPI + MongoDB)
- `/api/racecards/today` - Live racecards from The Racing API (cached 2min)
- `/api/analyze` - 8-criteria race analysis (live by race_id or mock fallback)
- `/api/bankroll` - Get/Update bankroll settings
- `/api/bets` - Bet CRUD operations
- `/api/bets/{id}/settle` - Settle bet as WIN/LOSS
- `/api/statistics` - Performance statistics
- `/api/tracks` - List approved UK/US tracks
- `/api/scraper/status` - Data source configuration status

### Frontend (React + Tailwind + Shadcn UI)
- Dashboard - Bankroll widget, quick stats, recent bets
- Race Analysis - LIVE course/race selection, 8-criteria scoring, recommendations
- Bet History - Track/settle bets, filter by status
- Statistics - ROI/win rate charts, performance by score
- Settings - Bankroll config, discipline rules display

## Core Requirements
1. 8-Criteria Scoring Algorithm (adapted for live API data)
   - Track Type (approved UK/US/IRE tracks)
   - Form Completeness (minimum 3 runs + official rating)
   - Form & Consistency (win rate + place rate analysis)
   - Recent Trend (improving/declining + last position)
   - Official Rating Value (competitive rating threshold)
   - Weight & Class (lighter weight advantage in handicaps)
   - Fitness (days since last run, 7-42 days optimal)
   - Positive Angle (headgear, improving form + rating, etc.)

2. Betting Recommendations: WIN, PLACE, Box Trifecta, Safety bet
3. Bankroll Management: Stop-loss, 2-loss rule, 3% max stake, daily limit

## What's Been Implemented (Feb 10, 2026)
- Full backend API with live Racing API integration
- 2-minute response caching to handle API rate limits (429)
- 8-criteria scoring working with real horse data
- Live racecards showing 5 UK/IRE courses with real races
- One-click race analysis with full criteria breakdown
- Bankroll management persisted to MongoDB
- Bet placement with bankroll deduction
- Bet settlement (WIN/LOSS) with profit tracking
- Statistics with score-level breakdown
- Dark theme UI with LIVE data indicators

## What's Been Implemented (Feb 11, 2026)
- `/api/best-bets` endpoint — auto-scans today's live racecards, applies 8-criteria, returns top picks
- Dashboard "Today's Best Bets" widget with LIVE badge, 5 picks, stake & profit projections
- `/api/results` endpoint — returns settled/pending bets + live race results (graceful 401 handling for free tier)
- `/results` page with Pending bets, Settled bets, and Race Results tabs
- Sidebar nav updated with Results link
- Bugfix: `/api/analyze` no longer throws KeyError when a horse is REJECTED (insufficient form / unapproved track) — rejection dicts now include confidence_rating, star_rating, recommendation fields
- Bugfix: React hydration warning fixed in RaceAnalysis (Badge no longer nested inside `<p>`)
- Testing: backend 20/20 pass, frontend 100% flows working (iteration_4.json)

## Tech Stack
- Backend: Python FastAPI, Motor (MongoDB async), httpx
- Frontend: React, Tailwind CSS, Shadcn UI, Recharts
- Database: MongoDB
- External API: The Racing API (theracingapi.com)
- Fonts: Chivo (headings), Manrope (body), JetBrains Mono (data)

## Prioritized Backlog

### P0 (Done)
- [x] 8-criteria scoring algorithm
- [x] Bankroll management with MongoDB persistence
- [x] Race analysis UI with live data
- [x] Bet tracking and settlement
- [x] The Racing API integration (live racecards)
- [x] API rate limit handling with caching
- [x] Today's Best Bets auto-scanner (endpoint + Dashboard widget)
- [x] Results page (settled bets + live race results with graceful 401 fallback)

### P1 (Next)
- [ ] Alternative odds integration — The Odds API does NOT support horse racing; explore RapidAPI, Betfair Exchange, or stick with Estimated
- [ ] Advanced bet types (Trifecta / Parlay recommendations using 8-criteria scores)
- [ ] Real-time bookmaker odds integration (requires paid API plan)
- [ ] Expert consensus data (Racing Post, At The Races, Timeform)
- [ ] Market confidence data (Betfair Exchange)
- [ ] Push notifications for qualifying bets

### P2 (Future)
- [ ] User authentication (if needed)
- [ ] Historical data analysis and backtesting
- [ ] Auto-bet execution
- [ ] Mobile app
- [ ] Additional data sources integration

## Known Limitations
- Odds shown as "Estimated" (free API plan doesn't provide bookmaker odds)
- Expert consensus, Timeform, and Betfair criteria not yet available
- Rate limit: ~30 requests/minute on The Racing API free plan
