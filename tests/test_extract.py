"""
Unit tests for extract/espn_client.py.

parse_events() is a pure function (JSON in, Game list out) so we test it
directly with a fixture payload instead of hitting the real API — fast,
deterministic, and doesn't depend on ESPN being up or a real game existing
that day.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "extract"))

from espn_client import parse_events  # noqa: E402


FIXTURE_PAYLOAD = {
    "events": [
        {
            "id": "401547439",
            "date": "2026-01-15T18:00Z",
            "competitions": [
                {
                    "status": {"type": {"name": "STATUS_FINAL"}},
                    "venue": {"fullName": "Test Arena"},
                    "competitors": [
                        {"homeAway": "home", "score": "24", "team": {"displayName": "Home Team"}},
                        {"homeAway": "away", "score": "17", "team": {"displayName": "Away Team"}},
                    ],
                }
            ],
        },
        {
            # In-progress game: scores present but not final
            "id": "401547440",
            "date": "2026-01-15T21:00Z",
            "competitions": [
                {
                    "status": {"type": {"name": "STATUS_IN_PROGRESS"}},
                    "venue": {"fullName": "Test Stadium"},
                    "competitors": [
                        {"homeAway": "home", "score": "3", "team": {"displayName": "Home B"}},
                        {"homeAway": "away", "score": "0", "team": {"displayName": "Away B"}},
                    ],
                }
            ],
        },
        {
            # Not-yet-started game: no score field
            "id": "401547441",
            "date": "2026-01-16T00:00Z",
            "competitions": [
                {
                    "status": {"type": {"name": "STATUS_SCHEDULED"}},
                    "venue": {},
                    "competitors": [
                        {"homeAway": "home", "score": None, "team": {"displayName": "Home C"}},
                        {"homeAway": "away", "score": None, "team": {"displayName": "Away C"}},
                    ],
                }
            ],
        },
    ]
}


def test_parse_events_returns_one_game_per_event():
    games = parse_events(FIXTURE_PAYLOAD, league="nfl")
    assert len(games) == 3


def test_parse_events_extracts_scores_correctly():
    games = parse_events(FIXTURE_PAYLOAD, league="nfl")
    final_game = games[0]
    assert final_game.home_score == 24
    assert final_game.away_score == 17
    assert final_game.status == "STATUS_FINAL"


def test_parse_events_handles_missing_score_as_none():
    games = parse_events(FIXTURE_PAYLOAD, league="nfl")
    scheduled_game = games[2]
    assert scheduled_game.home_score is None
    assert scheduled_game.away_score is None


def test_parse_events_handles_missing_venue():
    games = parse_events(FIXTURE_PAYLOAD, league="nfl")
    scheduled_game = games[2]
    assert scheduled_game.venue is None


def test_parse_events_tags_league_correctly():
    games = parse_events(FIXTURE_PAYLOAD, league="nba")
    assert all(g.league == "nba" for g in games)


def test_parse_events_empty_payload_returns_empty_list():
    assert parse_events({"events": []}, league="mlb") == []
