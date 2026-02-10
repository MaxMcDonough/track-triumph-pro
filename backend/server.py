from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict
import uuid
from datetime import datetime, timezone
import random

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Default user ID for no-auth mode
DEFAULT_USER_ID = "default_user"

# Create the main app
app = FastAPI(title="Horse Racing Betting Analyzer API")
api_router = APIRouter(prefix="/api")

# Configure logging
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
    result: str  # WIN or LOSS

class RaceAnalysisRequest(BaseModel):
    track: str
    race_number: int
    date: Optional[str] = None

# ==================== HELPER FUNCTIONS ====================

async def ensure_default_bankroll():
    """Ensure default user has bankroll settings"""
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
    """Get bankroll settings"""
    settings = await ensure_default_bankroll()
    
    # Calculate today's P/L
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
    """Update bankroll settings"""
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
    """Reset bankroll to starting amount"""
    settings = await ensure_default_bankroll()
    await db.bankroll_settings.update_one(
        {"user_id": DEFAULT_USER_ID},
        {"$set": {
            "current_bankroll": settings["starting_bankroll"],
            "consecutive_losses": 0
        }}
    )
    return await get_bankroll()

# ==================== 8-CRITERIA SCORING ALGORITHM ====================

APPROVED_UK_TRACKS = [
    'wolverhampton', 'southwell', 'chelmsford', 'kempton',
    'lingfield', 'newcastle', 'dundalk', 'curragh',
    'leopardstown', 'naas', 'downpatrick'
]

APPROVED_US_TRACKS = [
    'churchill-downs', 'santa-anita', 'gulfstream',
    'belmont', 'saratoga', 'keeneland', 'del-mar'
]

