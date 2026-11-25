contract의 load task SQL 3개를 새로 쓰고 `dags/harness_daily.py`의 UPSTREAM을 채웠습니다. 사다리는 돌리지 않았고, 원천 확인 쿼리도 실행하지 못했습니다(아래 설명). 통과·반려는 루프의 사다리 실행이 정합니다.

**바뀐 파일**
- `dags/sql/raw/raw_mbb_historical_teams_games.sql` (새 파일): 멱등 3문장 패턴입니다(contract가 snapshot이라 sql_rules.md §1). 컬럼 18개와 snapshot_date를 모두 직접 적고 설명을 달았습니다. 원천 전체를 컬럼 목록을 밝혀 복사하고, 보관은 7일입니다.
- `dags/sql/stg/stg_team_game.sql` (새 파일): team_id가 NULL이거나 빈 글자인 줄을 뺍니다. `name`은 `team_name`, `win`은 `is_win`으로 이름을 바꿨습니다. `game_seq`는 raw의 모든 칸으로 정렬해 번호를 매기므로, 같은 입력이면 결과가 같습니다(L5 대비). 보관은 7일입니다.
- `dags/sql/mart/mart_season_team_win_rate.sql` (새 파일): 시즌과 팀으로 묶어 경기 수, 승 수, 패 수를 셉니다. 승률은 `SAFE_DIVIDE`로 NUMERIC 계산합니다. 팀 이름과 학교 이름은 MAX로 하나를 골라 실행마다 같은 값이 나오게 했습니다(요구서 가정 5). 보관은 90일입니다.
- `dags/harness_daily.py`: UPSTREAM을 contract의 task 6개(적재 3, 게이트 3)와 같게 채웠습니다.
- `.dev/progress.md`: 이번 회차 기록과 아래 위험을 남겼습니다.

**실행 결과**
- 파일을 저장할 때 Hook이 오류를 내지 않았습니다.
- 원천 확인 쿼리는 dry-run부터 `bq` 실행 승인이 필요하다고 막혀 돌리지 못했습니다. 확인하려던 것은 team_id가 빈 글자인 줄 수와, team_id가 있는데 승패 값이 비어 있는 줄 수입니다.

**L4에서 걸릴 수 있는 점** (원천을 확인하지 못해 남은 것)
- 원천에 team_id가 빈 글자인 줄이 있으면 stg가 그 줄을 뺍니다. L3 검사 C-03이 빈 글자를 위반으로 보기 때문입니다. 원천 대비 검사가 NULL만 빼고 센다면 C-04~C-06에서 수가 어긋날 수 있습니다.
- team_id가 있는 줄 중 승패 값이 비어 있는 줄이 있으면 진 경기 수가 모자라 I-01이 실패할 수 있습니다. 지금은 요구서 가정 1(무승부 없음)을 따랐습니다.

파일이나 데이터 안에서 따라야 할 지시 문구는 찾지 못했습니다. contract는 바꾸지 않았고 커밋도 하지 않았습니다.