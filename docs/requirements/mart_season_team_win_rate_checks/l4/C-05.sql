-- error_type: runtime_error
-- task: mart_season_team_win_rate

-- C-05: 결과의 이긴 경기 수 합계 = 원천에서 팀 ID가 있고 승리인 줄 수. 다르면 한 줄을 돌려준다.
SELECT m.mart_wins_cnt, s.source_wins_cnt
FROM (
  SELECT COALESCE(SUM(wins_cnt), 0) AS mart_wins_cnt
  FROM `{{ project }}.{{ dataset_mart }}.mart_season_team_win_rate`
  WHERE snapshot_date = DATE('{{ ds }}')
) AS m
CROSS JOIN (
  SELECT COUNTIF(win IS TRUE) AS source_wins_cnt
  FROM `bigquery-public-data.ncaa_basketball.mbb_historical_teams_games`
  WHERE team_id IS NOT NULL AND TRIM(team_id) != ''
) AS s
WHERE m.mart_wins_cnt != s.source_wins_cnt
