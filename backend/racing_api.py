"""
The Racing API Integration Module
https://api.theracingapi.com/v1
"""
import os
import httpx
from typing import Optional, Dict, List
import logging
import re

logger = logging.getLogger(__name__)


class TheRacingAPI:
    BASE_URL = "https://api.theracingapi.com/v1"

    def __init__(self):
        self.username = os.environ.get("RACING_API_USERNAME")
        self.password = os.environ.get("RACING_API_PASSWORD")
        self.configured = bool(self.username and self.password)
        if self.configured:
            logger.info("Racing API configured")

    def _auth(self):
        return (self.username, self.password)

    async def _get(self, path: str, params: Optional[Dict] = None) -> Dict:
        if not self.configured:
            return {"error": "API not configured", "configured": False}
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.BASE_URL}{path}",
                    auth=self._auth(),
                    params=params or {},
                )
                if response.status_code == 200:
                    return {"success": True, "data": response.json()}
                elif response.status_code == 401:
                    return {"error": "Authentication failed", "status": 401}
                else:
                    return {"error": f"API error: {response.status_code}", "detail": response.text}
        except Exception as e:
            logger.error(f"Racing API error: {e}")
            return {"error": str(e)}

    async def get_racecards_free(self, date: Optional[str] = None) -> Dict:
        params = {}
        if date:
            params["date"] = date
        return await self._get("/racecards/free", params)

    async def get_courses(self, region_codes: Optional[str] = None) -> Dict:
        params = {}
        if region_codes:
            params["region_codes"] = region_codes
        return await self._get("/courses", params)

    async def get_regions(self) -> Dict:
        return await self._get("/courses/regions")

    async def get_results_today(self) -> Dict:
        return await self._get("/results/today-free")

    def parse_form(self, form_str: str) -> Dict:
        """Parse form string like '6P84U4' into useful metrics."""
        if not form_str:
            return {"runs": 0, "wins": 0, "places": 0, "win_rate": 0, "place_rate": 0, "recent_trend": "unknown"}

        runs = []
        for ch in form_str:
            if ch.isdigit():
                runs.append(int(ch))
            elif ch in ('P', 'p'):
                runs.append(0)  # pulled up
            elif ch in ('F', 'f'):
                runs.append(0)  # fell
            elif ch in ('U', 'u'):
                runs.append(0)  # unseated
            elif ch == '-':
                continue

        total = len(runs) if runs else 1
        wins = sum(1 for r in runs if r == 1)
        places = sum(1 for r in runs if 1 <= r <= 3)

        # Recent trend (last 3 runs)
        recent = runs[-3:] if len(runs) >= 3 else runs
        if recent:
            avg_recent = sum(recent) / len(recent)
            older = runs[:-3] if len(runs) > 3 else []
            avg_older = sum(older) / len(older) if older else avg_recent
            if avg_recent < avg_older:
                trend = "improving"
            elif avg_recent > avg_older:
                trend = "declining"
            else:
                trend = "stable"
        else:
            trend = "unknown"

        return {
            "runs": total,
            "wins": wins,
            "places": places,
            "win_rate": round((wins / total) * 100, 1) if total else 0,
            "place_rate": round((places / total) * 100, 1) if total else 0,
            "recent_trend": trend,
            "last_position": runs[-1] if runs else None,
        }

    def transform_racecard(self, racecard: Dict) -> Dict:
        """Transform API racecard into our app format."""
        runners = []
        for r in racecard.get("runners", []):
            form_analysis = self.parse_form(r.get("form", ""))

            try:
                ofr = int(r.get("ofr", 0) or 0)
            except (ValueError, TypeError):
                ofr = 0
            try:
                lbs = int(r.get("lbs", 0) or 0)
            except (ValueError, TypeError):
                lbs = 0
            try:
                last_run = int(r.get("last_run", 0) or 0)
            except (ValueError, TypeError):
                last_run = 0

            # Skip non-runners
            num_str = str(r.get("number", "0") or "0")
            if num_str.upper() == "NR":
                continue

            try:
                draw = int(r.get("draw", 0) or 0)
            except (ValueError, TypeError):
                draw = 0
            try:
                number = int(num_str)
            except (ValueError, TypeError):
                number = 0

            runners.append({
                "name": r.get("horse", "Unknown"),
                "horse_id": r.get("horse_id", ""),
                "age": r.get("age", ""),
                "sex": r.get("sex", ""),
                "draw_number": draw,
                "number": number,
                "jockey_name": r.get("jockey", ""),
                "jockey_id": r.get("jockey_id", ""),
                "trainer_name": r.get("trainer", ""),
                "trainer_id": r.get("trainer_id", ""),
                "weight_lbs": int(r.get("lbs", 0) or 0),
                "official_rating": ofr,
                "headgear": r.get("headgear", ""),
                "form": r.get("form", ""),
                "form_analysis": form_analysis,
                "last_run_days": int(r.get("last_run", 0) or 0),
                "sire": r.get("sire", ""),
                "dam": r.get("dam", ""),
                "owner": r.get("owner", ""),
            })

        return {
            "race_id": racecard.get("race_id", ""),
            "course": racecard.get("course", ""),
            "date": racecard.get("date", ""),
            "off_time": racecard.get("off_time", ""),
            "off_dt": racecard.get("off_dt", ""),
            "race_name": racecard.get("race_name", ""),
            "distance": racecard.get("distance_f", ""),
            "region": racecard.get("region", ""),
            "race_class": racecard.get("race_class", ""),
            "race_type": racecard.get("type", ""),
            "age_band": racecard.get("age_band", ""),
            "prize": racecard.get("prize", ""),
            "field_size": int(racecard.get("field_size", 0) or 0),
            "going": racecard.get("going", ""),
            "surface": racecard.get("surface", ""),
            "race_status": racecard.get("race_status", ""),
            "runners": runners,
        }


racing_api = TheRacingAPI()
