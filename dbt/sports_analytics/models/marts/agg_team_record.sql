select
    league,
    team,
    count(*)                                            as games_played,
    sum(case when is_win then 1 else 0 end)             as wins,
    sum(case when not is_win then 1 else 0 end)         as losses,
    round(
        safe_divide(sum(case when is_win then 1 else 0 end), count(*)), 3
    )                                                    as win_pct,
    round(avg(points_scored), 1)                        as avg_points_scored,
    round(avg(points_allowed), 1)                       as avg_points_allowed
from {{ ref('int_team_game_log') }}
group by league, team
order by league, win_pct desc
