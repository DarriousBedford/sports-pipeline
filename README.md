# NFL / NBA / MLB Sports ETL Pipeline

An end-to-end batch pipeline that pulls real NFL, NBA, and MLB game data
from ESPN's public API, loads it into **BigQuery**, transforms it with
**dbt**, and is orchestrated with **Prefect** — validated with both dbt
data-quality tests and a pytest unit-test suite for the extraction logic.

```
extract (ESPN API)  →  load (BigQuery, MERGE)  →  dbt run  →  dbt test
        │                                              │
        └──────────────── orchestrated by Prefect ─────┘
```

## Why this project

Companion piece to a Snowflake/dbt/GitHub-Actions fraud analytics
pipeline, built to show range rather than repeat the same stack: a
different warehouse (BigQuery instead of Snowflake), a different
orchestration paradigm (Prefect's Python-native flows instead of
GitHub-Actions-as-scheduler), a real external API instead of synthetic
data, and deeper transformation logic — window functions for rolling
scoring trends, an idempotent MERGE-based load, and a pytest suite
alongside the dbt tests.

## Stack

- **Python** — ESPN API extraction (`requests`, retry/backoff), BigQuery loading
- **BigQuery** — cloud data warehouse (free sandbox tier — no expiring trial)
- **dbt** — staging + marts, schema tests, custom data-quality tests
- **Prefect** — flow orchestration, task-level retries and logging
- **GitHub Actions** — CI (pytest on every push) + daily scheduled pipeline run
- **pytest** — unit tests for the ESPN response parser (mocked payloads, no live API calls)

## Data model

| Layer   | Table                    | Purpose                                                        |
|---------|--------------------------|-------------------------------------------------------------------|
| raw     | `raw_games`               | Landed game records, MERGE-upserted by `game_id`                    |
| staging | `stg_games`                | Typed, cleaned, `is_final` flag derived                              |
| marts   | `fct_games`                | One row per completed game, winner + margin computed                 |
| marts   | `int_team_game_log`        | Unpivoted to one row per team per game (feeds the two marts below)   |
| marts   | `agg_team_record`          | Win/loss record and average scoring per team per league               |
| marts   | `agg_scoring_trends`       | Trailing 5-game rolling scoring average per team (hot/cold streaks)   |

The raw load uses a **stage-then-MERGE** pattern rather than a plain
append, so re-running the pipeline for a date range that includes
in-progress games safely updates their scores once final, instead of
creating duplicate rows.

## Setup

### 1. Create a GCP project + enable BigQuery
BigQuery's [sandbox tier](https://cloud.google.com/bigquery/docs/sandbox)
is free indefinitely (with query/storage limits) — no credit card or
trial expiration to worry about. Create a project, then a **service
account** with the "BigQuery Data Editor" and "BigQuery Job User" roles,
and download its JSON key.

### 2. Bootstrap the dataset and tables
Run `sql/init_bigquery.sql` in the BigQuery console (swap in your project
id first).

### 3. Push this repo to GitHub
```bash
git init
git add .
git commit -m "Initial sports ETL pipeline"
git remote add origin <your-repo-url>
git push -u origin main
```

### 4. Add repo secrets
**Settings → Secrets and variables → Actions → New repository secret**:
- `GCP_PROJECT_ID`
- `GCP_SA_KEY` — paste the full contents of the service account JSON key

### 5. Run it
**Actions tab → Sports Pipeline → Run workflow** to trigger manually, or
wait for the daily schedule. **Actions tab → CI** runs automatically on
every push to catch parsing bugs before they reach the pipeline.

### Running locally instead
```bash
pip install -r requirements.txt
export GCP_PROJECT_ID=... GOOGLE_APPLICATION_CREDENTIALS=/path/to/key.json
python orchestration/flow.py --days-back 3
```

### Running just the tests
```bash
pytest tests/ -v
```

## Project layout

```
sports-pipeline/
├── .github/workflows/
│   ├── ci.yml                    # pytest on every push
│   └── pipeline.yml              # daily scheduled pipeline run
├── extract/
│   ├── espn_client.py            # API client + pure JSON parser
│   ├── run_extract.py            # standalone extract runner
│   └── load_to_bigquery.py       # stage + MERGE loader
├── orchestration/flow.py         # Prefect flow tying it together
├── dbt/sports_analytics/
│   ├── models/staging/           # cleaning layer
│   └── models/marts/             # game facts, team records, scoring trends
├── tests/test_extract.py         # pytest suite for the parser
└── sql/init_bigquery.sql         # one-time dataset/table bootstrap
```

## Notes / next steps

- The ESPN endpoint is public and undocumented (no official rate limits
  published), so the client uses retry-with-backoff and keeps request
  volume reasonable by default (one call per league per day, not per game).
- Natural extensions: deploy the Prefect flow to Prefect Cloud's free tier
  for a hosted run-history dashboard instead of relying on GitHub Actions
  logs, add play-by-play or player-level stats via ESPN's `/summary`
  endpoint, or add a Slack/email alert task on pipeline failure.
