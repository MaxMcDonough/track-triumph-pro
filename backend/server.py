from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
import uuid
from datetime import datetime, timezone
import random

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

from racing_api import racing_api

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

DEFAULT_USER_ID = "default_user"

app = FastAPI(title="Horse Racing Betting Analyzer API")
api_router = APIRouter(prefix="/api")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ==================== MODELS ====================

class BankrollUpdate(BaseModel):
    current_bankroll: Optional[float] = None
    stop_loss: Optional[float] = None
    max_daily_bets: Optional[int] = None

class BetCreate(BaseModel):
    track: str
    race_number: int
    horse_name: str
    draw_number: int
    bet_type: str
    stake: float
    odds: float
    score: int

class BetSettle(BaseModel):
    result: str

class RaceAnalysisRequest(BaseModel):
    race_id: Optional[str] = None
    track: Optional[str] = None
    race_number: Optional[int] = None
    date: Optional[str] = None

# ==================== HELPERS ====================

async def ensure_default_bankroll():
    settings = await db.bankroll_settings.find_one({"user_id": DEFAULT_USER_ID}, {"_id": 0})
    if not settings:
        await db.bankroll_settings.insert_one({
            "user_id": DEFAULT_USER_ID,
            "starting_bankroll": 250.0,
            "current_bankroll": 250.0,
            "stop_loss": 60.0,
            "max_daily_bets": 5,
            "max_stake_percent": 0.03,
            "consecutive_losses": 0,
            "created_at": datetime.now(timezone.utc).isoformat()
        })
    return await db.bankroll_settings.find_one({"user_id": DEFAULT_USER_ID}, {"_id": 0})

# ==================== BANKROLL ENDPOINTS ====================

@api_router.get("/bankroll")
async def get_bankroll():
    settings = await ensure_default_bankroll()
    bets = await db.bets.find({
        "user_id": DEFAULT_USER_ID,
        "result": {"$ne": None}
    }, {"_id": 0}).to_list(1000)
    today_pl = sum(bet.get("profit_loss", 0) for bet in bets if bet.get("profit_loss"))
    return {
        **settings,
        "today_pl": today_pl,
        "cushion": settings["current_bankroll"] - settings["stop_loss"],
        "percent_above_stop_loss": ((settings["current_bankroll"] - settings["stop_loss"]) / settings["stop_loss"] * 100) if settings["stop_loss"] > 0 else 0
    }

@api_router.put("/bankroll")
async def update_bankroll(update: BankrollUpdate):
    await ensure_default_bankroll()
    update_data = {k: v for k, v in update.model_dump().items() if v is not None}
    if update_data:
        await db.bankroll_settings.update_one(
            {"user_id": DEFAULT_USER_ID},
            {"$set": update_data}
        )
    return await get_bankroll()

@api_router.post("/bankroll/reset")
async def reset_bankroll():
    settings = await ensure_default_bankroll()
    await db.bankroll_settings.update_one(
        {"user_id": DEFAULT_USER_ID},
        {"$set": {
            "current_bankroll": settings["starting_bankroll"],
            "consecutive_losses": 0
        }}
    )
    return await get_bankroll()

# ==================== 8-CRITERIA SCORING ====================

APPROVED_TRACKS = {
    'wolverhampton', 'southwell', 'chelmsford', 'kempton',
    'lingfield', 'newcastle', 'dundalk', 'curragh',
    'leopardstown', 'naas', 'downpatrick',
    'churchill-downs', 'santa-anita', 'gulfstream',
    'belmont', 'saratoga', 'keeneland', 'del-mar',
    # Add common UK/IRE courses from the API
    'ayr', 'ffos las', 'limerick', 'ascot', 'aintree',
    'cheltenham', 'doncaster', 'epsom', 'goodwood',
    'haydock', 'market rasen', 'musselburgh', 'perth',
    'redcar', 'sandown', 'sedgefield', 'thirsk',
    'warwick', 'wetherby', 'wincanton', 'windsor',
    'york', 'catterick', 'exeter', 'fontwell',
    'huntingdon', 'leicester', 'ludlow', 'newbury',
    'nottingham', 'plumpton', 'stratford', 'taunton',
    'uttoxeter', 'bath', 'beverley', 'brighton',
    'carlisle', 'chepstow', 'hamilton', 'hexham',
    'pontefract', 'ripon', 'towcester', 'bangor-on-dee',
    'cork', 'fairyhouse', 'galway', 'gowran park',
    'killarney', 'kilbeggan', 'laytown', 'listowel',
    'navan', 'punchestown', 'roscommon', 'sligo',
    'thurles', 'tipperary', 'tramore', 'wexford',
}


