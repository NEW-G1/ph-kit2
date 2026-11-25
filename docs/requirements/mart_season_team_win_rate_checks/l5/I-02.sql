-- error_type: idempotency_break
-- task: mart_season_team_win_rate

-- I-02: 같은 날짜로 두 번 실행해도 결과가 같다.
-- 두 실행의 행 수·체크섬 비교는 사다리(l5_idem)가 한다. 이 쿼리는 2회 실행 뒤 남은 당일 파티션에
-- 이중 적재 흔적이 없는지 본다: 행 수가 원천의 고유 (season, team_id) 조합 수와 같고,
-- 경기 수 합계가 원천에서 팀 ID가 있는 줄 수와 같아야 한다. 다르면 한 줄을 돌려준다.
SELECT m.mart_rows, s.source_combo_cnt, m.mart_games_cnt, s.source_games_cnt
FROM (
  SELECT COUNT(*) AS mart_rows, COALESCE(SUM(games_cnt), 0) AS mart_games_cnt
  FROM `{{ project }}.{{ dataset_mart }}.mart_season_team_win_rate`
  WHERE snapshot_date = DATE('{{ ds }}')
) AS m
CROSS JOIN (
  SELECT COUNT(*) AS source_games_cnt, COUNT(DISTINCT TO_JSON_STRING(STRUCT(season, team_id))) AS source_combo_cnt
  FROM `bigquery-public-data.ncaa_basketball.mbb_historical_teams_games`
  WHERE team_id IS NOT NULL AND TRIM(team_id) != ''
) AS s
WHERE m.mart_rows != s.source_combo_cnt
   OR m.mart_games_cnt != s.source_games_cnt