def calculate_horse_score(horse: Dict, track: str, bet_type: str = "PLACE") -> Dict:
    """Calculate 8-criteria score for a horse"""
    score = 0
    max_score = 8
    criteria_breakdown = {}
    
    # CRITERION 1: TRACK TYPE (Pass/Fail)
    is_approved_track = track.lower() in APPROVED_UK_TRACKS or track.lower() in APPROVED_US_TRACKS
    if not is_approved_track:
        return {
            "score": 0,
            "max_score": max_score,
            "verdict": "REJECTED - Not approved track",
            "criteria_breakdown": {"track_type": "FAIL - International/minor track"}
        }
    criteria_breakdown["track_type"] = "✅ PASS - Approved UK/US track"
    
    # CRITERION 2: COMPLETE STATISTICS (Pass/Fail)
    has_complete_stats = all([
        horse.get("trainer_last_14_days_percent") is not None,
        horse.get("jockey_last_14_days_percent") is not None,
        horse.get("course_percent") is not None,
        horse.get("distance_percent") is not None
    ])
    
    if not has_complete_stats:
        return {
            "score": 0,
            "max_score": max_score,
            "verdict": "REJECTED - Incomplete data",
            "criteria_breakdown": {
                **criteria_breakdown,
                "complete_stats": "FAIL - Missing critical statistics"
            }
        }
    criteria_breakdown["complete_stats"] = "✅ PASS - All statistics available"
    
    # CRITERION 3: EXPERT CONSENSUS (0-2 points)
    expert_score = 0
    expert_details = []
    
    if horse.get("racing_post_top3_position") and horse["racing_post_top3_position"] > 0:
        expert_score += 1
        expert_details.append(f"Racing Post: #{horse['racing_post_top3_position']}")
    
    if horse.get("at_the_races_top3_position") and horse["at_the_races_top3_position"] > 0:
        expert_score += 1
        expert_details.append(f"At The Races: #{horse['at_the_races_top3_position']}")
    
    score += expert_score
    
    if expert_score == 2:
        criteria_breakdown["expert_consensus"] = f"✅ 2/2 - {', '.join(expert_details)}"
    elif expert_score == 1:
        criteria_breakdown["expert_consensus"] = f"⚠️ 1/2 - {', '.join(expert_details)}"
    else:
        criteria_breakdown["expert_consensus"] = "❌ 0/2 - Not in expert top 3"
    
    # CRITERION 4: HOT STATISTICS (0-2 points)
    HOT_THRESHOLD = 20
    hot_stats_score = 0
    hot_stats_details = []
    
    trainer_percent = horse.get("trainer_last_14_days_percent", 0)
    if trainer_percent >= HOT_THRESHOLD:
        hot_stats_score += 1
        hot_stats_details.append(f"Trainer: {trainer_percent}% 🔥")
    else:
        hot_stats_details.append(f"Trainer: {trainer_percent}%")
    
    jockey_percent = horse.get("jockey_last_14_days_percent", 0)
    if jockey_percent >= HOT_THRESHOLD:
        hot_stats_score += 1
        hot_stats_details.append(f"Jockey: {jockey_percent}% 🔥")
    else:
        hot_stats_details.append(f"Jockey: {jockey_percent}%")
    
    score += hot_stats_score
    
    if hot_stats_score == 2:
        criteria_breakdown["hot_stats"] = f"✅ 2/2 - {', '.join(hot_stats_details)}"
    elif hot_stats_score == 1:
        criteria_breakdown["hot_stats"] = f"⚠️ 1/2 - {', '.join(hot_stats_details)}"
    else:
        criteria_breakdown["hot_stats"] = f"❌ 0/2 - {', '.join(hot_stats_details)}"
    
    # CRITERION 5: ODDS VALUE (0-1 points)
    odds_score = 0
    if bet_type == "WIN":
        win_odds = horse.get("best_win_odds", 0)
        if 2.0 <= win_odds <= 9.0:
            odds_score = 1
            criteria_breakdown["odds_value"] = f"✅ WIN odds {win_odds:.2f} - Good value"
        elif win_odds < 2.0:
            criteria_breakdown["odds_value"] = f"❌ WIN odds {win_odds:.2f} - Too short"
        else:
            criteria_breakdown["odds_value"] = f"❌ WIN odds {win_odds:.2f} - Too long"
    else:
        place_odds = horse.get("best_place_odds", 0)
        if place_odds >= 1.83:
            odds_score = 1
            criteria_breakdown["odds_value"] = f"✅ PLACE odds {place_odds:.2f} - Good value"
        else:
            criteria_breakdown["odds_value"] = f"❌ PLACE odds {place_odds:.2f} - Too short"
    
    score += odds_score
    
    # CRITERION 6: MARKET CONFIDENCE (0-1 points)
    market_score = 0
    volume = horse.get("betfair_matched_volume", 0)
    movement = horse.get("betfair_price_movement", "stable")
    sharp_money = horse.get("betfair_sharp_money_indicator", "none")
    
    if (volume > 50000 and movement == "steam") or sharp_money == "strong":
        market_score = 1
        criteria_breakdown["market_confidence"] = f"✅ Strong market support (£{volume/1000:.0f}k matched, {movement})"
    elif movement == "drift":
        criteria_breakdown["market_confidence"] = "❌ Drifting in odds (negative signal)"
    else:
        criteria_breakdown["market_confidence"] = "⚠️ Moderate market activity"
    
    score += market_score
    
    # CRITERION 7: THIRD EXPERT OPINION (0-1 points)
    timeform_score = 0
    timeform_rating = horse.get("timeform_rating", 0)
    timeform_flags = horse.get("timeform_flags", [])
    
    has_strong_timeform = timeform_rating >= 80
    has_timeform_flags = any(f in timeform_flags for f in ['!', '↑', 'C'])
    
    if has_strong_timeform and (expert_score >= 1 or has_timeform_flags):
        timeform_score = 1
        flags_str = f" ({', '.join(timeform_flags)})" if timeform_flags else ""
        criteria_breakdown["timeform_opinion"] = f"✅ Timeform {timeform_rating}{flags_str}"
    else:
        criteria_breakdown["timeform_opinion"] = f"⚠️ Timeform {timeform_rating or 'N/A'}"
    
    score += timeform_score
    
    # CRITERION 8: POSITIVE ANGLE (0-1 points)
    angle_score = 0
    positive_angles = []
    
    if horse.get("class_movement") == "dropping":
        positive_angles.append("Class drop")
    if horse.get("first_time_blinkers") or horse.get("first_time_tongue_tie"):
        positive_angles.append("First-time equipment")
    if horse.get("course_percent", 0) >= 25:
        positive_angles.append(f"Track specialist ({horse['course_percent']}%)")
    if horse.get("trainer_after_break_percent", 0) >= 25:
        positive_angles.append("Trainer after break angle")
    if horse.get("draw_advantage") == "strong":
        positive_angles.append("Favorable draw")
    if horse.get("pace_advantage") == "sole front-runner":
        positive_angles.append("Sole early speed")
    
    if positive_angles:
        angle_score = 1
        criteria_breakdown["positive_angle"] = f"✅ {', '.join(positive_angles)}"
    else:
        criteria_breakdown["positive_angle"] = "⚠️ No standout angles"
    
    score += angle_score
    
    # Calculate confidence and recommendations
    score_percentage = (score / max_score) * 100
    
    if score >= 7:
        confidence_rating = "90-95%"
        star_rating = 5
        recommendation = "EXCELLENT BET - Strong recommend"
    elif score >= 6:
        confidence_rating = "80-90%"
        star_rating = 4
        recommendation = "STRONG BET - Recommend"
    elif score >= 5:
        confidence_rating = "70-80%"
        star_rating = 4
        recommendation = "GOOD BET - Acceptable"
    elif score >= 4:
        confidence_rating = "60-70%"
        star_rating = 3
        recommendation = "BORDERLINE - Proceed with caution"
    elif score >= 3:
        confidence_rating = "50-60%"
        star_rating = 2
        recommendation = "WEAK - Not recommended"
    else:
        confidence_rating = "<50%"
        star_rating = 1
        recommendation = "AVOID - Do not bet"
    
    return {
        "score": score,
        "max_score": max_score,
        "score_percentage": score_percentage,
        "confidence_rating": confidence_rating,
        "star_rating": star_rating,
        "recommendation": recommendation,
        "criteria_breakdown": criteria_breakdown,
        "horse_name": horse.get("name"),
        "draw_number": horse.get("draw_number"),
        "current_odds": {
            "win": horse.get("best_win_odds"),
            "place": horse.get("best_place_odds")
        }
    }

