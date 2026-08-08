-- Passes when this returns zero rows.
select game_id, home_score, away_score
from {{ ref('fct_games') }}
where home_score < 0 or away_score < 0
