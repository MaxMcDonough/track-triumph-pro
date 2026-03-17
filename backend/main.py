"""
Track Triumph Pro — Backend API
Proxies The Racing API with caching, serves live horse racing data.
"""
import os
import time
import json
from datetime import datetime, date
from typing import Optional
from functools import lru_cache

import httpx
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# ── Config ──────────────────────────────────────────────────────────
RACING_API_BASE = "https://api.theracingapi.com/v1"
RACING_API_USER = os.getenv("RACING_API_USER", "")
RACING_API_PASS = os.getenv("RACING_API_PASS", "")

app = FastAPI(title="Track Triumph Pro API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Simple in-memory cache ──────────────────────────────────────────
_cache: dict[str, tuple[float, any]] = {}
CACHE_TTL = 180  # 3 minutes


def get_cache(key: str):
    if key in _cache:
        ts, data = _cache[key]
        if time.time() - ts < CACHE_TTL:
            return data
        del _cache[key]
    return None


def set_cache(key: str, data):
    _cache[key] = (time.time(), data)


# ── Racing API client ───────────────────────────────────────────────
async def racing_api_get(path: str, params: dict = None) -> dict:
    """Make authenticated GET request to The Racing API."""
    if not RACING_API_USER or not RACING_API_PASS:
        raise HTTPException(
            status_code=503,
            detail="Racing API credentials not configured. Set RACING_API_USER and RACING_API_PASS env vars."
        )

    cache_key = f"{path}:{json.dumps(params or {}, sort_keys=True)}"
    cached = get_cache(cache_key)
    if cached is not None:
        return cached

    url = f"{RACING_API_BASE}{path}"
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            resp = await client.get(
                url,
                params=params,
                auth=(RACING_API_USER, RACING_API_PASS),
            )
            resp.raise_for_status()
            data = resp.json()
            set_cache(cache_key, data)
            return data
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail=str(e))
        except httpx.RequestError as e:
            raise HTTPException(status_code=502, detail=f"Racing API connection error: {str(e)}")


# ── Health ──────────────────────────────────────────────────────────
@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "api_configured": bool(RACING_API_USER and RACING_API_PASS),
        "timestamp": datetime.utcnow().isoformat(),
    }


# ── Regions & Courses ──────────────────────────────────────────────
@app.get("/api/regions")
async def get_regions():
    """Get list of racing regions."""
    return await racing_api_get("/courses/regions")


@app.get("/api/courses")
async def get_courses(region_codes: Optional[str] = Query(None, description="Comma-separated region codes e.g. gb,ire,usa")):
    """Get list of courses/tracks, optionally filtered by region."""
    params = {}
    if region_codes:
        params["region_codes"] = region_codes
    return await racing_api_get("/courses", params)


# ── Racecards (Today's Races) ─────────────────────────────────────
@app.get("/api/racecards")
async def get_racecards(
    region_codes: Optional[str] = Query(None),
    date: Optional[str] = Query(None, description="Date YYYY-MM-DD"),
):
    """Get today's racecards with runners, odds, and race details."""
    params = {}
    if region_codes:
        params["region_codes"] = region_codes
    if date:
        params["date"] = date
    return await racing_api_get("/racecards", params)


@app.get("/api/racecards/{racecard_id}")
async def get_racecard_detail(racecard_id: str):
    """Get detailed racecard for a specific race."""
    return await racing_api_get(f"/racecards/{racecard_id}")


# ── Results ────────────────────────────────────────────────────────
@app.get("/api/results")
async def get_results(
    region_codes: Optional[str] = Query(None),
    date: Optional[str] = Query(None),
):
    """Get race results."""
    params = {}
    if region_codes:
        params["region_codes"] = region_codes
    if date:
        params["date"] = date
    return await racing_api_get("/results", params)


@app.get("/api/results/{result_id}")
async def get_result_detail(result_id: str):
    """Get detailed result for a specific race."""
    return await racing_api_get(f"/results/{result_id}")


