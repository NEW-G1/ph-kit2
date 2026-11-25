-- mart_season_team_win_rate: 시즌마다 팀마다 경기 수, 승 수, 패 수, 승률을 집계한다 (snapshot, sql_rules.md §1)
-- 상류: stg_team_game (당일 파티션)
-- team_name, market은 같은 시즌 같은 팀 안에서 하나라고 가정한다(요구서 가정 5). 같은 입력에 같은 값이 나오도록 MAX로 고른다

-- (1) 테이블이 없을 때만 생성
CREATE TABLE IF NOT EXISTS `{{ project }}.{{ dataset_mart }}.mart_season_team_win_rate`
(
  snapshot_date DATE OPTIONS (description = '실행 날짜 (Airflow ds). 파티션 키'),
  season INT64 OPTIONS (description = '경기가 열린 시즌'),
  team_id STRING OPTIONS (description = 'Sportradar 팀 ID'),
  team_name STRING OPTIONS (description = '팀 이름'),
  market STRING OPTIONS (description = '팀의 학교 이름'),
  games_cnt INT64 OPTIONS (description = '그 시즌에 팀이 치른 경기 수'),
  wins_cnt INT64 OPTIONS (description = '그 시즌에 팀이 이긴 경기 수'),
  losses_cnt INT64 OPTIONS (description = '그 시즌에 팀이 진 경기 수'),
  win_rate NUMERIC OPTIONS (description = '이긴 경기 수를 치른 경기 수로 나눈 값(0~1). 다른 행과 합산하거나 평균내면 틀린 값이 된다')
)
PARTITION BY snapshot_date
CLUSTER BY season, team_id
OPTIONS (
  partition_expiration_days = 90,
  description = '시즌별 팀별 승률. stg_team_game(원천 bigquery-public-data.ncaa_basketball.mbb_historical_teams_games)을 시즌과 팀으로 집계한다. 팀 ID가 없는 줄은 빠져 있다'
);

-- (2) 당일 파티션 삭제
DELETE FROM `{{ project }}.{{ dataset_mart }}.mart_season_team_win_rate`
WHERE snapshot_date = DATE('{{ ds }}');

-- (3) 당일 파티션 적재
INSERT INTO `{{ project }}.{{ dataset_mart }}.mart_season_team_win_rate`
  (snapshot_date, season, team_id, team_name, market, games_cnt, wins_cnt, losses_cnt, win_rate)
SELECT
  DATE('{{ ds }}') AS snapshot_date,
  season,
  team_id,
  MAX(team_name) AS team_name,
  MAX(market) AS market,
  COUNT(*) AS games_cnt,
  COUNTIF(is_win) AS wins_cnt,
  COUNTIF(NOT is_win) AS losses_cnt,
  SAFE_DIVIDE(CAST(COUNTIF(is_win) AS NUMERIC), CAST(COUNT(*) AS NUMERIC)) AS win_rate
FROM `{{ project }}.{{ dataset_stg }}.stg_team_game`
WHERE snapshot_date = DATE('{{ ds }}')
GROUP BY season, team_id;
