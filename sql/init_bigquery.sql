-- Run this once in the BigQuery console (or via `bq query`) before the
-- pipeline runs. Replace `your-project-id` with your actual GCP project id,
-- or just run it interactively in the console where the project is already
-- selected for you.

CREATE SCHEMA IF NOT EXISTS `your-project-id.sports_analytics`
    OPTIONS (location = 'US');

CREATE TABLE IF NOT EXISTS `your-project-id.sports_analytics.raw_games` (
    game_id      STRING,
    league       STRING,
    game_date    STRING,
    status       STRING,
    home_team    STRING,
    home_score   INT64,
    away_team    STRING,
    away_score   INT64,
    venue        STRING,
    loaded_at    TIMESTAMP
);

-- Staging table the loader truncates and reloads into on every run before
-- merging into raw_games above.
CREATE TABLE IF NOT EXISTS `your-project-id.sports_analytics.raw_games_staging` (
    game_id      STRING,
    league       STRING,
    game_date    STRING,
    status       STRING,
    home_team    STRING,
    home_score   INT64,
    away_team    STRING,
    away_score   INT64,
    venue        STRING
);
