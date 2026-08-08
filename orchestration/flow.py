"""
Prefect flow for the sports pipeline.

Unlike the fraud project's Airflow DAG (declarative, file-based, needs a
scheduler process running), this is a plain Python function decorated with
@flow -- Prefect handles retries, logging, and state tracking around normal
function calls. It can be run directly (`python orchestration/flow.py`),
scheduled via GitHub Actions cron (see .github/workflows/pipeline.yml), or
deployed to Prefect Cloud's free tier for a hosted schedule + run history UI.
"""

import os
import subprocess
import sys
from datetime import date, timedelta

from prefect import flow, task, get_run_logger

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "extract"))
from espn_client import fetch_games, LEAGUES  # noqa: E402
from load_to_bigquery import load as load_games  # noqa: E402

DBT_DIR = os.path.join(os.path.dirname(__file__), "..", "dbt", "sports_analytics")


@task(retries=3, retry_delay_seconds=10)
def extract_league(league: str, day: date) -> list[dict]:
    logger = get_run_logger()
    games = fetch_games(league, day)
    logger.info(f"{league} {day}: fetched {len(games)} games")
    return games


@task(retries=2, retry_delay_seconds=15)
def load_games_task(games: list[dict]) -> int:
    import json
    import tempfile

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(games, f)
        path = f.name

    return load_games(path)


@task
def run_dbt(command: str) -> None:
    logger = get_run_logger()
    result = subprocess.run(
        ["dbt", command, "--profiles-dir", "."],
        cwd=DBT_DIR, capture_output=True, text=True,
    )
    logger.info(result.stdout)
    if result.returncode != 0:
        logger.error(result.stderr)
        raise RuntimeError(f"dbt {command} failed")


@flow(name="sports-pipeline", log_prints=True)
def sports_pipeline(days_back: int = 1):
    """Pulls the last `days_back` days of NFL/NBA/MLB games and rebuilds the marts."""
    all_games = []
    for league in LEAGUES:
        for offset in range(days_back):
            day = date.today() - timedelta(days=offset)
            games = extract_league(league, day)
            all_games.extend(games)

    load_games_task(all_games)
    run_dbt("run")
    run_dbt("test")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--days-back", type=int, default=1)
    args = parser.parse_args()

    sports_pipeline(days_back=args.days_back)
