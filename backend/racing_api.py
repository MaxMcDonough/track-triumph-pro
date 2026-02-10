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
            logger.info(f"Racing API configured with username: {self.username[:8]}...")
    
    def _get_auth(self):
        """Get HTTP Basic Auth tuple"""
        return (self.username, self.password)
    
    async def get_racecards_free(self, date: Optional[str] = None) -> Dict:
        """
        Get today's free racecards (available on all plans)
        """
        if not self.configured:
            return {"error": "API not configured", "configured": False}
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                params = {}
                if date:
                    params["date"] = date
                
                response = await client.get(
                    f"{self.BASE_URL}/racecards/free",
                    auth=self._get_auth(),
                    params=params
                )
                
                logger.info(f"Racecards API response status: {response.status_code}")
                
                if response.status_code == 200:
                    return {"success": True, "data": response.json()}
                elif response.status_code == 401:
                    return {"error": "Authentication failed - check API credentials", "status": 401}
                else:
                    return {"error": f"API error: {response.status_code}", "detail": response.text}
                    
        except Exception as e:
            logger.error(f"Racing API error: {e}")
            return {"error": str(e)}
    
    async def get_racecards_basic(self, date: Optional[str] = None) -> Dict:
        """
        Get racecards with basic data (requires Basic+ plan)
        """
        if not self.configured:
            return {"error": "API not configured", "configured": False}
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                params = {}
                if date:
                    params["date"] = date
                
                response = await client.get(
                    f"{self.BASE_URL}/racecards/basic",
                    auth=self._get_auth(),
                    params=params
                )
                
                if response.status_code == 200:
                    return {"success": True, "data": response.json()}
                elif response.status_code == 401:
                    return {"error": "Authentication failed or insufficient plan", "status": 401}
                else:
                    return {"error": f"API error: {response.status_code}", "detail": response.text}
                    
        except Exception as e:
            logger.error(f"Racing API error: {e}")
            return {"error": str(e)}
    
    async def get_racecards_standard(self, date: Optional[str] = None) -> Dict:
        """
        Get racecards with standard data (requires Standard+ plan)
        """
        if not self.configured:
            return {"error": "API not configured", "configured": False}
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                params = {}
                if date:
                    params["date"] = date
                
                response = await client.get(
                    f"{self.BASE_URL}/racecards/standard",
                    auth=self._get_auth(),
                    params=params
                )
                
                if response.status_code == 200:
                    return {"success": True, "data": response.json()}
                elif response.status_code == 401:
                    return {"error": "Authentication failed or insufficient plan", "status": 401}
                else:
                    return {"error": f"API error: {response.status_code}", "detail": response.text}
                    
        except Exception as e:
            logger.error(f"Racing API error: {e}")
            return {"error": str(e)}

    async def get_courses(self, region_codes: Optional[List[str]] = None) -> Dict:
        """
        Get list of courses (free endpoint)
        """
        if not self.configured:
            return {"error": "API not configured", "configured": False}
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                params = {}
                if region_codes:
                    params["region_codes"] = region_codes
                
                response = await client.get(
                    f"{self.BASE_URL}/courses",
                    auth=self._get_auth(),
                    params=params
                )
                
                if response.status_code == 200:
                    return {"success": True, "data": response.json()}
                else:
                    return {"error": f"API error: {response.status_code}"}
                    
        except Exception as e:
            logger.error(f"Racing API error: {e}")
            return {"error": str(e)}

    async def get_regions(self) -> Dict:
        """
        Get list of regions (free endpoint)
        """
        if not self.configured:
            return {"error": "API not configured", "configured": False}
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.BASE_URL}/courses/regions",
                    auth=self._get_auth()
                )
                
                if response.status_code == 200:
                    return {"success": True, "data": response.json()}
                else:
                    return {"error": f"API error: {response.status_code}"}
                    
        except Exception as e:
            logger.error(f"Racing API error: {e}")
            return {"error": str(e)}

    async def get_results_today_free(self) -> Dict:
        """
        Get today's results (free endpoint)
        """
        if not self.configured:
            return {"error": "API not configured", "configured": False}
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.BASE_URL}/results/today-free",
                    auth=self._get_auth()
                )
                
                if response.status_code == 200:
                    return {"success": True, "data": response.json()}
                else:
                    return {"error": f"API error: {response.status_code}"}
                    
        except Exception as e:
            logger.error(f"Racing API error: {e}")
            return {"error": str(e)}

    async def search_horse(self, name: str) -> Dict:
        """
        Search for a horse by name (requires Standard+ plan)
        """
        if not self.configured:
            return {"error": "API not configured", "configured": False}
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.BASE_URL}/horses/search",
                    auth=self._get_auth(),
                    params={"name": name}
                )
                
                if response.status_code == 200:
                    return {"success": True, "data": response.json()}
                else:
                    return {"error": f"API error: {response.status_code}"}
                    
        except Exception as e:
            logger.error(f"Racing API error: {e}")
            return {"error": str(e)}

    async def search_trainer(self, name: str) -> Dict:
        """
        Search for a trainer by name (requires Standard+ plan)
        """
        if not self.configured:
            return {"error": "API not configured", "configured": False}
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.BASE_URL}/trainers/search",
                    auth=self._get_auth(),
                    params={"name": name}
                )
                
                if response.status_code == 200:
                    return {"success": True, "data": response.json()}
                else:
                    return {"error": f"API error: {response.status_code}"}
                    
        except Exception as e:
            logger.error(f"Racing API error: {e}")
            return {"error": str(e)}

    async def search_jockey(self, name: str) -> Dict:
        """
        Search for a jockey by name (requires Standard+ plan)
        """
        if not self.configured:
            return {"error": "API not configured", "configured": False}
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.BASE_URL}/jockeys/search",
                    auth=self._get_auth(),
                    params={"name": name}
                )
                
                if response.status_code == 200:
                    return {"success": True, "data": response.json()}
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
