# Horse Racing Betting Analyzer - PRD

## Original Problem Statement
Build a comprehensive, professional-grade horse racing betting analysis web application that implements a proven statistical betting strategy. The system applies an 8-criteria scoring algorithm and provides actionable betting recommendations with confidence ratings and bankroll management.

## User Choices
- Dark mode default
- No login required (removed per user request)
- Full MVP with all features
- Default bankroll $250, Stop-loss $60
- Scraping infrastructure ready (API keys to be configured later)

## Architecture

### Backend (FastAPI + MongoDB)
- `/api/bankroll` - Get/Update bankroll settings
- `/api/tracks` - List approved UK/US tracks
- `/api/analyze` - 8-criteria race analysis
- `/api/bets` - Bet CRUD operations
- `/api/statistics` - Performance statistics
- `/api/scraper/status` - Data source configuration status

### Frontend (React + Tailwind + Shadcn UI)
- Dashboard - Bankroll widget, quick stats, recent bets
- Race Analysis - Track/race selection, recommendations, horse breakdown
- Bet History - Track/settle bets, filter by status
- Statistics - ROI/win rate charts, performance by score
- Settings - Bankroll config, discipline rules display

## Core Requirements (Static)
1. 8-Criteria Scoring Algorithm
   - Track Type (approved UK/US tracks only)
   - Complete Statistics
   - Expert Consensus (Racing Post + At The Races)
   - Hot Statistics (20%+ trainer/jockey)
   - Odds Value
   - Market Confidence
   - Third Expert Opinion (Timeform)
   - Positive Angle

2. Betting Recommendations
   - WIN bet recommendation
   - PLACE bet recommendation
   - Box Trifecta recommendation
   - Safety bet recommendation

3. Bankroll Management
   - Stop-loss protection
   - Two-loss rule (stop after 2 consecutive losses)
   - Maximum stake rule (3% of bankroll)
   - Daily bet limit
   - Chasing detection

## What's Been Implemented (Feb 2026)
- ✅ Full backend API with 8-criteria scoring
- ✅ Mock race data generator (scraping infrastructure ready)
- ✅ Bankroll management with all discipline rules
- ✅ Dark mode UI with professional design
- ✅ Dashboard with bankroll widget and quick actions
- ✅ Race analysis with detailed recommendations
- ✅ Bet history with settle functionality
- ✅ Statistics with charts (Recharts)
- ✅ Settings page with data source status

## Prioritized Backlog

### P0 (Done)
- [x] 8-criteria scoring algorithm
- [x] Bankroll management
- [x] Race analysis UI
- [x] Bet tracking and settlement

### P1 (Next)
- [ ] Configure actual data sources (Racing Post, Betfair, etc.)
- [ ] Real-time odds integration
- [ ] Push notifications for qualifying bets

### P2 (Future)
- [ ] User authentication (if needed)
- [ ] Historical data analysis
- [ ] Auto-bet execution
- [ ] Mobile app

## Tech Stack
- Backend: Python FastAPI, Motor (MongoDB async)
- Frontend: React, Tailwind CSS, Shadcn UI, Recharts
- Database: MongoDB
- Fonts: Chivo (headings), Manrope (body), JetBrains Mono (data)
