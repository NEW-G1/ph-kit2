# 일별 신규 지점 개설 건수 마트 (mart_daily_branch_openings) 요구서

## 1. 목적과 사용자
- 누가, 어떤 의사결정에 쓰는가: 데이터 팀 내부 학습·PoC. 특정 업무 의사결정은 없고, 파이프라인 검증이 목적이다. 요청자 역할 코드 requester1.

## 2. 원천과 레이어
- 원천 테이블 (bigquery-public-data.fdic_banks): `locations` (FDIC 보험 대상 금융기관의 사무소·지점 목록. 1행 = 사무소 1곳)
- 원천 전제 (2026-11-13 메타데이터 조회와 집계 쿼리로 확인. 근거는 `mart_daily_branch_openings_interview.md`):
  - 갱신 방식: 변경 없음. 테이블 마지막 수정 2022-10-17, 행 `last_updated` 최댓값 2022-10-14. 매일 전체 복사해도 같은 값이 쌓인다
  - 시간 컬럼: `date_established` DATE (지점 개설일, NULL 0건, 범위 1784-01-01 ~ 2022-10-04, 미래 날짜 0건). 날짜 파티션 없음
  - 리전: US (`dags/harness_config.json`의 `source.location`과 같음)
  - 테이블 크기: `locations` 22,105,760 바이트(약 22 MB), 81,496행, 실제 테이블(뷰 아님). 집계 쿼리 dry-run 2,910,245 바이트(약 2.9 MB)로 500 MB 이하
- 적재 방식 (contract `load`): mode `snapshot` (매일 원천 전체를 `snapshot_date` 파티션에 복사. 원천 500 MB 이하이고 날짜 파티션이 없어 incremental은 고를 수 없다)
- 레이어: raw `raw_locations` 신규 / stg `stg_branch_opening` 신규 / mart `mart_daily_branch_openings` 신규. 재사용한 상류 task 없음

## 3. 지표 정의
| 지표 | 계산식 | 단위 | 집계 기준일 | 제외 조건 |
|---|---|---|---|---|
| 신규 지점 개설 건수 (`new_branch_cnt`) | 개설일(`date_established`)이 같은 사무소의 `branch_fdic_uninum` 고유 개수 | 건 | 개설일 (`established_date`) | 없음. 본점(`main_office` TRUE)·모든 `service_type`·1900년 이전 개설일 모두 포함 |

## 4. 품질 기준 (ASSERT로 바꿀 수 있는 문장)
- raw 당일 파티션에 행이 존재한다
- stg의 `branch_fdic_uninum`은 고유하고 NULL이 없다
- stg의 `established_date`에 NULL이 없다
- mart의 `established_date`는 파티션 안에서 고유하다
- mart의 `new_branch_cnt`는 1 이상이다 (개설이 있는 날짜만 행이 있다)

## 5. 갱신 주기와 보관 기간
- 갱신 주기: 매일 snapshot (원천 전체를 당일 `snapshot_date` 파티션에 복사하고 전체 재집계)
- 보관 기간: raw·stg 7일, mart 90일 (`design_principles.md` §2 기본안)

## 6. 난이도 지표 (기록용, 판정에 쓰지 않음)
| task 수 | 조인 수 | ASSERT 수 | 원천 테이블 수 | 재사용한 상류 task 수 |
|---|---|---|---|---|
| 6 (적재 3 + 게이트 3) | 0 | 5 | 1 | 0 |

