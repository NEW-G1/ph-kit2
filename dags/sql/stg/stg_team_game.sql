-- stg_team_game: 팀 ID가 없는 줄을 빼고, 같은 시즌 같은 팀 안에서 경기 순번(game_seq)을 붙인다 (snapshot, sql_rules.md §1)
-- 상류: raw_mbb_historical_teams_games (당일 파티션)
-- game_seq 정렬은 raw의 모든 칸을 써서 같은 입력이면 같은 번호가 나오게 한다. 모든 칸이 같은 줄끼리는 번호가 바뀌어도 결과 행이 같다

-- (1) 테이블이 없을 때만 생성
CREATE TABLE IF NOT EXISTS `{{ project }}.{{ dataset_stg }}.stg_team_game`
(
  snapshot_date DATE OPTIONS (description = '실행 날짜 (Airflow ds). 파티션 키'),
  season INT64 OPTIONS (description = '경기가 열린 시즌'),
  team_id STRING OPTIONS (description = 'Sportradar 팀 ID. 비어 있는 줄은 이 표에 없다'),
  team_name STRING OPTIONS (description = '팀 이름'),
  market STRING OPTIONS (description = '팀의 학교 이름'),
  game_seq INT64 OPTIONS (description = '같은 시즌 같은 팀 안에서 줄을 구분하려고 붙인 1부터 시작하는 번호'),
  is_win BOOL OPTIONS (description = '팀이 이겼으면 참')
)
PARTITION BY snapshot_date
CLUSTER BY season, team_id
OPTIONS (
  partition_expiration_days = 7,
  description = '정리된 팀별 경기. raw_mbb_historical_teams_games(원천 bigquery-public-data.ncaa_basketball.mbb_historical_teams_games)에서 팀 ID가 있는 줄만 남기고 시즌과 팀 안의 경기 순번을 붙인다'
);

-- (2) 당일 파티션 삭제
DELETE FROM `{{ project }}.{{ dataset_stg }}.stg_team_game`
WHERE snapshot_date = DATE('{{ ds }}');

-- (3) 당일 파티션 적재
INSERT INTO `{{ project }}.{{ dataset_stg }}.stg_team_game`
  (snapshot_date, season, team_id, team_name, market, game_seq, is_win)
SELECT
  DATE('{{ ds }}') AS snapshot_date,
  season,
  team_id,
  name AS team_name,
  market,
  ROW_NUMBER() OVER (
    PARTITION BY season, team_id
    ORDER BY scheduled_date, opp_id, opp_code, opp_name, opp_market, opp_alias, opp_current_division,
             points_game, opp_points_game, win, attendance, name, market, alias, team_code, current_division
  ) AS game_seq,
  win AS is_win
FROM `{{ project }}.{{ dataset_raw }}.raw_mbb_historical_teams_games`
WHERE snapshot_date = DATE('{{ ds }}')
  AND team_id IS NOT NULL
  AND TRIM(team_id) <> '';