def calculate_stake(score: int, bankroll: float, bet_type: str) -> float:
    """Calculate recommended stake based on score and bankroll"""
    MAX_STAKE_PERCENT = 0.03
    
    if score >= 7:
        stake_percent = 0.03
    elif score >= 6:
        stake_percent = 0.025
    elif score >= 5:
        stake_percent = 0.02
    elif score >= 4:
        stake_percent = 0.015
    else:
        stake_percent = 0.01
    
    stake = bankroll * stake_percent
    stake = round(stake * 2) / 2  # Round to nearest $0.50
    stake = max(stake, 2)  # Minimum $2
    stake = min(stake, bankroll * MAX_STAKE_PERCENT)  # Max 3%
    
    return stake

def generate_warnings(horses: List[Dict], bankroll: float, stop_loss: float, consecutive_losses: int) -> List[Dict]:
    """Generate warnings based on analysis"""
    warnings = []
    
    # Check if top pick has low score
    if horses:
        top_score = max(h.get("score", 0) for h in horses)
        if top_score < 4:
            warnings.append({
                "level": "HIGH",
                "message": f"⚠️ Top pick only scores {top_score}/8 - No qualifying bets for this race",
                "action": "SKIP_RACE"
            })
    
    # Check if close to stop-loss
    cushion = bankroll - stop_loss
    cushion_percent = (cushion / stop_loss) * 100 if stop_loss > 0 else 0
    
    if cushion_percent < 20:
        warnings.append({
            "level": "CRITICAL",
            "message": f"🛑 Only {cushion_percent:.0f}% above stop-loss - Extreme caution required",
            "action": "REDUCE_STAKES"
        })
    elif cushion_percent < 50:
        warnings.append({
            "level": "HIGH",
            "message": f"⚠️ {cushion_percent:.0f}% above stop-loss - Be selective with bets",
            "action": "BE_SELECTIVE"
        })
    
    # Check consecutive losses
    if consecutive_losses >= 2:
        warnings.append({
            "level": "CRITICAL",
            "message": f"🛑 STOP BETTING: {consecutive_losses} consecutive losses. Per strategy, stop for the day.",
            "action": "STOP_FOR_DAY"
        })
    elif consecutive_losses == 1:
        warnings.append({
            "level": "HIGH",
            "message": "⚠️ WARNING: 1 loss away from mandatory stop. Next bet is critical.",
            "action": "PROCEED_WITH_CAUTION"
        })
    
    return warnings