def calculate_horse_score(horse: Dict, track: str, bet_type: str = "PLACE") -> Dict:
    """Calculate 8-criteria score for a horse using available live data."""
    score = 0
    max_score = 8
    criteria = {}

    # Normalize track name for matching
    track_lower = track.lower().strip()

    # CRITERION 1: TRACK TYPE
    is_approved = any(t in track_lower for t in APPROVED_TRACKS) or track_lower in APPROVED_TRACKS
    if not is_approved:
        return {
            "score": 0, "max_score": max_score,
            "verdict": "REJECTED - Not approved track",
            "criteria_breakdown": {"track_type": "FAIL - Unapproved track: " + track}
        }
    criteria["track_type"] = "PASS - Approved track"

    # CRITERION 2: FORM COMPLETENESS
    form = horse.get("form_analysis", {})
    has_form = form.get("runs", 0) >= 3
    has_rating = horse.get("official_rating", 0) > 0

    if not has_form:
        return {
            "score": 0, "max_score": max_score,
            "verdict": "REJECTED - Insufficient form data",
            "criteria_breakdown": {
                **criteria,
                "complete_stats": "FAIL - Fewer than 3 runs on record"
            }
        }
    criteria["complete_stats"] = f"PASS - {form['runs']} runs, OR {horse.get('official_rating', 'N/A')}"

    # CRITERION 3: FORM & CONSISTENCY (replaces expert consensus for live data)
    form_score = 0
    place_rate = form.get("place_rate", 0)
    win_rate = form.get("win_rate", 0)

    if place_rate >= 50:
        form_score += 1
    if win_rate >= 20:
        form_score += 1

    score += form_score
    if form_score == 2:
        criteria["form_analysis"] = f"PASS 2/2 - Win {win_rate}%, Place {place_rate}%"
    elif form_score == 1:
        criteria["form_analysis"] = f"PARTIAL 1/2 - Win {win_rate}%, Place {place_rate}%"
    else:
        criteria["form_analysis"] = f"FAIL 0/2 - Win {win_rate}%, Place {place_rate}%"

    # CRITERION 4: RECENT TREND (replaces hot stats for live data)
    trend_score = 0
    trend = form.get("recent_trend", "unknown")
    last_pos = form.get("last_position")

    if trend == "improving":
        trend_score += 1
    if last_pos and 1 <= last_pos <= 3:
        trend_score += 1

    score += trend_score
    last_str = f"Last: {last_pos}" if last_pos else "Last: N/A"
    if trend_score == 2:
        criteria["recent_trend"] = f"PASS 2/2 - {trend.title()}, {last_str}"
    elif trend_score == 1:
        criteria["recent_trend"] = f"PARTIAL 1/2 - {trend.title()}, {last_str}"
    else:
        criteria["recent_trend"] = f"FAIL 0/2 - {trend.title()}, {last_str}"

    # CRITERION 5: OFFICIAL RATING VALUE
    rating_score = 0
    ofr = horse.get("official_rating", 0)
    if ofr > 0:
        # Higher rated horse in the field is a positive signal
        if ofr >= 90:
            rating_score = 1
            criteria["rating_value"] = f"PASS - OR {ofr} (strong)"
        elif ofr >= 70:
            rating_score = 1
            criteria["rating_value"] = f"PASS - OR {ofr} (competitive)"
        else:
            criteria["rating_value"] = f"FAIL - OR {ofr} (low rated)"
    else:
        criteria["rating_value"] = "FAIL - No official rating"
    score += rating_score

    # CRITERION 6: WEIGHT & CLASS
    weight_score = 0
    weight_lbs = horse.get("weight_lbs", 0)
    if weight_lbs > 0:
        # Lighter weight is generally better (in handicaps)
        if weight_lbs <= 150:
            weight_score = 1
            criteria["weight_class"] = f"PASS - {weight_lbs}lbs (light)"
        elif weight_lbs <= 165:
            criteria["weight_class"] = f"NEUTRAL - {weight_lbs}lbs (mid range)"
        else:
            criteria["weight_class"] = f"FAIL - {weight_lbs}lbs (heavy)"
    else:
        criteria["weight_class"] = "NEUTRAL - Weight not available"
    score += weight_score

    # CRITERION 7: FITNESS (days since last run)
    fitness_score = 0
    last_run = horse.get("last_run_days", 0)
    if 7 <= last_run <= 42:
        fitness_score = 1
        criteria["fitness"] = f"PASS - {last_run} days since last run (fit)"
    elif last_run > 0 and last_run < 7:
        criteria["fitness"] = f"NEUTRAL - {last_run} days (quick turnaround)"
    elif last_run > 42:
        criteria["fitness"] = f"FAIL - {last_run} days since last run (long layoff)"
    else:
        criteria["fitness"] = "NEUTRAL - Last run data unavailable"
    score += fitness_score

    # CRITERION 8: POSITIVE ANGLE
    angle_score = 0
    angles = []

    headgear = horse.get("headgear", "")
    if headgear and "first" in headgear.lower():
        angles.append("First-time headgear")

    if form.get("recent_trend") == "improving" and ofr >= 70:
        angles.append("Improving form + good rating")

    if last_pos and last_pos <= 2 and trend == "improving":
        angles.append("Recent podium + upward trend")

    if weight_lbs > 0 and weight_lbs <= 140 and ofr >= 80:
        angles.append("Well handicapped (light + high OR)")

    if angles:
        angle_score = 1
        criteria["positive_angle"] = f"PASS - {', '.join(angles)}"
    else:
        criteria["positive_angle"] = "NEUTRAL - No standout angles"
    score += angle_score

    # Confidence & recommendation
    if score >= 7:
        confidence, stars, rec = "90-95%", 5, "EXCELLENT BET - Strong recommend"
    elif score >= 6:
        confidence, stars, rec = "80-90%", 4, "STRONG BET - Recommend"
    elif score >= 5:
        confidence, stars, rec = "70-80%", 4, "GOOD BET - Acceptable"
    elif score >= 4:
        confidence, stars, rec = "60-70%", 3, "BORDERLINE - Proceed with caution"
    elif score >= 3:
        confidence, stars, rec = "50-60%", 2, "WEAK - Not recommended"
    else:
        confidence, stars, rec = "<50%", 1, "AVOID - Do not bet"

    return {
        "score": score,
        "max_score": max_score,
        "score_percentage": (score / max_score) * 100,
        "confidence_rating": confidence,
        "star_rating": stars,
        "recommendation": rec,
        "criteria_breakdown": criteria,
        "horse_name": horse.get("name"),
        "draw_number": horse.get("draw_number"),
    }


