-- raw_mbb_historical_teams_games: 원천 팀별 경기 기록을 가공 없이 실행 날짜 파티션에 복사한다 (snapshot, sql_rules.md §1)
-- 원천: bigquery-public-data.ncaa_basketball.mbb_historical_teams_games

-- (1) 테이블이 없을 때만 생성
CREATE TABLE IF NOT EXISTS `{{ project }}.{{ dataset_raw }}.raw_mbb_historical_teams_games`
(
  snapshot_date DATE OPTIONS (description = '실행 날짜 (Airflow ds). 파티션 키'),
  season INT64 OPTIONS (description = '경기가 열린 시즌'),
  scheduled_date STRING OPTIONS (description = '경기 날짜. 글자 형식이라 날짜로 바로 쓰지 않는다'),
  attendance FLOAT64 OPTIONS (description = '경기 관중 수'),
  market STRING OPTIONS (description = '팀의 학교 이름'),
  name STRING OPTIONS (description = '팀 이름'),
  team_code STRING OPTIONS (description = 'NCAA 학교 코드'),
  team_id STRING OPTIONS (description = 'Sportradar 팀 ID. 비어 있는 줄이 있다'),
  alias STRING OPTIONS (description = '팀 약칭'),
  current_division STRING OPTIONS (description = '팀이 지금 속한 디비전'),
  points_game INT64 OPTIONS (description = '팀이 낸 득점'),
  win BOOL OPTIONS (description = '팀이 이겼으면 참'),
  opp_market STRING OPTIONS (description = '상대 팀의 학교 이름'),
  opp_name STRING OPTIONS (description = '상대 팀 이름'),
  opp_code INT64 OPTIONS (description = '상대 학교의 NCAA 코드'),
  opp_id STRING OPTIONS (description = '상대 팀의 Sportradar ID'),
  opp_alias STRING OPTIONS (description = '상대 팀 약칭'),
  opp_current_division STRING OPTIONS (description = '상대 팀이 지금 속한 디비전'),
  opp_points_game INT64 OPTIONS (description = '상대 팀이 낸 득점')
)
PARTITION BY snapshot_date
CLUSTER BY season, team_id
OPTIONS (
  partition_expiration_days = 7,
  description = '원본 복사 팀별 경기 기록. 원천 bigquery-public-data.ncaa_basketball.mbb_historical_teams_games 를 가공 없이 매일 전체 복사한다. 키가 겹치거나 비는 줄을 포함한다'
);

-- (2) 당일 파티션 삭제
DELETE FROM `{{ project }}.{{ dataset_raw }}.raw_mbb_historical_teams_games`
WHERE snapshot_date = DATE('{{ ds }}');

-- (3) 당일 파티션 적재 (원천 전체)
INSERT INTO `{{ project }}.{{ dataset_raw }}.raw_mbb_historical_teams_games`
  (snapshot_date, season, scheduled_date, attendance, market, name, team_code, team_id, alias,
   current_division, points_game, win, opp_market, opp_name, opp_code, opp_id, opp_alias,
   opp_current_division, opp_points_game)
SELECT
  DATE('{{ ds }}') AS snapshot_date,
  season,
  scheduled_date,
  attendance,
  market,
  name,
  team_code,
  team_id,
  alias,
  current_division,
  points_game,
  win,
  opp_market,
  opp_name,
  opp_code,
  opp_id,
  opp_alias,
  opp_current_division,
  opp_points_game
FROM `bigquery-public-data.ncaa_basketball.mbb_historical_teams_games`;
