{{
    config(
        materialized='table'
    )
}}

-- Unpivots fct_games from one-row-per-game to one-row-per-team-per-game,
-- which is the shape the downstream record/trend marts need. Kept as its
-- own model (rather than inlined into each mart) since both agg_team_record
-- and agg_scoring_trends build on this exact same team-perspective shape.

with home_rows as (
    select
        game_id, league, game_day,
        home_team as team,
        away_team as opponent,
        home_score as points_scored,
        away_score as points_allowed,
        winning_team = home_team as is_win
    from {{ ref('fct_games') }}
),

away_rows as (
    select
        game_id, league, game_day,
        away_team as team,
        home_team as opponent,
        away_score as points_scored,
        home_score as points_allowed,
        winning_team = away_team as is_win
    from {{ ref('fct_games') }}
)

select * from home_rows
union all
select * from away_rows