def calculate_stake(score: int, bankroll: float, bet_type: str) -> float:
    if score >= 7:
        pct = 0.03
    elif score >= 6:
        pct = 0.025
    elif score >= 5:
        pct = 0.02
    elif score >= 4:
        pct = 0.015
    else:
        pct = 0.01
    stake = bankroll * pct
    stake = round(stake * 2) / 2
    stake = max(stake, 2)
    stake = min(stake, bankroll * 0.03)
    return stake


def generate_warnings(scored_horses: List[Dict], bankroll: float, stop_loss: float, consecutive_losses: int) -> List[Dict]:
    warnings = []
    if scored_horses:
        top_score = max(h.get("score", 0) for h in scored_horses)
        if top_score < 4:
            warnings.append({
                "level": "HIGH",
                "message": f"Top pick only scores {top_score}/8 - No qualifying bets for this race",
                "action": "SKIP_RACE"
            })
    cushion = bankroll - stop_loss
    cushion_pct = (cushion / stop_loss) * 100 if stop_loss > 0 else 0
    if cushion_pct < 20:
        warnings.append({
            "level": "CRITICAL",
            "message": f"Only {cushion_pct:.0f}% above stop-loss - Extreme caution required",
            "action": "REDUCE_STAKES"
        })
    elif cushion_pct < 50:
        warnings.append({
            "level": "HIGH",
            "message": f"{cushion_pct:.0f}% above stop-loss - Be selective with bets",
            "action": "BE_SELECTIVE"
        })
    if consecutive_losses >= 2:
        warnings.append({
            "level": "CRITICAL",
            "message": f"STOP BETTING: {consecutive_losses} consecutive losses. Per strategy, stop for the day.",
            "action": "STOP_FOR_DAY"
        })
    elif consecutive_losses == 1:
        warnings.append({
            "level": "HIGH",
            "message": "WARNING: 1 loss away from mandatory stop. Next bet is critical.",
            "action": "PROCEED_WITH_CAUTION"
        })
    return warnings


