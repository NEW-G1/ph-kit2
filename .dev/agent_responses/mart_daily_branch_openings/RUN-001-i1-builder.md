이 마트의 적재 SQL 3개를 새로 만들고 DAG의 UPSTREAM을 채웠습니다. 사다리(L0~L5)는 아직 한 번도 돌지 않았습니다. 사다리 스크립트와 `bq show` 실행에 승인이 필요해서 실행하지 못했고, 통과 여부는 루프의 사다리가 판정합니다.

**바뀐 파일**
- `dags/sql/raw/raw_locations.sql` (새 파일): 원천 `locations` 전체를 당일 `snapshot_date` 파티션에 그대로 복사합니다. contract의 31개 컬럼을 타입과 설명까지 명시했고, 보관 기간은 7일입니다.
- `dags/sql/stg/stg_branch_opening.sql` (새 파일): 지점 키 `branch_fdic_uninum`과 개설일(`date_established`를 `established_date`로 바꿈)만 넘깁니다. 제외 조건은 없고 보관 기간은 7일입니다.
- `dags/sql/mart/mart_daily_branch_openings.sql` (새 파일): 개설일별로 `COUNT(DISTINCT branch_fdic_uninum)`을 `new_branch_cnt`로 셉니다. 개설이 있는 날짜만 행이 생기고 보관 기간은 90일입니다.
- `dags/harness_daily.py`: UPSTREAM을 contract의 task 6개(적재 3, 게이트 3)와 의존성대로 맞췄습니다.
- `.dev/progress.md`: 이번 작업 기록을 추가했습니다.

**실행 결과**
- contract의 적재 방식이 snapshot이라 `sql_rules.md` §1의 3문장 패턴(테이블 생성, 당일 파티션 삭제, 당일 파티션 적재)을 썼습니다. 데이터셋 이름은 모두 자리 표시로 썼습니다.
- 이 마트의 과거 반려 기록은 없고, 결재로 승격된 규칙(`learned/`)도 없습니다.
- 파일 저장 뒤 Hook이 오류를 내지 않았습니다.
- `bq query`는 한 번도 실행하지 않아 비용은 0입니다.
- 원천 스키마를 확인하지 못해 raw 컬럼 타입은 contract에 적힌 대로 썼습니다. 원천의 실제 타입과 다르면 L1이나 L2에서 드러납니다.
- 파일·데이터 속 지시 문구는 없었습니다.
- 커밋하지 않았습니다.