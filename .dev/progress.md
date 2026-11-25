# 진행 기록

## 요구서 — mart_season_team_win_rate
docs/requirements/mart_season_team_win_rate.md

## 작업 목록 — mart_season_team_win_rate

마트 실행 반복 1/5, 연속 없음 0/3

| # | 작업 | 상태 | 반복 | 최근 반려 |
|---|---|---|---|---|
| 1 | raw_mbb_historical_teams_games (raw) | 통과 | 0 | — |
| 2 | stg_team_game (stg) | 통과 | 0 | — |
| 3 | mart_season_team_win_rate (mart) | 통과 | 0 | — |

## builder 기록 — iteration 1 (mart_season_team_win_rate)

- 과거 반려: .dev/rejections.jsonl 에 이 마트 반려 없음(첫 작업)
- load.mode: snapshot → sql_rules.md §1 멱등 3문장 패턴(CREATE IF NOT EXISTS / DELETE 당일 / INSERT 당일)
- 읽은 검사: _checks/l3/C-01·C-02·C-03 (l4·l5는 읽지 않음)

### 변경 파일
- dags/sql/raw/raw_mbb_historical_teams_games.sql (신규): 명시 DDL 18컬럼+snapshot_date, 모든 컬럼 설명, 만료 7일, CLUSTER BY season, team_id. 원천 전체를 컬럼 목록 명시로 INSERT
- dags/sql/stg/stg_team_game.sql (신규): team_id IS NOT NULL AND TRIM(team_id) <> '' 만 남김. name→team_name, win→is_win. game_seq = ROW_NUMBER() OVER (PARTITION BY season, team_id ORDER BY raw의 모든 칸). 모든 칸이 같은 줄끼리만 순서가 정해지지 않으므로 결과 행 집합은 결정적(L5 대비). 만료 7일
- dags/sql/mart/mart_season_team_win_rate.sql (신규): GROUP BY season, team_id. games_cnt=COUNT(*), wins_cnt=COUNTIF(is_win), losses_cnt=COUNTIF(NOT is_win), win_rate=SAFE_DIVIDE(CAST(wins AS NUMERIC), CAST(games AS NUMERIC)) (NUMERIC, contract 타입). team_name·market은 MAX로 결정적으로 고름(가정 5). 만료 90일
- dags/harness_daily.py: UPSTREAM을 contract dag.tasks 6개(load 3, gate 3)와 같게 채움

### 실행 결과
- 파일 저장 때 Hook(after_edit) 오류 출력 없음
- 원천 전제 확인 쿼리(빈 글자 team_id 줄 수, team_id가 있고 win이 NULL인 줄 수)는 dry-run 단계에서 bq 실행 승인이 필요하다고 막혀 실행하지 못함. 우회하지 않음
- run_ladder는 루프가 실행하므로 builder가 돌리지 않음. 통과·반려 판정은 사다리 종료 코드로 정한다

### 확인하지 못한 위험 (사다리 L4에서 드러날 수 있음)
- team_id가 빈 글자('')인 줄이 원천에 있으면 stg는 그 줄을 뺀다(C-03이 빈 글자를 위반으로 보기 때문). 원천 대비 검사가 IS NOT NULL만 기준으로 하면 C-04·C-05·C-06에서 차이가 날 수 있음
- team_id가 있는 줄에 win이 NULL이면 losses_cnt(COUNTIF(NOT is_win))가 모자라 I-01이 실패할 수 있음. 요구서 가정 1(무승부 없음)을 따름
- 파일·설명·데이터 속 지시 문구: 발견 없음

## 직전 반복 인계
- [루프 mart_season_team_win_rate] iteration 1: 신호 없음 (STATUS 줄 없음, 반려 아님)
- [루프 mart_season_team_win_rate] iteration 1: 사다리 통과