def build_recommendations(scored_horses: List[Dict], bankroll: float):
    """Build WIN, PLACE, TRIFECTA, and SAFETY recommendations from scored horses."""
    win_sorted = sorted(scored_horses, key=lambda h: h["win_score"]["score"], reverse=True)
    place_sorted = sorted(scored_horses, key=lambda h: h["place_score"]["score"], reverse=True)

    win_rec = None
    top = win_sorted[0] if win_sorted else None
    if top and top["win_score"]["score"] >= 3:
        stake = calculate_stake(top["win_score"]["score"], bankroll, "WIN")
        est_odds = max(2.0, 12.0 - top["win_score"]["score"])  # Estimate based on score
        win_rec = {
            "type": "WIN",
            "horse": top["name"],
            "draw_number": top.get("draw_number", top.get("number", 0)),
            "odds": est_odds,
            "bookmaker": "Estimated",
            "score": top["win_score"]["score"],
            "max_score": top["win_score"]["max_score"],
            "confidence": top["win_score"]["confidence_rating"],
            "star_rating": top["win_score"]["star_rating"],
            "stake": stake,
            "potential_return": round(stake * est_odds, 2),
            "potential_profit": round((stake * est_odds) - stake, 2),
            "criteria_breakdown": top["win_score"]["criteria_breakdown"],
            "recommendation": top["win_score"]["recommendation"],
        }

    place_rec = None
    top_p = place_sorted[0] if place_sorted else None
    if top_p and top_p["place_score"]["score"] >= 3:
        stake = calculate_stake(top_p["place_score"]["score"], bankroll, "PLACE")
        est_place_odds = max(1.5, (12.0 - top_p["place_score"]["score"]) / 3 + 1)
        place_rec = {
            "type": "PLACE",
            "horse": top_p["name"],
            "draw_number": top_p.get("draw_number", top_p.get("number", 0)),
            "odds": round(est_place_odds, 2),
            "bookmaker": "Estimated",
            "score": top_p["place_score"]["score"],
            "max_score": top_p["place_score"]["max_score"],
            "confidence": top_p["place_score"]["confidence_rating"],
            "star_rating": top_p["place_score"]["star_rating"],
            "stake": stake,
            "potential_return": round(stake * est_place_odds, 2),
            "potential_profit": round((stake * est_place_odds) - stake, 2),
            "criteria_breakdown": top_p["place_score"]["criteria_breakdown"],
            "recommendation": top_p["place_score"]["recommendation"],
        }

    tri_rec = None
    top3 = place_sorted[:3]
    if len(top3) >= 3:
        avg = sum(h["place_score"]["score"] for h in top3) / 3
        tri_rec = {
            "type": "BOX_TRIFECTA",
            "horses": [
                {"position": i + 1, "name": h["name"], "draw_number": h.get("draw_number", 0),
                 "score": h["place_score"]["score"], "confidence": h["place_score"]["confidence_rating"]}
                for i, h in enumerate(top3)
            ],
            "unit_stake": 2,
            "total_combinations": 6,
            "total_stake": 12,
            "avg_score": round(avg, 1),
            "confidence": "75-85%" if avg >= 6 else ("65-75%" if avg >= 5 else "50-65%"),
            "star_rating": 4 if avg >= 6 else (3 if avg >= 5 else 2),
            "recommendation": "Box trifecta - These 3 to finish top 3 in any order",
        }

    safety_rec = None
    safety_candidates = [h for h in place_sorted if h["place_score"]["score"] >= 4]
    if safety_candidates:
        s = safety_candidates[0]
        stake = min(calculate_stake(s["place_score"]["score"], bankroll, "PLACE"), bankroll * 0.015)
        est_odds = max(1.5, (12.0 - s["place_score"]["score"]) / 3 + 1)
        safety_rec = {
            "type": "SAFETY_PLACE",
            "horse": s["name"],
            "draw_number": s.get("draw_number", 0),
            "odds": round(est_odds, 2),
            "bookmaker": "Estimated",
            "score": s["place_score"]["score"],
            "confidence": "60-70%",
            "star_rating": 3,
            "stake": stake,
            "potential_return": round(stake * est_odds, 2),
            "potential_profit": round((stake * est_odds) - stake, 2),
            "recommendation": "Conservative PLACE bet - Lower risk option",
        }

    return {"win": win_rec, "place": place_rec, "trifecta": tri_rec, "safety": safety_rec}


# ==================== LIVE DATA ENDPOINTS ====================

@api_router.get("/racecards/today")
async def get_todays_racecards():
    """Get today's live racecards from The Racing API."""
    result = await racing_api.get_racecards_free()
    if "error" in result:
        return {"success": False, "error": result["error"], "racecards": []}

    raw_cards = result.get("data", {}).get("racecards", [])
    # Group by course
    courses = {}
    all_races = []
    for rc in raw_cards:
        transformed = racing_api.transform_racecard(rc)
        course = transformed["course"]
        if course not in courses:
            courses[course] = {
                "course": course,
                "region": transformed["region"],
                "going": transformed["going"],
                "surface": transformed["surface"],
                "races": [],
            }
        courses[course]["races"].append({
            "race_id": transformed["race_id"],
            "off_time": transformed["off_time"],
            "race_name": transformed["race_name"],
            "race_type": transformed["race_type"],
            "race_class": transformed["race_class"],
            "distance": transformed["distance"],
            "field_size": transformed["field_size"],
            "prize": transformed["prize"],
            "going": transformed["going"],
        })
        all_races.append(transformed)

    return {
        "success": True,
        "data_source": "LIVE - The Racing API",
        "date": raw_cards[0]["date"] if raw_cards else datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "total_races": len(raw_cards),
        "courses": list(courses.values()),
        "races": all_races,
    }


