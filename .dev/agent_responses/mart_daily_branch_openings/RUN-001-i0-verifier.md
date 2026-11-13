검증 쿼리 11개를 `docs/requirements/mart_daily_branch_openings_checks/` 아래에 썼습니다. 쿼리는 실행하지 않았고, builder의 SQL과 `.dev/progress.md`는 보지 않았습니다. 머리말(`-- error_type:`, `-- task:`)은 `devlog.py`의 ERROR_TYPES에서 골랐습니다.

contract가 `load.mode: snapshot`이라 파티션 조건은 모두 `snapshot_date = DATE('{{ ds }}')`입니다. 원천은 `bigquery-public-data.fdic_banks.locations` 전체와 비교합니다.

| 단계 | check id | 검사 내용 |
|---|---|---|
| l3 | C-01 | raw 당일 파티션이 0행이면 위반 |
| l3 | C-02 | stg의 `branch_fdic_uninum` 중복 또는 NULL |
| l3 | C-03 | stg의 `established_date` NULL |
| l3 | C-04 | mart의 `established_date` 중복 |
| l3 | C-05 | mart의 `new_branch_cnt`가 NULL 또는 1 미만 |
| l4 | C-06 | stg 행 수와 원천 행 수가 다름 |
| l4 | C-07 | mart `new_branch_cnt` 합계와 원천 행 수가 다름 |
| l4 | C-08 | mart 행 수와 원천 `date_established`의 서로 다른 날짜 수가 다름 |
| l4 | C-09 | 날짜별 건수가 다르거나 한쪽에만 있는 날짜 (FULL OUTER JOIN) |
| l4 | I-01 | 개설일 최솟값·최댓값이 원천과 다름 (`IS DISTINCT FROM`) |
| l5 | I-02 | 아래 한계 참고 |

C-01은 contract의 `allow_empty_days`가 없어서 그대로 썼습니다.

**I-02의 한계:** 쿼리 하나로는 "2회 실행 사이"의 행 수·체크섬을 비교할 수 없습니다. 그 비교는 사다리 스크립트 몫입니다. 그래서 I-02는 재실행 뒤 mart 당일 파티션이 원천에서 다시 계산한 행 수와 합계(날짜 수, 총 행 수)에 일치하는지만 봅니다. DELETE가 빠져 행이 겹쌓이면 이 검사에 걸립니다. 사다리가 2회 실행 비교 자체를 돌리는지는 확인하지 못했습니다.

**사다리로 검증되지 않는 완료 조건 (보고만, 반려 아님):**
- 산출물 생성(정의서, 단위테스트 결과서, `flow_diagram.py` 흐름도)과 템플릿 필수 칸 누락 0
- `.dev/` 반려·개입·비용 로그 기록
- L6 OM 등록 (요구서에서 키트 범위 밖으로 명시)