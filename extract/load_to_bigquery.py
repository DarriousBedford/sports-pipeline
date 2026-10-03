"""
Loads games JSON into `raw_games` in BigQuery.

Append-only by design: every run appends rows with a `loaded_at` timestamp.
Re-fetched games (e.g. to pick up final scores) create additional rows;
dbt's stg_games model dedupes to the latest row per game_id.

(Uses a load job instead of MERGE because the BigQuery sandbox blocks DML.)
"""

import argparse
import json
import os
from datetime import datetime, timezone

from google.cloud import bigquery

PROJECT = os.environ.get("GCP_PROJECT_ID")
DATASET = os.environ.get("BQ_DATASET", "sports_analytics")
RAW_TABLE = f"{DATASET}.raw_games"


def load(json_path: str) -> int:
    client = bigquery.Client(project=PROJECT)

    with open(json_path) as f:
        rows = json.load(f)

    if not rows:
        print("No rows to load.")
        return 0

    # Stamp each row (MERGE used to do this with CURRENT_TIMESTAMP()).
    loaded_at = datetime.now(timezone.utc).isoformat()
    for row in rows:
        row["loaded_at"] = loaded_at

    # Explicit schema: game_id looks numeric, so autodetect would wrongly infer INT64.
    job_config = bigquery.LoadJobConfig(
        write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
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
            bigquery.SchemaField("loaded_at", "TIMESTAMP"),
        ],
    )
    load_job = client.load_table_from_json(
        rows, f"{PROJECT}.{RAW_TABLE}", job_config=job_config,
    )
    load_job.result()

    print(f"Appended {len(rows)} rows to {RAW_TABLE}")
    return len(rows)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", type=str, default="/tmp/games.json")
    args = parser.parse_args()
    load(args.json)