async def get_mock_race_data(track: str, race_number: int) -> List[Dict]:
    """Generate mock race data for demonstration"""
    horse_names = [
        "Thunder Bolt", "Silver Storm", "Golden Arrow", "Dark Knight",
        "Flying Spirit", "Royal Champion", "Lucky Star", "Midnight Run",
        "Fast Forward", "Wild Card", "Storm Chaser", "Iron Will"
    ]
    
    jockeys = ["J. Murphy", "T. Marquand", "W. Buick", "R. Havlin", "D. Tudhope", 
               "H. Bentley", "C. Soumillon", "F. Dettori"]
    trainers = ["J. Gosden", "C. Appleby", "A. Balding", "W. Haggas", 
                "R. Varian", "M. Johnston", "R. Hannon", "K. Ryan"]
    
    num_horses = random.randint(8, 12)
    horses = []
    
    for i in range(num_horses):
        trainer_hot = random.random() > 0.6
        jockey_hot = random.random() > 0.6
        
        horse = {
            "name": horse_names[i % len(horse_names)],
            "draw_number": i + 1,
            "jockey_name": random.choice(jockeys),
            "trainer_name": random.choice(trainers),
            "age": random.randint(3, 7),
            "weight": f"{random.randint(8, 10)}-{random.randint(0, 13)}",
            "official_rating": random.randint(60, 110),
            "form": "-".join([str(random.randint(1, 9)) for _ in range(5)]),
            "trainer_last_14_days_percent": random.randint(15, 35) if trainer_hot else random.randint(5, 18),
            "jockey_last_14_days_percent": random.randint(15, 35) if jockey_hot else random.randint(5, 18),
            "course_percent": random.randint(10, 40),
            "distance_percent": random.randint(15, 45),
            "racing_post_top3_position": random.choice([0, 0, 0, 1, 2, 3]),
            "at_the_races_top3_position": random.choice([0, 0, 0, 1, 2, 3]),
            "timeform_rating": random.randint(65, 95),
            "timeform_flags": random.sample(["!", "↑", "C", "D", "p"], random.randint(0, 2)),
            "best_win_odds": round(random.uniform(2.0, 15.0), 2),
            "best_place_odds": round(random.uniform(1.5, 5.0), 2),
            "best_win_odds_bookmaker": random.choice(["Bet365", "William Hill", "Ladbrokes", "Betfair"]),
            "best_place_odds_bookmaker": random.choice(["Bet365", "William Hill", "Ladbrokes", "Betfair"]),
            "betfair_matched_volume": random.randint(5000, 150000),
            "betfair_price_movement": random.choice(["steam", "drift", "stable", "stable"]),
            "betfair_sharp_money_indicator": random.choice(["strong", "moderate", "none", "none"]),
            "class_movement": random.choice(["dropping", "rising", None, None]),
            "first_time_blinkers": random.random() > 0.9,
            "first_time_tongue_tie": random.random() > 0.95,
            "trainer_after_break_percent": random.randint(10, 35),
            "draw_advantage": random.choice(["strong", "moderate", "none", None]),
            "pace_advantage": random.choice(["sole front-runner", "prominent", None, None])
        }
        horses.append(horse)
    
    return horses

