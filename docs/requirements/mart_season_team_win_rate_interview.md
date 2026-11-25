# mart_season_team_win_rate 인터뷰 기록

## ① 문제 확인
- 요청: "시즌별 팀별 승률을 보고 싶다"
- 이해한 내용: 시즌마다 팀마다 한 줄로, 그 시즌에 팀이 치른 경기 중 이긴 비율(승률)
- 원천: `bigquery-public-data.ncaa_basketball` (리전 US). 선택한 표 3개 중 경기 표(`mbb_historical_teams_games`)만 쓴다.
- 개인정보: 후보 칸 모두 "없음"으로 사람이 확정함(S11, `docs/architecture/pii_columns.md`)

## ② 데이터 확인 (고정 조회 결과, 집계값만)
| # | 조회 | 결과 |
|---|---|---|
| 1 | 값 분포 | 승패(`win`): 이김 291,531, 짐 279,917. 현재 디비전: D1 221,020, 비어 있음 189,275, D3 78,126, D2 71,579, NAIA 7,487, USCAA 1,986, NCCAA 1,889, NCAIA 85, CIS 1 |
| 2 | 빈 값 | 전체 571,448줄. 시즌 0, 경기 날짜 111,168, 팀 이름 188,265, 팀 ID 188,265, 학교 이름 107,222, 승패 0, 득점 0, 상대 득점 0 |
| 3 | 기간 | 시즌 1996~2016(21개). 팀 ID 714개. 시즌과 팀 ID 조합 13,437개. 경기 날짜는 글자 형식(예: 01-APR-00 12:00 AM) |
| 4 | 키 후보 중복 | 팀 정보가 있는 줄 중 시즌, 팀, 날짜, 상대, 양쪽 득점이 모두 같은 묶음 66개(2줄씩, 3줄 이상 없음). 팀 ID가 없는 줄은 키를 만들 수 없음 |
| 5 | 조인 시 행 증가 | 조인 없음(경기 표 하나만 읽음). 참고로 시즌 기록 표와 비교하면 같은 시즌과 팀 조합 13,328개 중 승 합계가 같은 것은 8,932개, 패 합계가 같은 것은 10,723개 |
| 6 | 개인정보 후보 | 후보 칸은 `name`, `opp_name`(팀 이름)뿐이었고 사람이 개인정보 아님으로 확정함 |
| 7 | 크기와 파티션 | 경기 표 122,556,944 바이트, 571,448줄, 날짜 파티션 없음. 시즌 기록 표 6,260,443 바이트, 경기 표(`mbb_games_sr`) 50,412,402 바이트 → snapshot |

### 위험 항목
- 팀 ID가 없는 줄이 33%(188,265줄): 정리 단계에서 빼고 건수를 검사에 잇는다(R-03, C-04)
- 완전히 같은 줄 66묶음: 그대로 센다. 중복 입력인지 실제 경기인지 코드로 구분할 수 없다
- 경기 날짜 칸이 글자 형식이고 비어 있는 줄이 많음: 쓰지 않는다
- 시즌 기록 표와 승 합계가 67%만 맞음: 일치 검사의 기준으로 쓰지 않는다(R-04는 경기 표 자체로 비교)

### 근거 쿼리
고정 조회는 모두 dry-run을 먼저 돌렸고(최대 54,925,172 바이트) 본 실행에 `--maximum_bytes_billed=524288000`을 걸었다. 읽은 표는 `bigquery-public-data.ncaa_basketball`의 `mbb_historical_teams_games`, `mbb_historical_teams_seasons`, `__TABLES__`이다.

```sql
-- 조회 1: 값 분포
SELECT 'win' AS col, CAST(win AS STRING) AS val, COUNT(*) AS n FROM `bigquery-public-data.ncaa_basketball.mbb_historical_teams_games` GROUP BY val
UNION ALL
SELECT 'current_division', CAST(current_division AS STRING), COUNT(*) FROM `bigquery-public-data.ncaa_basketball.mbb_historical_teams_games` GROUP BY 2
ORDER BY col, n DESC
```

```sql
-- 조회 2: 빈 값
SELECT COUNT(*) AS total_rows, COUNTIF(season IS NULL) AS null_season, COUNTIF(scheduled_date IS NULL) AS null_scheduled_date, COUNTIF(name IS NULL) AS null_name, COUNTIF(team_id IS NULL) AS null_team_id, COUNTIF(market IS NULL) AS null_market, COUNTIF(win IS NULL) AS null_win, COUNTIF(points_game IS NULL) AS null_points_game, COUNTIF(opp_points_game IS NULL) AS null_opp_points_game
FROM `bigquery-public-data.ncaa_basketball.mbb_historical_teams_games`
```