@api_router.get("/best-bets")
async def get_best_bets():
    """Auto-scan all today's races and return the top picks."""
    result = await racing_api.get_racecards_free()
    if "error" in result:
        return {"success": False, "error": result["error"], "picks": []}

    settings = await ensure_default_bankroll()
    bankroll = settings.get("current_bankroll", 250.0)

    raw_cards = result.get("data", {}).get("racecards", [])
    all_picks = []

    for rc in raw_cards:
        transformed = racing_api.transform_racecard(rc)
        track = transformed["course"]
        for horse in transformed["runners"]:
            ps = calculate_horse_score(horse, track, "PLACE")
            if ps["score"] >= 4:
                stake = calculate_stake(ps["score"], bankroll, "PLACE")
                est_odds = max(1.5, (12.0 - ps["score"]) / 3 + 1)
                all_picks.append({
                    "race_id": transformed["race_id"],
                    "course": track,
                    "off_time": transformed["off_time"],
                    "race_name": transformed["race_name"],
                    "race_type": transformed["race_type"],
                    "race_class": transformed["race_class"],
                    "distance": transformed["distance"],
                    "going": transformed["going"],
                    "horse": horse["name"],
                    "draw_number": horse.get("draw_number", 0),
                    "jockey": horse.get("jockey_name", ""),
                    "trainer": horse.get("trainer_name", ""),
                    "form": horse.get("form", ""),
                    "official_rating": horse.get("official_rating", 0),
                    "score": ps["score"],
                    "max_score": ps["max_score"],
                    "confidence": ps["confidence_rating"],
                    "star_rating": ps["star_rating"],
                    "recommendation": ps["recommendation"],
                    "criteria_breakdown": ps["criteria_breakdown"],
                    "estimated_odds": round(est_odds, 2),
                    "recommended_stake": stake,
                    "potential_profit": round((stake * est_odds) - stake, 2),
                })

    all_picks.sort(key=lambda p: p["score"], reverse=True)
    top_picks = all_picks[:10]

    return {
        "success": True,
        "data_source": "LIVE - The Racing API",
        "date": raw_cards[0]["date"] if raw_cards else datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "total_races_scanned": len(raw_cards),
        "total_qualifying": len(all_picks),
        "picks": top_picks,
    }


@api_router.get("/results")
async def get_race_results():
    """Get today's race results from The Racing API + user's bet outcomes."""
    # Fetch live results
    api_result = await racing_api.get_results_today()
    live_results = []
    results_available = False
    if api_result.get("success"):
        results_available = True
        for r in api_result.get("data", {}).get("results", []):
            runners = []
            for runner in r.get("runners", []):
                runners.append({
                    "position": runner.get("position", ""),
                    "horse": runner.get("horse", ""),
                    "jockey": runner.get("jockey", ""),
                    "trainer": runner.get("trainer", ""),
                    "sp": runner.get("sp", ""),
                    "distance_beaten": runner.get("distance_beaten", ""),
                })
            runners.sort(key=lambda x: int(x["position"]) if x["position"].isdigit() else 999)
            live_results.append({
                "race_id": r.get("race_id", ""),
                "course": r.get("course", ""),
                "off_time": r.get("off_time", ""),
                "race_name": r.get("race_name", ""),
                "distance": r.get("distance_f", ""),
                "going": r.get("going", ""),
                "race_class": r.get("race_class", ""),
                "race_type": r.get("type", ""),
                "prize": r.get("prize", ""),
                "runners": runners,
                "winner": runners[0]["horse"] if runners and runners[0].get("position") == "1" else "",
            })

    # Fetch user's settled bets
    settled_bets = await db.bets.find(
        {"user_id": DEFAULT_USER_ID, "result": {"$ne": None}},
        {"_id": 0}
    ).sort("timestamp", -1).to_list(50)

    # Fetch user's pending bets
    pending_bets = await db.bets.find(
        {"user_id": DEFAULT_USER_ID, "result": None},
        {"_id": 0}
    ).sort("timestamp", -1).to_list(50)

    return {
        "success": True,
        "live_results": live_results,
        "live_results_count": len(live_results),
        "settled_bets": settled_bets,
        "pending_bets": pending_bets,
        "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
    }


