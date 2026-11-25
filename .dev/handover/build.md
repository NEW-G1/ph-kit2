# 인수인계 — mart_season_team_win_rate (build, 2026-11-25)

> 사실 칸(2·3·4·5·8)은 `scripts/handover/make_facts.py` 출력이다. 고치거나 추측해서 채우지 않는다.
> 설명 칸(1·6·7)만 builder가 쓴다 (`.claude/rules/handover.md`).

- contract_version: 1
- 생성 시각: 2026-11-25T11:12:05+09:00
- 기준 커밋: ee6a7a5a9bec48e273a8d58c68821bc8f197478d

## 1. 한 줄 요약
미국 대학 남자 농구의 팀별 경기 기록(NCAA 공개 데이터, `ncaa_basketball`의 `mbb_historical_teams_games`)을 하루 한 번 전체 복사해, 시즌마다 팀마다 경기 수, 이긴 수, 진 수, 승률을 한 줄로 집계한 결과 표(`mart_season_team_win_rate`)를 만든다.

## 2. 바뀐 것  ← 코드
기준점 `a5eea51d` 대비 (git diff a5eea51d...HEAD). contract: 기준점 v1 → 지금 v1

| 구분 | 이름 | 변경 |
|---|---|---|
| 테이블 | thelook_raw.raw_mbb_historical_teams_games | 그대로 |
| 테이블 | thelook_stg.stg_team_game | 그대로 |
| 테이블 | thelook_mart.mart_season_team_win_rate | 그대로 |
| task | raw_mbb_historical_teams_games | 그대로 |
| task | gate_raw_mart_season_team_win_rate | 그대로 |
| task | stg_team_game | 그대로 |
| task | gate_stg_mart_season_team_win_rate | 그대로 |
| task | mart_season_team_win_rate | 그대로 |
| task | gate_mart_mart_season_team_win_rate | 그대로 |
| 파일 | dags/harness_daily.py | 변경 |
| 파일 | dags/sql/dq/gate_mart_mart_season_team_win_rate.sql | 신규 |
| 파일 | dags/sql/dq/gate_raw_mart_season_team_win_rate.sql | 신규 |
| 파일 | dags/sql/dq/gate_stg_mart_season_team_win_rate.sql | 신규 |
| 파일 | dags/sql/mart/mart_season_team_win_rate.sql | 신규 |
| 파일 | dags/sql/raw/raw_mbb_historical_teams_games.sql | 신규 |
| 파일 | dags/sql/stg/stg_team_game.sql | 신규 |
| 파일 | docs/requirements/mart_season_team_win_rate_checks/l3/C-01.sql | 신규 |
| 파일 | docs/requirements/mart_season_team_win_rate_checks/l3/C-02.sql | 신규 |
| 파일 | docs/requirements/mart_season_team_win_rate_checks/l3/C-03.sql | 신규 |
| 파일 | docs/requirements/mart_season_team_win_rate_checks/l4/C-04.sql | 신규 |
| 파일 | docs/requirements/mart_season_team_win_rate_checks/l4/C-05.sql | 신규 |
| 파일 | docs/requirements/mart_season_team_win_rate_checks/l4/C-06.sql | 신규 |
| 파일 | docs/requirements/mart_season_team_win_rate_checks/l4/I-01.sql | 신규 |
| 파일 | docs/requirements/mart_season_team_win_rate_checks/l5/I-02.sql | 신규 |

## 3. 데이터 흐름  ← 코드 (DAG 의존성)
원천: bigquery-public-data.ncaa_basketball.mbb_historical_teams_games

- (원천) → raw_mbb_historical_teams_games
- raw_mbb_historical_teams_games → stg_team_game
- stg_team_game → mart_season_team_win_rate

게이트: gate_raw_mart_season_team_win_rate (raw 층, 상류 raw_mbb_historical_teams_games), gate_stg_mart_season_team_win_rate (stg 층, 상류 stg_team_game), gate_mart_mart_season_team_win_rate (mart 층, 상류 mart_season_team_win_rate)

OM 리니지 링크는 결재 후 L6 통과 시 docs/handover/ 반영 때 추가한다.

## 4. 검증 결과  ← 코드 (검증 사다리)
contract v1의 사다리 반복 1회

| 반복 | 판정 | task별 |
|---|---|---|
| 1 | pass | raw_mbb_historical_teams_games pass, stg_team_game pass, mart_season_team_win_rate pass |

마지막 통과 반복 1 (task 3/3 통과, ds 2026-11-25)

| 단계 | 결과 | 수치 |
|---|---|---|
| L0 계약·DAG 구조 | 통과 | load_tasks 3, gate_tasks 3, tables 3, checks 8, traces 9 |
| L1 dry-run | 통과 | 스캔량 합 0 bytes (여러 문장 스크립트는 하한값) |
| L2 ai_dev 실행 | 통과 | 실행한 테이블 mart_season_team_win_rate, raw_mbb_historical_teams_games, stg_team_game |
| L3 레이어 게이트 | 통과 | 검사 C-01, C-02, C-03 위반 0행 |
| L4 정합성 | 통과 | 검사 C-04, C-05, C-06, I-01 위반 0행 |
| L5 멱등성 | 통과 | 재실행 전후 행 수·체크섬 같음 (ds 파티션 행 수 합 968,068), 검사 I-02 위반 0행 |
| L6 OM 등록 | 결재 후 | 운영 DAG·OM 에이전트 실행 뒤 판정 |