```sql
-- 조회 3: 기간
SELECT MIN(season) AS min_season, MAX(season) AS max_season, COUNT(DISTINCT season) AS n_seasons, MIN(scheduled_date) AS min_date_str, MAX(scheduled_date) AS max_date_str, COUNT(DISTINCT team_id) AS n_teams, COUNT(DISTINCT CONCAT(CAST(season AS STRING), '|', team_id)) AS n_season_team_keys
FROM `bigquery-public-data.ncaa_basketball.mbb_historical_teams_games`
```

```sql
-- 조회 4와 5: 키 중복, 시즌 기록 표와 비교
WITH g AS (SELECT season, team_id, COUNT(*) AS games, COUNTIF(win) AS wins, COUNTIF(win IS NOT NULL AND NOT win) AS losses FROM `bigquery-public-data.ncaa_basketball.mbb_historical_teams_games` GROUP BY season, team_id),
dup AS (SELECT COUNT(*) AS dup_rows FROM (SELECT season, team_id, scheduled_date, opp_id, COUNT(*) AS c FROM `bigquery-public-data.ncaa_basketball.mbb_historical_teams_games` GROUP BY 1, 2, 3, 4 HAVING c > 1)),
s AS (SELECT season, team_id, COUNT(*) AS rows_in_seasons, SUM(wins) AS wins, SUM(losses) AS losses, SUM(ties) AS ties FROM `bigquery-public-data.ncaa_basketball.mbb_historical_teams_seasons` GROUP BY season, team_id)
SELECT (SELECT dup_rows FROM dup) AS dup_game_rows, (SELECT COUNT(*) FROM g) AS keys_in_games, (SELECT COUNT(*) FROM s) AS keys_in_seasons, (SELECT MAX(rows_in_seasons) FROM s) AS max_rows_per_key_in_seasons, COUNT(*) AS keys_matched, COUNTIF(g.wins = s.wins) AS wins_equal, COUNTIF(g.losses = s.losses) AS losses_equal, COUNTIF(g.games = s.wins + s.losses + IFNULL(s.ties, 0)) AS games_equal_wlt
FROM g JOIN s USING (season, team_id)
```

```sql
-- 조회 4 보충: 팀 정보가 있는 줄의 완전 중복
SELECT COUNT(*) AS dup_groups, SUM(c) AS rows_in_dup_groups, SUM(c - 1) AS extra_rows, COUNTIF(c = 2) AS groups_of_2, COUNTIF(c > 2) AS groups_over_2
FROM (SELECT season, team_id, scheduled_date, opp_id, points_game, opp_points_game, COUNT(*) AS c FROM `bigquery-public-data.ncaa_basketball.mbb_historical_teams_games` WHERE team_id IS NOT NULL GROUP BY 1, 2, 3, 4, 5, 6 HAVING c > 1)
```

```sql
-- 조회 7: 크기
SELECT table_id, row_count, size_bytes, type FROM `bigquery-public-data.ncaa_basketball.__TABLES__` WHERE table_id IN ('mbb_historical_teams_games', 'mbb_historical_teams_seasons', 'mbb_games_sr') ORDER BY table_id
```

## ③~⑤ 질문과 답
| 번호 | 질문 | 기본안 | 근거 | 답 |
|---|---|---|---|---|
| 1/6 | 팀 이름과 팀 ID가 비어 있는 줄을 어떻게 할까 | 결과에서 빼고 빼는 건수를 기록 | 188,265줄(33%)은 어느 팀인지 알 수 없음 | 기본안대로 |
| 2/6 | 승률을 어떻게 계산할까 | 이긴 경기 수 ÷ 치른 경기 수. 완전히 같은 줄 66묶음은 그대로 셈 | 승패 칸 빈 값 0, 무승부 칸 없음, 완전 중복 66묶음 | 기본안대로 |
| 3/6 | 어느 표를 쓸까 | 경기 표 하나만 | 시즌 기록 표와 승 합계가 67%만 맞음 | 기본안대로 |
| 4/6 | 결과 표 이름 | `mart_season_team_win_rate` | 결과 한 줄은 시즌과 팀 | 기본안대로 |
| 5/6 | 갱신 주기 | 하루 한 번 전체 복사(snapshot) | 원천 500 MB 이하, 날짜 파티션 없음 | 기본안대로 |
| 6/6 | 가정 8개와 범위 밖 | 요구서 9절 그대로 | 위 조회 | 기본안대로 |

### 가정
요구서 9절의 가정 8개와 같다.

## ⑥ 결재 요약
- 만들 것: 시즌마다 팀마다 한 줄의 승률 표
- 작업 목록: 원본 복사 → 검사 → 정리 → 검사 → 결과 표 → 검사 (적재 3개, 검사 3개)
- 결과 한 줄의 모양: 시즌, 팀 ID, 팀 이름, 학교 이름, 치른 경기 수, 이긴 경기 수, 진 경기 수, 승률
- 읽는 원천: `mbb_historical_teams_games` 하나(약 117 MB, 전체를 읽음)
- 막은 개인정보 칸: 없음