@api_router.post("/analyze")
async def analyze_race(request: RaceAnalysisRequest):
    """Analyze a race using live data (by race_id) or mock data (by track+race_number)."""
    settings = await ensure_default_bankroll()
    bankroll = settings.get("current_bankroll", 250.0)
    stop_loss = settings.get("stop_loss", 60.0)
    consecutive_losses = settings.get("consecutive_losses", 0)

    # If race_id provided, use live data
    if request.race_id:
        return await _analyze_live_race(request.race_id, bankroll, stop_loss, consecutive_losses)

    # Fallback: mock data
    return await _analyze_mock_race(request.track or "wolverhampton", request.race_number or 1,
                                     request.date, bankroll, stop_loss, consecutive_losses)


async def _analyze_live_race(race_id: str, bankroll: float, stop_loss: float, consecutive_losses: int):
    """Analyze a specific race from live racecards."""
    result = await racing_api.get_racecards_free()
    if "error" in result:
        raise HTTPException(status_code=502, detail=result["error"])

    raw_cards = result.get("data", {}).get("racecards", [])
    target = None
    for rc in raw_cards:
        if rc.get("race_id") == race_id:
            target = rc
            break

    if not target:
        raise HTTPException(status_code=404, detail=f"Race {race_id} not found in today's racecards")

    transformed = racing_api.transform_racecard(target)
    track = transformed["course"]
    runners = transformed["runners"]

    scored = []
    for horse in runners:
        ws = calculate_horse_score(horse, track, "WIN")
        ps = calculate_horse_score(horse, track, "PLACE")
        scored.append({**horse, "win_score": ws, "place_score": ps})

    recs = build_recommendations(scored, bankroll)
    warnings = generate_warnings(
        [{"score": h["place_score"]["score"]} for h in scored],
        bankroll, stop_loss, consecutive_losses
    )

    return {
        "success": True,
        "data_source": "LIVE - The Racing API",
        "race_info": {
            "race_id": race_id,
            "track": track,
            "race_name": transformed["race_name"],
            "off_time": transformed["off_time"],
            "race_type": transformed["race_type"],
            "race_class": transformed["race_class"],
            "distance": transformed["distance"],
            "going": transformed["going"],
            "surface": transformed["surface"],
            "field_size": len(runners),
            "date": transformed["date"],
        },
        "recommendations": recs,
        "all_horses": scored,
        "bankroll_status": {
            "current": bankroll,
            "stop_loss": stop_loss,
            "cushion": bankroll - stop_loss,
            "percent_above_stop_loss": ((bankroll - stop_loss) / stop_loss * 100) if stop_loss > 0 else 0
        },
        "warnings": warnings,
    }


async def _analyze_mock_race(track: str, race_number: int, date: Optional[str],
                              bankroll: float, stop_loss: float, consecutive_losses: int):
    """Analyze with mock data (fallback)."""
    horses = _generate_mock_data(track, race_number)
    scored = []
    for horse in horses:
        ws = calculate_horse_score(horse, track, "WIN")
        ps = calculate_horse_score(horse, track, "PLACE")
        scored.append({**horse, "win_score": ws, "place_score": ps})

    recs = build_recommendations(scored, bankroll)
    warnings = generate_warnings(
        [{"score": h["place_score"]["score"]} for h in scored],
        bankroll, stop_loss, consecutive_losses
    )

    return {
        "success": True,
        "data_source": "MOCK - Demo data",
        "race_info": {
            "track": track,
            "race_number": race_number,
            "date": date or datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "field_size": len(horses),
        },
        "recommendations": recs,
        "all_horses": scored,
        "bankroll_status": {
            "current": bankroll,
            "stop_loss": stop_loss,
            "cushion": bankroll - stop_loss,
            "percent_above_stop_loss": ((bankroll - stop_loss) / stop_loss * 100) if stop_loss > 0 else 0
        },
        "warnings": warnings,
    }


def _generate_mock_data(track: str, race_number: int) -> List[Dict]:
    names = ["Thunder Bolt", "Silver Storm", "Golden Arrow", "Dark Knight",
             "Flying Spirit", "Royal Champion", "Lucky Star", "Midnight Run",
             "Fast Forward", "Wild Card", "Storm Chaser", "Iron Will"]
    jockeys = ["J. Murphy", "T. Marquand", "W. Buick", "R. Havlin", "D. Tudhope", "H. Bentley"]
    trainers = ["J. Gosden", "C. Appleby", "A. Balding", "W. Haggas", "R. Varian", "M. Johnston"]

    num = random.randint(8, 12)
    horses = []
    for i in range(num):
        form_str = "".join([str(random.randint(1, 9)) for _ in range(6)])
        horses.append({
            "name": names[i % len(names)],
            "draw_number": i + 1,
            "number": i + 1,
            "jockey_name": random.choice(jockeys),
            "trainer_name": random.choice(trainers),
            "age": str(random.randint(3, 7)),
            "weight_lbs": random.randint(130, 175),
            "official_rating": random.randint(50, 110),
            "form": form_str,
            "form_analysis": racing_api.parse_form(form_str),
            "last_run_days": random.randint(5, 60),
            "headgear": "",
            "sire": "", "dam": "", "owner": "",
            "horse_id": "", "jockey_id": "", "trainer_id": "",
            "sex": "gelding",
        })
    return horses