# ==================== RACE ANALYSIS ENDPOINTS ====================

@api_router.post("/analyze")
async def analyze_race(request: RaceAnalysisRequest):
    """Analyze a race and generate betting recommendations"""
    
    settings = await ensure_default_bankroll()
    bankroll = settings.get("current_bankroll", 250.0)
    stop_loss = settings.get("stop_loss", 60.0)
    consecutive_losses = settings.get("consecutive_losses", 0)
    
    # Get mock race data
    horses = await get_mock_race_data(request.track, request.race_number)
    
    # Score all horses
    scored_horses = []
    for horse in horses:
        win_score = calculate_horse_score(horse, request.track, "WIN")
        place_score = calculate_horse_score(horse, request.track, "PLACE")
        scored_horses.append({
            **horse,
            "win_score": win_score,
            "place_score": place_score
        })
    
    # Sort by score for recommendations
    win_sorted = sorted(scored_horses, key=lambda h: h["win_score"]["score"], reverse=True)
    place_sorted = sorted(scored_horses, key=lambda h: h["place_score"]["score"], reverse=True)
    
    # Generate WIN recommendation
    top_win = win_sorted[0] if win_sorted else None
    win_recommendation = None
    if top_win:
        stake = calculate_stake(top_win["win_score"]["score"], bankroll, "WIN")
        win_recommendation = {
            "type": "WIN",
            "horse": top_win["name"],
            "draw_number": top_win["draw_number"],
            "odds": top_win["best_win_odds"],
            "bookmaker": top_win["best_win_odds_bookmaker"],
            "score": top_win["win_score"]["score"],
            "max_score": top_win["win_score"]["max_score"],
            "confidence": top_win["win_score"]["confidence_rating"],
            "star_rating": top_win["win_score"]["star_rating"],
            "stake": stake,
            "potential_return": stake * top_win["best_win_odds"],
            "potential_profit": (stake * top_win["best_win_odds"]) - stake,
            "criteria_breakdown": top_win["win_score"]["criteria_breakdown"],
            "recommendation": top_win["win_score"]["recommendation"]
        }
    
    # Generate PLACE recommendation
    top_place = place_sorted[0] if place_sorted else None
    place_recommendation = None
    if top_place:
        stake = calculate_stake(top_place["place_score"]["score"], bankroll, "PLACE")
        place_recommendation = {
            "type": "PLACE",
            "horse": top_place["name"],
            "draw_number": top_place["draw_number"],
            "odds": top_place["best_place_odds"],
            "bookmaker": top_place["best_place_odds_bookmaker"],
            "score": top_place["place_score"]["score"],
            "max_score": top_place["place_score"]["max_score"],
            "confidence": top_place["place_score"]["confidence_rating"],
            "star_rating": top_place["place_score"]["star_rating"],
            "stake": stake,
            "potential_return": stake * top_place["best_place_odds"],
            "potential_profit": (stake * top_place["best_place_odds"]) - stake,
            "criteria_breakdown": top_place["place_score"]["criteria_breakdown"],
            "recommendation": top_place["place_score"]["recommendation"]
        }
    
    # Generate TRIFECTA recommendation
    top3 = place_sorted[:3]
    trifecta_recommendation = None
    if len(top3) >= 3:
        avg_score = sum(h["place_score"]["score"] for h in top3) / 3
        trifecta_recommendation = {
            "type": "BOX_TRIFECTA",
            "horses": [
                {"position": i+1, "name": h["name"], "draw_number": h["draw_number"], 
                 "score": h["place_score"]["score"], "confidence": h["place_score"]["confidence_rating"]}
                for i, h in enumerate(top3)
            ],
            "unit_stake": 2,
            "total_combinations": 6,
            "total_stake": 12,
            "avg_score": avg_score,
            "confidence": "75-85%" if avg_score >= 6 else ("65-75%" if avg_score >= 5 else "50-65%"),
            "star_rating": 4 if avg_score >= 6 else (3 if avg_score >= 5 else 2),
            "recommendation": "Box trifecta - These 3 to finish top 3 in any order"
        }
    
    # Generate SAFETY bet recommendation
    safety_candidates = [h for h in place_sorted if h["place_score"]["score"] >= 4]
    safety_recommendation = None
    if safety_candidates:
        safety = max(safety_candidates, key=lambda h: h["best_place_odds"])
        stake = min(
            calculate_stake(safety["place_score"]["score"], bankroll, "PLACE"),
            bankroll * 0.015
        )
        safety_recommendation = {
            "type": "SAFETY_PLACE",
            "horse": safety["name"],
            "draw_number": safety["draw_number"],
            "odds": safety["best_place_odds"],
            "bookmaker": safety["best_place_odds_bookmaker"],
            "score": safety["place_score"]["score"],
            "confidence": "60-70%",
            "star_rating": 3,
            "stake": stake,
            "potential_return": stake * safety["best_place_odds"],
            "potential_profit": (stake * safety["best_place_odds"]) - stake,
            "recommendation": "Conservative PLACE bet - Lower risk option"
        }
    
    # Generate warnings
    warnings = generate_warnings(
        [{"score": h["place_score"]["score"]} for h in scored_horses],
        bankroll, stop_loss, consecutive_losses
    )
    
    return {
        "success": True,
        "race_info": {
            "track": request.track,
            "race_number": request.race_number,
            "date": request.date or datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "field_size": len(horses)
        },
        "recommendations": {
            "win": win_recommendation,
            "place": place_recommendation,
            "trifecta": trifecta_recommendation,
            "safety": safety_recommendation
        },
        "all_horses": scored_horses,
        "bankroll_status": {
            "current": bankroll,
            "stop_loss": stop_loss,
            "cushion": bankroll - stop_loss,
            "percent_above_stop_loss": ((bankroll - stop_loss) / stop_loss * 100) if stop_loss > 0 else 0
        },
        "warnings": warnings
    }

