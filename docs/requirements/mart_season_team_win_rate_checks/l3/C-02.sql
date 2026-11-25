-- error_type: range_violation
-- task: mart_season_team_win_rate

-- C-02: 승률은 0 이상 1 이하이다. 범위를 벗어나거나 비어 있는 행을 돌려준다.
-- 경기 수는 1 이상이므로 승률이 NULL인 행도 위반으로 본다.
SELECT season, team_id, games_cnt, wins_cnt, win_rate
FROM `{{ project }}.{{ dataset_mart }}.mart_season_team_win_rate`
WHERE snapshot_date = DATE('{{ ds }}')
  AND (win_rate IS NULL OR win_rate < 0 OR win_rate > 1)
