-- Passes when this returns zero rows.
select league, team, win_pct
from {{ ref('agg_team_record') }}
where win_pct < 0 or win_pct > 1