## 7. 완료 조건 (모두 코드로 판정 가능해야 함)
- [ ] L0 계약·DAG 구조: contract.json 형식 검사 통과(인터뷰 필수 칸·`traces_to` 포함), DAG 파일 문법 검사(실제 import는 배포 때), SQL 파일과 task 1:1, task 목록·의존성이 contract와 일치
- [ ] L1 dry-run: 모든 신규 SQL 문법 통과, 쿼리당 스캔량 ≤ 500 MB (결정 46)
- [ ] L2 개발 데이터셋 실행: ai_dev 데이터셋에서 신규 SQL 전부 성공
- [ ] L3 레이어 게이트: raw/stg/mart 사이 ASSERT C-01 ~ C-05 전부 통과
- [ ] L4 원천 대비 정합성: stg 행 수 = 원천 행 수 (오차 0), mart `new_branch_cnt` 합계 = 원천 행 수 (오차 0), mart 행 수 = 원천 개설일 고유 날짜 수 (오차 0), 날짜별 건수 일치, 개설일 최솟값·최댓값 일치
- [ ] L5 멱등성: 2회 연속 실행 결과의 행 수·체크섬 동일
- [ ] (결재 후) L6 OM 등록: 키트 범위 밖(운영 실행 없음)
- [ ] 산출물: 테이블·컬럼 정의서, 단위테스트 결과서, 데이터 흐름도(`flow_diagram.py`) 생성, 템플릿 필수 칸 누락 0
- [ ] 기록: .dev/ 에 반려·개입·비용 로그 기록

## 8. 사람 결재 지점
- 이 요구서와 contract.json 승인(요구서 PR 머지로 기록, 결정 44), push·PR·머지, 완료 조건 자체의 변경

## 9. 그레인·키, 가정, 범위 밖 (결정 42, 비면 L0 실패)
- 그레인(행 1개의 의미)과 키:
  - mart: 한 `snapshot_date` 파티션 안에서 개설일 1일 = 1행. 키 (`snapshot_date`, `established_date`)
  - stg: 한 `snapshot_date` 파티션 안에서 지점 1곳 = 1행. 키 (`snapshot_date`, `branch_fdic_uninum`)
  - raw: 원천 `locations` 1행 = 1행. 키 (`snapshot_date`, `branch_fdic_uninum`)
- 가정 목록 (AI가 스스로 채운 칸, 근거는 인터뷰 기록의 쿼리):
  - 지점 1곳의 식별자는 `branch_fdic_uninum`이다 (81,496건 모두 고유, NULL 0건)
  - 개설일은 `date_established`이고 NULL이 없어 제외·대체 규칙이 필요 없다
  - 원천은 2022-10 이후 갱신되지 않아 매일 같은 값이 쌓인다. `snapshot_date`는 실행일이며 개설일과 무관하다
  - 원천의 모든 행은 사무소 1곳이며, 같은 사무소가 중복 행으로 들어 있지 않다
  - 0건인 날짜는 행을 만들지 않는다 (요청자 답변)
- 범위 밖 (이번에 하지 않을 것):
  - 주·도시·기관별 등 차원 분해 (요청자가 일자별 전국 1행으로 정함)
  - 폐점·이전·합병 추적 (원천에 폐점일 컬럼이 없음)
  - 개설이 없는 날짜를 0건으로 채우는 달력 보정
  - 지점 주소·기관명 등 상세 컬럼의 stg·mart 전달

## 10. 요구 목록 (contract의 requirements, traces_to가 가리키는 요구 ID)
| 요구 ID | 요구 | 근거 절 (이 요구서의 절 번호 1~9 중 하나. contract `requirements[].section`에는 따옴표 없는 숫자로, 예: 3) |
|---|---|---|
| R-01 | 개설일별 신규 지점 개설 건수(`new_branch_cnt`)를 일자별 전국 1행으로 만든다 | 3 |
| R-02 | 본점, 모든 사무소 유형, 1900년 이전 개설일을 제외하지 않고 센다 | 3 |
| R-03 | 개설이 있는 날짜만 행으로 만든다 (0건인 날짜는 행 없음) | 9 |
| R-04 | mart 건수 합계와 행 수가 원천과 오차 0으로 일치한다 | 4 |
| R-05 | stg의 지점 키는 고유하고 개설일에 NULL이 없다 | 4 |
| R-06 | 같은 날짜로 2회 연속 실행해도 결과가 같다 | 7 |