# ==================== BET MANAGEMENT ====================

@api_router.post("/bets")
async def place_bet(bet_data: BetCreate):
    settings = await ensure_default_bankroll()
    bankroll = settings.get("current_bankroll", 0)
    stop_loss = settings.get("stop_loss", 0)
    consecutive_losses = settings.get("consecutive_losses", 0)

    if bankroll - bet_data.stake < stop_loss:
        raise HTTPException(status_code=400, detail="Bet would breach stop-loss")
    if consecutive_losses >= 2:
        raise HTTPException(status_code=400, detail="Two consecutive losses - betting stopped for today")
    max_stake = bankroll * settings.get("max_stake_percent", 0.03)
    if bet_data.stake > max_stake:
        raise HTTPException(status_code=400, detail=f"Stake exceeds maximum ({max_stake:.2f})")

    bet_id = f"bet_{uuid.uuid4().hex[:12]}"
    bet_doc = {
        "bet_id": bet_id,
        "user_id": DEFAULT_USER_ID,
        "track": bet_data.track,
        "race_number": bet_data.race_number,
        "horse_name": bet_data.horse_name,
        "draw_number": bet_data.draw_number,
        "bet_type": bet_data.bet_type,
        "stake": bet_data.stake,
        "odds": bet_data.odds,
        "score": bet_data.score,
        "result": None,
        "profit_loss": None,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    await db.bets.insert_one(bet_doc)
    new_bankroll = bankroll - bet_data.stake
    await db.bankroll_settings.update_one(
        {"user_id": DEFAULT_USER_ID},
        {"$set": {"current_bankroll": new_bankroll}}
    )
    return {"bet_id": bet_id, "message": "Bet placed successfully", "new_bankroll": new_bankroll}


@api_router.post("/bets/{bet_id}/settle")
async def settle_bet(bet_id: str, settle_data: BetSettle):
    bet = await db.bets.find_one({"bet_id": bet_id, "user_id": DEFAULT_USER_ID}, {"_id": 0})
    if not bet:
        raise HTTPException(status_code=404, detail="Bet not found")
    if bet.get("result"):
        raise HTTPException(status_code=400, detail="Bet already settled")

    settings = await ensure_default_bankroll()
    bankroll = settings.get("current_bankroll", 0)
    consecutive_losses = settings.get("consecutive_losses", 0)

    if settle_data.result == "WIN":
        profit_loss = (bet["stake"] * bet["odds"]) - bet["stake"]
        new_bankroll = bankroll + bet["stake"] + profit_loss
        consecutive_losses = 0
        message = f"BET WON! +${profit_loss:.2f}. New bankroll: ${new_bankroll:.2f}"
    else:
        profit_loss = -bet["stake"]
        new_bankroll = bankroll
        consecutive_losses += 1
        must_stop = consecutive_losses >= 2
        message = f"BET LOST. -${bet['stake']:.2f}. " + (
            f"{consecutive_losses} losses in a row. STOP BETTING FOR TODAY." if must_stop
            else f"New bankroll: ${new_bankroll:.2f}"
        )

    await db.bets.update_one(
        {"bet_id": bet_id},
        {"$set": {"result": settle_data.result, "profit_loss": profit_loss}}
    )
    await db.bankroll_settings.update_one(
        {"user_id": DEFAULT_USER_ID},
        {"$set": {"current_bankroll": new_bankroll, "consecutive_losses": consecutive_losses}}
    )
    return {
        "outcome": settle_data.result,
        "profit_loss": profit_loss,
        "new_bankroll": new_bankroll,
        "consecutive_losses": consecutive_losses,
        "must_stop": consecutive_losses >= 2,
        "message": message
    }


@api_router.get("/bets")
async def get_bets():
    bets = await db.bets.find({"user_id": DEFAULT_USER_ID}, {"_id": 0}).sort("timestamp", -1).to_list(100)
    return {"bets": bets}


@api_router.get("/statistics")
async def get_statistics():
    bets = await db.bets.find({"user_id": DEFAULT_USER_ID, "result": {"$ne": None}}, {"_id": 0}).to_list(1000)
    settings = await ensure_default_bankroll()

    if not bets:
        return {
            "overall": {
                "total_bets": 0, "wins": 0, "losses": 0, "win_rate": "0%",
                "total_staked": "0.00", "total_profit": "0.00", "roi": "0%"
            },
            "by_score": {},
            "recent_form": {"last_10_bets": "", "consecutive_losses": 0}
        }

    wins = len([b for b in bets if b.get("result") == "WIN"])
    losses = len([b for b in bets if b.get("result") == "LOSS"])
    total_staked = sum(b.get("stake", 0) for b in bets)
    total_profit = sum(b.get("profit_loss", 0) for b in bets)
    roi = (total_profit / total_staked * 100) if total_staked > 0 else 0
    win_rate = (wins / len(bets) * 100) if bets else 0

    by_score = {}
    for s in range(3, 9):
        sb = [b for b in bets if b.get("score") == s]
        if sb:
            sw = len([b for b in sb if b.get("result") == "WIN"])
            ss = sum(b.get("stake", 0) for b in sb)
            sp = sum(b.get("profit_loss", 0) for b in sb)
            by_score[str(s)] = {
                "bets": len(sb), "wins": sw,
                "win_rate": f"{(sw / len(sb) * 100):.1f}%",
                "total_staked": f"{ss:.2f}",
                "total_profit": f"{sp:.2f}",
                "roi": f"{(sp / ss * 100):.1f}%" if ss > 0 else "0%"
            }

    recent = sorted(bets, key=lambda b: b.get("timestamp", ""), reverse=True)[:10]
    last_10 = "".join(["W" if b.get("result") == "WIN" else "L" for b in recent])

    return {
        "overall": {
            "total_bets": len(bets), "wins": wins, "losses": losses,
            "win_rate": f"{win_rate:.1f}%",
            "total_staked": f"{total_staked:.2f}",
            "total_profit": f"{total_profit:.2f}",
            "roi": f"{roi:.1f}%",
            "current_bankroll": f"{settings.get('current_bankroll', 0):.2f}",
            "starting_bankroll": f"{settings.get('starting_bankroll', 250):.2f}"
        },
        "by_score": by_score,
        "recent_form": {
            "last_10_bets": last_10,
            "consecutive_losses": settings.get("consecutive_losses", 0)
        }
    }


# ==================== TRACKS ====================

@api_router.get("/tracks")
async def get_tracks():
    return {
        "uk_tracks": [
            {"id": "wolverhampton", "name": "Wolverhampton (AW)", "country": "UK"},
            {"id": "southwell", "name": "Southwell (AW)", "country": "UK"},
            {"id": "chelmsford", "name": "Chelmsford (AW)", "country": "UK"},
            {"id": "kempton", "name": "Kempton (AW)", "country": "UK"},
            {"id": "lingfield", "name": "Lingfield (AW)", "country": "UK"},
            {"id": "newcastle", "name": "Newcastle (AW)", "country": "UK"},
            {"id": "dundalk", "name": "Dundalk", "country": "Ireland"},
            {"id": "curragh", "name": "Curragh", "country": "Ireland"},
            {"id": "leopardstown", "name": "Leopardstown", "country": "Ireland"},
            {"id": "naas", "name": "Naas", "country": "Ireland"},
        ],
        "us_tracks": [
            {"id": "churchill-downs", "name": "Churchill Downs", "country": "USA"},
            {"id": "santa-anita", "name": "Santa Anita", "country": "USA"},
            {"id": "gulfstream", "name": "Gulfstream Park", "country": "USA"},
            {"id": "belmont", "name": "Belmont Park", "country": "USA"},
            {"id": "saratoga", "name": "Saratoga", "country": "USA"},
            {"id": "keeneland", "name": "Keeneland", "country": "USA"},
            {"id": "del-mar", "name": "Del Mar", "country": "USA"},
        ]
    }


@api_router.get("/scraper/status")
async def get_scraper_status():
    return {
        "the_racing_api": {
            "configured": racing_api.configured,
            "source": "The Racing API (theracingapi.com)",
            "status": "connected" if racing_api.configured else "not configured"
        },
        "racing_post": {"configured": False, "source": "Racing Post"},
        "betfair": {"configured": False, "source": "Betfair Exchange"},
        "timeform": {"configured": False, "source": "Timeform"},
        "at_the_races": {"configured": False, "source": "At The Races"},
        "oddschecker": {"configured": False, "source": "OddsChecker"},
    }


@api_router.get("/")
async def root():
    return {"message": "Horse Racing Betting Analyzer API", "status": "running"}


# Include router and middleware
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
