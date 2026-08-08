{{
    config(
        materialized='table'
    )
}}

with games as (
    select * from {{ ref('stg_games') }}
    where is_final  -- only completed games belong in the fact table
),

with_outcome as (
    select
        game_id,
        league,
        game_day,
        home_team,
        home_score,
        away_team,
        away_score,
        venue,
        home_score - away_score as home_margin,
        case
            when home_score > away_score then home_team
            when away_score > home_score then away_team
            else null  -- tie (possible in NFL/MLB)
        end as winning_team,
        home_score + away_score as total_points
    from games
)

select * from with_outcome