# ==================== BET MANAGEMENT ENDPOINTS ====================

@api_router.post("/bets")
async def place_bet(bet_data: BetCreate):
    """Record a new bet"""
    settings = await ensure_default_bankroll()
    
    bankroll = settings.get("current_bankroll", 0)
    stop_loss = settings.get("stop_loss", 0)
    consecutive_losses = settings.get("consecutive_losses", 0)
    
    # Validate bet
    if bankroll - bet_data.stake < stop_loss:
        raise HTTPException(status_code=400, detail="Bet would breach stop-loss")
    
    if consecutive_losses >= 2:
        raise HTTPException(status_code=400, detail="Two consecutive losses - betting stopped for today")
    
    max_stake = bankroll * settings.get("max_stake_percent", 0.03)
    if bet_data.stake > max_stake:
        raise HTTPException(status_code=400, detail=f"Stake exceeds maximum ({max_stake:.2f})")
    
    # Create bet record
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
    
    # Update bankroll
    new_bankroll = bankroll - bet_data.stake
    await db.bankroll_settings.update_one(
        {"user_id": DEFAULT_USER_ID},
        {"$set": {"current_bankroll": new_bankroll}}
    )
    
    return {
        "bet_id": bet_id,
        "message": "Bet placed successfully",
        "new_bankroll": new_bankroll
    }

@api_router.post("/bets/{bet_id}/settle")
async def settle_bet(bet_id: str, settle_data: BetSettle):
    """Settle a bet (mark as WIN or LOSS)"""
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
        message = f"✅ BET WON! +${profit_loss:.2f}. New bankroll: ${new_bankroll:.2f}"
    else:
        profit_loss = -bet["stake"]
        new_bankroll = bankroll
        consecutive_losses += 1
        must_stop = consecutive_losses >= 2
        message = f"❌ BET LOST. -${bet['stake']:.2f}. " + (
            f"{consecutive_losses} losses in a row. 🛑 STOP BETTING FOR TODAY." if must_stop 
            else f"New bankroll: ${new_bankroll:.2f}"
        )
    
    # Update bet
    await db.bets.update_one(
        {"bet_id": bet_id},
        {"$set": {"result": settle_data.result, "profit_loss": profit_loss}}
    )
    
    # Update bankroll
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
    """Get bet history"""
    bets = await db.bets.find({"user_id": DEFAULT_USER_ID}, {"_id": 0}).sort("timestamp", -1).to_list(100)
    return {"bets": bets}

