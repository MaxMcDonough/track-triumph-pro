"""
The Racing API Integration Module
https://api.theracingapi.com/documentation
"""
import os
import httpx
from datetime import datetime, timezone
from typing import Optional, Dict, List
import logging
import base64

logger = logging.getLogger(__name__)

class TheRacingAPI:
    """Client for The Racing API (theracingapi.com)"""
    
    BASE_URL = "https://api.theracingapi.com/v1"
    
    def __init__(self):
        self.username = os.environ.get("RACING_API_USERNAME")
        self.password = os.environ.get("RACING_API_PASSWORD")
        
        if not self.username or not self.password:
            logger.warning("Racing API credentials not configured")
            self.configured = False
        else:
            self.configured = True
            # Create Basic Auth header
            credentials = f"{self.username}:{self.password}"
            encoded = base64.b64encode(credentials.encode()).decode()
            self.auth_header = f"Basic {encoded}"
    
    def _get_headers(self) -> Dict:
        """Get request headers with authentication"""
        return {
            "Authorization": self.auth_header,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    
    async def get_todays_racecards(self, region: str = "gb") -> Dict:
        """
        Get today's racecards
        region: gb (UK), ire (Ireland), usa, aus, etc.
        """
        if not self.configured:
            return {"error": "API not configured", "configured": False}
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.BASE_URL}/racecards",
                    headers=self._get_headers(),
                    params={"region": region}
                )
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 401:
                    return {"error": "Authentication failed - check API credentials"}
                else:
                    return {"error": f"API error: {response.status_code}", "detail": response.text}
                    
        except Exception as e:
            logger.error(f"Racing API error: {e}")
            return {"error": str(e)}
    
    async def get_racecard_by_course(self, course: str, date: Optional[str] = None) -> Dict:
        """
        Get racecard for a specific course
        course: Course name (e.g., 'wolverhampton', 'chelmsford')
        date: Date in YYYY-MM-DD format (default: today)
        """
        if not self.configured:
            return {"error": "API not configured", "configured": False}
        
        if not date:
            date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # First get today's racecards
                response = await client.get(
                    f"{self.BASE_URL}/racecards",
                    headers=self._get_headers(),
                    params={"date": date}
                )
                
                if response.status_code != 200:
                    return {"error": f"API error: {response.status_code}"}
                
                data = response.json()
                
                # Filter by course
                racecards = data.get("racecards", [])
                course_racecards = [
                    rc for rc in racecards 
                    if course.lower() in rc.get("course", "").lower()
                ]
                
                return {
                    "success": True,
                    "course": course,
                    "date": date,
                    "racecards": course_racecards
                }
                
        except Exception as e:
            logger.error(f"Racing API error: {e}")
            return {"error": str(e)}
    
    async def get_race_detail(self, race_id: str) -> Dict:
        """
        Get detailed information for a specific race
        race_id: The race ID from the racecard
        """
        if not self.configured:
            return {"error": "API not configured", "configured": False}
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.BASE_URL}/racecards/{race_id}",
                    headers=self._get_headers()
                )
                
                if response.status_code == 200:
                    return {"success": True, "data": response.json()}
                else:
                    return {"error": f"API error: {response.status_code}"}
                    
        except Exception as e:
            logger.error(f"Racing API error: {e}")
            return {"error": str(e)}
    
    async def get_runners(self, race_id: str) -> Dict:
        """
        Get runners/horses for a specific race with detailed stats
        """
        if not self.configured:
            return {"error": "API not configured", "configured": False}
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.BASE_URL}/racecards/{race_id}/runners",
                    headers=self._get_headers()
                )
                
                if response.status_code == 200:
                    return {"success": True, "runners": response.json()}
                else:
                    return {"error": f"API error: {response.status_code}"}
                    
        except Exception as e:
            logger.error(f"Racing API error: {e}")
            return {"error": str(e)}
    
    async def get_horse_form(self, horse_id: str) -> Dict:
        """
        Get historical form/results for a specific horse
        """
        if not self.configured:
            return {"error": "API not configured", "configured": False}
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.BASE_URL}/horses/{horse_id}/results",
                    headers=self._get_headers()
                )
                
                if response.status_code == 200:
                    return {"success": True, "form": response.json()}
                else:
                    return {"error": f"API error: {response.status_code}"}
                    
        except Exception as e:
            logger.error(f"Racing API error: {e}")
            return {"error": str(e)}
    
    async def get_jockey_stats(self, jockey_id: str, days: int = 14) -> Dict:
        """
        Get jockey statistics for recent period
        """
        if not self.configured:
            return {"error": "API not configured", "configured": False}
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.BASE_URL}/jockeys/{jockey_id}/results",
                    headers=self._get_headers(),
                    params={"period": f"{days}d"}
                )
                
                if response.status_code == 200:
                    results = response.json()
                    # Calculate win percentage
                    total = len(results.get("results", []))
                    wins = len([r for r in results.get("results", []) if r.get("position") == "1"])
                    win_percent = (wins / total * 100) if total > 0 else 0
                    
                    return {
                        "success": True,
                        "jockey_id": jockey_id,
                        "period_days": days,
                        "total_rides": total,
                        "wins": wins,
                        "win_percent": round(win_percent, 1)
                    }
                else:
                    return {"error": f"API error: {response.status_code}"}
                    
        except Exception as e:
            logger.error(f"Racing API error: {e}")
            return {"error": str(e)}
    
    async def get_trainer_stats(self, trainer_id: str, days: int = 14) -> Dict:
        """
        Get trainer statistics for recent period
        """
        if not self.configured:
            return {"error": "API not configured", "configured": False}
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.BASE_URL}/trainers/{trainer_id}/results",
                    headers=self._get_headers(),
                    params={"period": f"{days}d"}
                )
                
                if response.status_code == 200:
                    results = response.json()
                    # Calculate win percentage
                    total = len(results.get("results", []))
                    wins = len([r for r in results.get("results", []) if r.get("position") == "1"])
                    win_percent = (wins / total * 100) if total > 0 else 0
                    
                    return {
                        "success": True,
                        "trainer_id": trainer_id,
                        "period_days": days,
                        "total_runners": total,
                        "wins": wins,
                        "win_percent": round(win_percent, 1)
                    }
                else:
                    return {"error": f"API error: {response.status_code}"}
                    
        except Exception as e:
            logger.error(f"Racing API error: {e}")
            return {"error": str(e)}
    
    async def get_odds(self, race_id: str) -> Dict:
        """
        Get current odds for a race
        """
        if not self.configured:
            return {"error": "API not configured", "configured": False}
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.BASE_URL}/racecards/{race_id}/odds",
                    headers=self._get_headers()
                )
                
                if response.status_code == 200:
                    return {"success": True, "odds": response.json()}
                else:
                    return {"error": f"API error: {response.status_code}"}
                    
        except Exception as e:
            logger.error(f"Racing API error: {e}")
            return {"error": str(e)}

    def transform_runner_to_horse_data(self, runner: Dict, race_info: Dict) -> Dict:
        """
        Transform API runner data to our horse data format for scoring
        """
        # Parse odds from fractional to decimal
        odds_str = runner.get("odds", "5/1")
        try:
            if "/" in str(odds_str):
                num, den = odds_str.split("/")
                decimal_odds = (float(num) / float(den)) + 1
            else:
                decimal_odds = float(odds_str)
        except:
            decimal_odds = 5.0
        
        return {
            "name": runner.get("horse", "Unknown"),
            "draw_number": int(runner.get("draw", runner.get("number", 0))),
            "jockey_name": runner.get("jockey", ""),
            "trainer_name": runner.get("trainer", ""),
            "age": int(runner.get("age", 0)),
            "weight": runner.get("weight", runner.get("lbs", "")),
            "official_rating": int(runner.get("or", 0)) if runner.get("or") else None,
            "form": runner.get("form", ""),
            "horse_id": runner.get("horse_id"),
            "jockey_id": runner.get("jockey_id"),
            "trainer_id": runner.get("trainer_id"),
            
            # These will be populated from additional API calls
            "trainer_last_14_days_percent": None,
            "jockey_last_14_days_percent": None,
            "course_percent": None,
            "distance_percent": None,
            "racing_post_top3_position": None,
            "at_the_races_top3_position": None,
            "timeform_rating": None,
            "timeform_flags": [],
            
            # Odds
            "best_win_odds": decimal_odds,
            "best_place_odds": decimal_odds / 4 + 1,  # Approximate place odds
            "best_win_odds_bookmaker": "The Racing API",
            "best_place_odds_bookmaker": "The Racing API",
            
            # Market data (placeholder - needs separate API)
            "betfair_matched_volume": 0,
            "betfair_price_movement": "stable",
            "betfair_sharp_money_indicator": "none",
            
            # Angles
            "class_movement": None,
            "first_time_blinkers": runner.get("headgear", "").lower().startswith("first"),
            "first_time_tongue_tie": False,
            "trainer_after_break_percent": None,
            "draw_advantage": None,
            "pace_advantage": None
        }


# Singleton instance
racing_api = TheRacingAPI()
