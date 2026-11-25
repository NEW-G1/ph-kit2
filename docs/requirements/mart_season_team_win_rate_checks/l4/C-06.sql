-- error_type: runtime_error
-- task: mart_season_team_win_rate

-- C-06: 결과의 (season, team_id) 조합 수 = 원천에서 팀 ID가 있는 고유 조합 수. 다르면 한 줄을 돌려준다.
SELECT m.mart_combo_cnt, s.source_combo_cnt
FROM (
  SELECT COUNT(*) AS mart_combo_cnt
  FROM `{{ project }}.{{ dataset_mart }}.mart_season_team_win_rate`
  WHERE snapshot_date = DATE('{{ ds }}')
) AS m
CROSS JOIN (
  SELECT COUNT(*) AS source_combo_cnt
  FROM (
    SELECT DISTINCT season, team_id
    FROM `bigquery-public-data.ncaa_basketball.mbb_historical_teams_games`
    WHERE team_id IS NOT NULL AND TRIM(team_id) != ''
  )
) AS s
WHERE m.mart_combo_cnt != s.source_combo_cnt