@api_router.get("/statistics")
async def get_statistics():
    """Get betting statistics"""
    bets = await db.bets.find({"user_id": DEFAULT_USER_ID, "result": {"$ne": None}}, {"_id": 0}).to_list(1000)
    settings = await ensure_default_bankroll()
    
    if not bets:
        return {
            "overall": {
                "total_bets": 0,
                "wins": 0,
                "losses": 0,
                "win_rate": "0%",
                "total_staked": "0.00",
                "total_profit": "0.00",
                "roi": "0%"
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
    
    # By score level
    by_score = {}
    for score in range(3, 9):
        score_bets = [b for b in bets if b.get("score") == score]
        if score_bets:
            score_wins = len([b for b in score_bets if b.get("result") == "WIN"])
            score_staked = sum(b.get("stake", 0) for b in score_bets)
            score_profit = sum(b.get("profit_loss", 0) for b in score_bets)
            by_score[str(score)] = {
                "bets": len(score_bets),
                "wins": score_wins,
                "win_rate": f"{(score_wins / len(score_bets) * 100):.1f}%",
                "total_staked": f"{score_staked:.2f}",
                "total_profit": f"{score_profit:.2f}",
                "roi": f"{(score_profit / score_staked * 100):.1f}%" if score_staked > 0 else "0%"
            }
    
    # Recent form
    recent = sorted(bets, key=lambda b: b.get("timestamp", ""), reverse=True)[:10]
    last_10 = "".join(["W" if b.get("result") == "WIN" else "L" for b in recent])
    
    return {
        "overall": {
            "total_bets": len(bets),
            "wins": wins,
            "losses": losses,
            "win_rate": f"{win_rate:.1f}%",
            "total_staked": f"{total_staked:.2f}",
            "total_profit": f"{total_profit:.2f}",
            "roi": f"{roi:.1f}%",
            "current_bankroll": f"{settings.get('current_bankroll', 0):.2f}" if settings else "0.00",
            "starting_bankroll": f"{settings.get('starting_bankroll', 250):.2f}" if settings else "250.00"
        },
        "by_score": by_score,
        "recent_form": {
            "last_10_bets": last_10,
            "consecutive_losses": settings.get("consecutive_losses", 0) if settings else 0
        }
    }

# ==================== TRACKS ENDPOINT ====================

@api_router.get("/tracks")
async def get_tracks():
    """Get list of approved tracks"""
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

# ==================== SCRAPER STATUS ====================

@api_router.get("/scraper/status")
async def get_scraper_status():
    """Get status of scraping configuration"""
    return {
        "racing_post": {"configured": bool(os.environ.get("RACING_POST_API_KEY")), "source": "Racing Post"},
        "betfair": {"configured": bool(os.environ.get("BETFAIR_API_KEY")), "source": "Betfair Exchange"},
        "timeform": {"configured": bool(os.environ.get("TIMEFORM_API_KEY")), "source": "Timeform"},
        "at_the_races": {"configured": bool(os.environ.get("ATR_API_KEY")), "source": "At The Races"},
        "oddschecker": {"configured": bool(os.environ.get("ODDSCHECKER_API_KEY")), "source": "OddsChecker"},
        "message": "Configure API keys in environment variables to enable live data scraping"
    }

# ==================== ROOT ENDPOINT ====================

@api_router.get("/")
async def root():
    return {"message": "Horse Racing Betting Analyzer API", "status": "running"}

# Include router and add middleware
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
