"""
Runs the extract step across all three leagues for a given date range and
writes the combined result to a JSON file for the loader to pick up.

Usage:
    python extract/run_extract.py --start 2026-08-01 --end 2026-08-07 --out /tmp/games.json
"""

import argparse
import json
import os
import sys
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from espn_client import fetch_games, LEAGUES


def daterange(start: date, end: date):
    for n in range((end - start).days + 1):
        yield start + timedelta(days=n)


def run(start: date, end: date, out_path: str) -> int:
    all_games = []
    for league in LEAGUES:
        for day in daterange(start, end):
            games = fetch_games(league, day)
            all_games.extend(games)
            print(f"{league} {day}: {len(games)} games")

    with open(out_path, "w") as f:
        json.dump(all_games, f)

    print(f"Wrote {len(all_games)} total games to {out_path}")
    return len(all_games)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", type=str, required=True, help="YYYY-MM-DD")
    parser.add_argument("--end", type=str, required=True, help="YYYY-MM-DD")
    parser.add_argument("--out", type=str, default="/tmp/games.json")
    args = parser.parse_args()

    start = date.fromisoformat(args.start)
    end = date.fromisoformat(args.end)
    run(start, end, args.out)
