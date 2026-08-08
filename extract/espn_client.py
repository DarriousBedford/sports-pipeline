"""
Thin client around ESPN's public (undocumented, but widely used and stable)
scoreboard API. No API key required.

Endpoint shape:
    https://site.api.espn.com/apis/site/v2/sports/{sport}/{league}/scoreboard?dates=YYYYMMDD

We keep this module pure request/parse logic with no I/O side effects beyond
the HTTP call, so it's easy to unit test with mocked responses (see
tests/test_extract.py).
"""

from __future__ import annotations

import time
from dataclasses import dataclass, asdict
from datetime import date

import requests

BASE_URL = "https://site.api.espn.com/apis/site/v2/sports"

# (sport, league) as ESPN's API expects them in the URL path
LEAGUES = {
    "nfl": ("football", "nfl"),
    "nba": ("basketball", "nba"),
    "mlb": ("baseball", "mlb"),
}


@dataclass
class Game:
    game_id: str
    league: str
    game_date: str
    status: str
    home_team: str
    home_score: int | None
    away_team: str
    away_score: int | None
    venue: str | None


def _fetch_scoreboard(league: str, game_date: date, session: requests.Session, retries: int = 3) -> dict:
    sport, league_path = LEAGUES[league]
    url = f"{BASE_URL}/{sport}/{league_path}/scoreboard"
    params = {"dates": game_date.strftime("%Y%m%d")}

    last_err = None
    for attempt in range(retries):
        try:
            resp = session.get(url, params=params, timeout=10)
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as e:
            last_err = e
            time.sleep(2 ** attempt)  # exponential backoff
    raise RuntimeError(f"Failed to fetch {league} scoreboard for {game_date}: {last_err}")


def parse_events(payload: dict, league: str) -> list[Game]:
    """Pure function: ESPN JSON -> list of Game records. No network calls."""
    games = []
    for event in payload.get("events", []):
        competition = event["competitions"][0]
        competitors = competition["competitors"]
        home = next(c for c in competitors if c["homeAway"] == "home")
        away = next(c for c in competitors if c["homeAway"] == "away")

        games.append(Game(
            game_id=event["id"],
            league=league,
            game_date=event["date"],
            status=competition["status"]["type"]["name"],
            home_team=home["team"]["displayName"],
            home_score=int(home["score"]) if home.get("score") not in (None, "") else None,
            away_team=away["team"]["displayName"],
            away_score=int(away["score"]) if away.get("score") not in (None, "") else None,
            venue=competition.get("venue", {}).get("fullName"),
        ))
    return games


def fetch_games(league: str, game_date: date, session: requests.Session | None = None) -> list[dict]:
    """Fetch + parse in one call. Returns a list of plain dicts ready to load."""
    session = session or requests.Session()
    payload = _fetch_scoreboard(league, game_date, session)
    return [asdict(g) for g in parse_events(payload, league)]
