-- Trailing 5-game rolling averages per team, ordered by game date.
-- Surfaces hot/cold streaks that a season-long average would hide --
-- e.g. a team allowing 30+ points/game over its last 5 despite a strong
-- overall record.

select
    game_id,
    league,
    team,
    game_day,
    points_scored,
    points_allowed,
    round(avg(points_scored) over (
        partition by team
        order by game_day
        rows between 4 preceding and current row
    ), 1) as trailing_5_avg_scored,
    round(avg(points_allowed) over (
        partition by team
        order by game_day
        rows between 4 preceding and current row
    ), 1) as trailing_5_avg_allowed
from {{ ref('int_team_game_log') }}
order by league, team, game_day