# ── Horses ─────────────────────────────────────────────────────────
@app.get("/api/horses/search")
async def search_horses(name: str = Query(..., min_length=2)):
    """Search horses by name."""
    return await racing_api_get("/horses/search", {"name": name})


@app.get("/api/horses/{horse_id}/results")
async def get_horse_results(horse_id: str):
    """Get full result history for a horse."""
    return await racing_api_get(f"/horses/{horse_id}/results")


# ── Jockeys ────────────────────────────────────────────────────────
@app.get("/api/jockeys/search")
async def search_jockeys(name: str = Query(..., min_length=2)):
    """Search jockeys by name."""
    return await racing_api_get("/jockeys/search", {"name": name})


@app.get("/api/jockeys/{jockey_id}/results")
async def get_jockey_results(jockey_id: str):
    """Get result history for a jockey."""
    return await racing_api_get(f"/jockeys/{jockey_id}/results")


@app.get("/api/jockeys/{jockey_id}/analysis/classes")
async def get_jockey_class_analysis(jockey_id: str):
    """Get jockey stats by race class."""
    return await racing_api_get(f"/jockeys/{jockey_id}/analysis/classes")


@app.get("/api/jockeys/{jockey_id}/analysis/distances")
async def get_jockey_distance_analysis(jockey_id: str):
    """Get jockey stats by distance."""
    return await racing_api_get(f"/jockeys/{jockey_id}/analysis/distances")


# ── Trainers ───────────────────────────────────────────────────────
@app.get("/api/trainers/search")
async def search_trainers(name: str = Query(..., min_length=2)):
    """Search trainers by name."""
    return await racing_api_get("/trainers/search", {"name": name})


@app.get("/api/trainers/{trainer_id}/results")
async def get_trainer_results(trainer_id: str):
    """Get result history for a trainer."""
    return await racing_api_get(f"/trainers/{trainer_id}/results")


@app.get("/api/trainers/{trainer_id}/analysis/classes")
async def get_trainer_class_analysis(trainer_id: str):
    """Get trainer stats by race class."""
    return await racing_api_get(f"/trainers/{trainer_id}/analysis/classes")


# ── Owners ─────────────────────────────────────────────────────────
@app.get("/api/owners/search")
async def search_owners(name: str = Query(..., min_length=2)):
    """Search owners by name."""
    return await racing_api_get("/owners/search", {"name": name})


# ── Sires ──────────────────────────────────────────────────────────
@app.get("/api/sires/search")
async def search_sires(name: str = Query(..., min_length=2)):
    """Search sires by name."""
    return await racing_api_get("/sires/search", {"name": name})


@app.get("/api/sires/{sire_id}/analysis/distances")
async def get_sire_distance_analysis(sire_id: str):
    """Get sire progeny stats by distance."""
    return await racing_api_get(f"/sires/{sire_id}/analysis/distances")


# ── Dams ───────────────────────────────────────────────────────────
@app.get("/api/dams/search")
async def search_dams(name: str = Query(..., min_length=2)):
    """Search dams by name."""
    return await racing_api_get("/dams/search", {"name": name})


# ── Stats Aggregation (computed from API data) ─────────────────────
@app.get("/api/dashboard/stats")
async def get_dashboard_stats():
    """Get aggregated dashboard statistics from today's racing data."""
    try:
        racecards = await racing_api_get("/racecards")
        results = await racing_api_get("/results")

        races_today = len(racecards) if isinstance(racecards, list) else 0
        results_today = len(results) if isinstance(results, list) else 0

        total_runners = 0
        if isinstance(racecards, list):
            for rc in racecards:
                runners = rc.get("runners", [])
                total_runners += len(runners)

        return {
            "races_today": races_today,
            "results_available": results_today,
            "total_runners": total_runners,
            "data_freshness": "live",
            "last_updated": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        return {
            "races_today": 0,
            "results_available": 0,
            "total_runners": 0,
            "data_freshness": "offline",
            "error": str(e),
            "last_updated": datetime.utcnow().isoformat(),
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
