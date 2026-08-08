"""
Loads games JSON into `raw.games` in BigQuery.

Idempotent by design: loads into a staging table then MERGEs into the raw
table on game_id, so re-running for the same date range (e.g. a retried
Actions run) never creates duplicates -- important since games can also be
re-fetched to pick up final scores after a game finishes.
"""

import argparse
import json
import os

from google.cloud import bigquery

PROJECT = os.environ.get("GCP_PROJECT_ID")
DATASET = os.environ.get("BQ_DATASET", "sports_analytics")
RAW_TABLE = f"{DATASET}.raw_games"
STAGING_TABLE = f"{DATASET}.raw_games_staging"

MERGE_SQL = f"""
MERGE `{PROJECT}.{RAW_TABLE}` T
USING `{PROJECT}.{STAGING_TABLE}` S
ON T.game_id = S.game_id
WHEN MATCHED THEN
  UPDATE SET
    status = S.status,
    home_score = S.home_score,
    away_score = S.away_score,
    loaded_at = CURRENT_TIMESTAMP()
WHEN NOT MATCHED THEN
  INSERT (game_id, league, game_date, status, home_team, home_score,
          away_team, away_score, venue, loaded_at)
  VALUES (S.game_id, S.league, S.game_date, S.status, S.home_team, S.home_score,
          S.away_team, S.away_score, S.venue, CURRENT_TIMESTAMP())
"""


def load(json_path: str) -> int:
    client = bigquery.Client(project=PROJECT)

    with open(json_path) as f:
        rows = json.load(f)

    if not rows:
        print("No rows to load.")
        return 0

    # Load into a fresh staging table (truncate-and-replace each run).
    # Schema is spelled out explicitly rather than using autodetect=True --
    # game_id values look like pure numbers (e.g. "401816352"), so
    # autodetect infers INT64 instead of STRING, which then breaks the
    # MERGE below when comparing against raw_games' STRING game_id column.
    job_config = bigquery.LoadJobConfig(
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
        schema=[
            bigquery.SchemaField("game_id", "STRING"),
            bigquery.SchemaField("league", "STRING"),
            bigquery.SchemaField("game_date", "STRING"),
            bigquery.SchemaField("status", "STRING"),
            bigquery.SchemaField("home_team", "STRING"),
            bigquery.SchemaField("home_score", "INT64"),
            bigquery.SchemaField("away_team", "STRING"),
            bigquery.SchemaField("away_score", "INT64"),
            bigquery.SchemaField("venue", "STRING"),
        ],
    )
    load_job = client.load_table_from_json(
        rows, f"{PROJECT}.{STAGING_TABLE}", job_config=job_config,
    )
    load_job.result()

    # Merge staging -> raw so re-runs update scores instead of duplicating rows.
    client.query(MERGE_SQL).result()

    print(f"Merged {len(rows)} rows into {RAW_TABLE}")
    return len(rows)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", type=str, default="/tmp/games.json")
    args = parser.parse_args()
    load(args.json)