### 비용  ← 코드 (.dev/cost.jsonl)
실행 1회 (RUN-001)

| 역할 | 호출 수 | 비용 합(USD, 정가 환산 추정) | 입력 토큰 | 출력 토큰 | bq 바이트 |
|---|---|---|---|---|---|
| builder | 1 | 0.8023 | 28 | 12,179 | 461,293,928 |
| verifier | 1 | 0.2517 | 10 | 7,323 | 0 |

## 5. 반려 이력  ← 코드 (.dev/rejections.jsonl)
`.dev/rejections.jsonl` (해결 = 같은 task가 그 뒤 반복에서 통과한 첫 반복, ladder_result 기준)

반려 없음

**개입 기록** (`.dev/interventions.jsonl`, 같은 마트, 해석 없이 그대로)

| ID | 시각 | 종류 | 단계 | 대상 | 분 | 메모 |
|---|---|---|---|---|---|---|
| H-0001 | 2026-11-25T10:58:29+09:00 | approval | approval_1 | PR #2 머지 a5eea51 | 6 | git 머지 기록에서 자동 |

## 6. 운영 방법
- DAG는 `harness_daily` 하나이고 작업은 6개다. 순서는 원본 복사(raw) → raw 검사 → 정리(stg) → stg 검사 → 결과 표(mart) → mart 검사다. 표 하나가 작업 하나라서, 실패한 작업의 이름이 곧 문제의 표다.
- 적재 방식은 snapshot이다. 실행할 때마다 원천 전체(약 117 MB)를 그날의 `snapshot_date` 파티션에 복사한다. 원천은 과거 기록이라 값이 바뀌지 않는다.
- 재실행은 같은 날짜로 그대로 다시 실행하면 된다. 각 SQL은 당일 파티션을 지우고 다시 넣는 방식이라 결과가 같다(멱등).
- 검사 작업이 실패하면 로그의 `[C-xx]` 번호로 어느 검사인지 찾는다. 검사는 재시도하지 않는다(`retries=0`). 번호의 뜻은 `docs/requirements/mart_season_team_win_rate.contract.json`의 `checks`에 있다.
- 보관 기간은 raw, stg 7일, mart 90일이다.
- 결재 전에는 `ai_dev`에서만 실행했고, 운영 데이터셋 실행과 운영 DAG 실행은 승인 2 이후 사람이 한다. 운영 등록 확인(L6)은 아직 하지 않았다.

## 7. 주의점과 알려진 데이터 특성
- 팀 ID가 비어 있는 줄이 원천에 188,265개(전체 571,448줄의 약 33%) 있다. 어느 팀인지 알 수 없어 정리 단계에서 뺀다. 결과 표의 경기 수 합계는 원천 전체 줄 수보다 적다. 정리 단계는 빈 글자인 팀 ID도 함께 뺀다.
- 팀 정보가 있는 줄 중 시즌, 팀, 날짜, 상대, 양쪽 득점이 모두 같은 줄이 66묶음(2줄씩) 있다. 중복 입력인지 실제 경기인지 구분할 수 없어 그대로 센다.
- 경기 날짜 칸은 글자 형식이고 111,168줄이 비어 있어 쓰지 않는다. 시즌은 `season` 칸을 쓴다. 기간은 1996~2016 시즌이다.
- 시즌 기록 표(`mbb_historical_teams_seasons`)는 이긴 수 합계가 이 경기 표와 같은 시즌·팀 조합이 13,328개 중 8,932개(약 67%)뿐이라 쓰지 않았고, 정합성 검사도 경기 표 자체로 한다.
- 같은 시즌, 같은 팀 ID 안에서 팀 이름과 학교 이름은 하나라고 보고 `MAX`로 고른다(요구서 가정 5).
- `win_rate`는 비율이라 행끼리 더하거나 평균 내면 틀린 값이 된다. 여러 팀이나 시즌을 합칠 때는 `wins_cnt`와 `games_cnt`를 먼저 합쳐 다시 나눈다.
- 위 "바뀐 것"과 "링크" 표의 데이터셋 이름이 `thelook_raw`, `thelook_stg`, `thelook_mart`로 나오는 것은 `dags/harness_config.json`의 운영 데이터셋 설정 값이 그대로 남아 있어서다. 원천(`ncaa_basketball`)과 무관한 이름이다. 이름 변경은 설정 변경이라 사람 결재 대상이다.
- 파일, 설명, 데이터 속 지시 문구는 발견하지 못했다.

## 8. 링크  ← 코드
- OM 테이블: 결재 후 L6 통과 시 docs/handover/ 반영 때 추가
- 납품 산출물: 아직 없음 (out/deliverables/)
- 요구서: docs/requirements/mart_season_team_win_rate.md
- contract: docs/requirements/mart_season_team_win_rate.contract.json
- 인터뷰 기록: docs/requirements/mart_season_team_win_rate_interview.md
