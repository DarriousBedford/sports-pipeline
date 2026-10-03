with source as (
    select * from {{ source('raw', 'raw_games') }}
    -- raw_games is append-only (the loader no longer MERGEs), so the same
    -- game can appear multiple times. Keep only the most recent load per game.
    qualify row_number() over (
        partition by game_id
        order by loaded_at desc
    ) = 1
),

parsed as (
    select
        *,
        -- ESPN's game_date sometimes omits seconds (e.g. "2026-08-03T23:40Z"
        -- instead of "...23:40:00Z"), which a plain CAST to TIMESTAMP
        -- rejects. Try the with-seconds format first, fall back to the
        -- without-seconds format, so either shape parses cleanly.
        coalesce(
            safe.parse_timestamp('%Y-%m-%dT%H:%M:%SZ', game_date),
            safe.parse_timestamp('%Y-%m-%dT%H:%MZ', game_date)
        ) as parsed_game_date
    from source
),

cleaned as (
    select
        game_id,
        league,
        parsed_game_date               as game_date,
        date(parsed_game_date)         as game_day,
        status,
        home_team,
        home_score,
        away_team,
        away_score,
        venue,
        -- ESPN reports STATUS_FINAL only once a game has actually concluded;
        -- everything else (scheduled, in-progress, postponed) we treat as not final
        status = 'STATUS_FINAL' as is_final
    from parsed
    where game_id is not null
)

select * from cleaned
