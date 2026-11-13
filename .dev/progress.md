# 진행 기록

## 요구서 — mart_daily_branch_openings
docs/requirements/mart_daily_branch_openings.md

## 작업 목록 — mart_daily_branch_openings

마트 실행 반복 1/5, 연속 없음 0/3

| # | 작업 | 상태 | 반복 | 최근 반려 |
|---|---|---|---|---|
| 1 | raw_locations (raw) | 통과 | 0 | — |
| 2 | stg_branch_opening (stg) | 통과 | 0 | — |
| 3 | mart_daily_branch_openings (mart) | 통과 | 0 | — |

## builder iteration 1 — mart_daily_branch_openings (2026-11-13)
- 과거 반려: .dev/rejections.jsonl 에 이 마트 반려 없음 (첫 시도)
- load.mode: snapshot → sql_rules.md §1 패턴 적용. learned 규칙 없음
- 변경 파일
  - dags/sql/raw/raw_locations.sql (신규) — 명시적 DDL(contract 31컬럼·타입·설명), 7일 만료, 원천 전체를 컬럼 이름으로 복사
  - dags/sql/stg/stg_branch_opening.sql (신규) — branch_fdic_uninum, date_established→established_date. 제외 조건 없음, 7일 만료
  - dags/sql/mart/mart_daily_branch_openings.sql (신규) — established_date별 COUNT(DISTINCT branch_fdic_uninum), 90일 만료. 0건 날짜 행 없음
  - dags/harness_daily.py — UPSTREAM을 contract dag.tasks 6개와 맞춤
- 실행 결과
  - Write 뒤 Hook(after_edit) 오류 출력 없음
  - bq show(원천 스키마 확인)와 사다리 스크립트 직접 실행은 권한 승인 필요로 실행하지 않음. bq query 실행 없음 (비용 0)
  - 원천 컬럼 타입은 contract 기준으로 적음. 원천 타입과 다르면 L1/L2에서 드러남
- 지시 문구 발견: 없음
- 판정: 사다리 종료 코드에 맡김 (자체 완료 판단 안 함)

## 직전 반복 인계
- [루프 mart_daily_branch_openings] iteration 1: 신호 없음 (STATUS 줄 없음, 반려 아님)
- [루프 mart_daily_branch_openings] iteration 1: 사다리 통과
