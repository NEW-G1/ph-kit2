# 인수인계 — mart_daily_branch_openings (build, 2026-11-13)

> 사실 칸(2·3·4·5·8)은 `scripts/handover/make_facts.py` 출력이다. 고치거나 추측해서 채우지 않는다.
> 설명 칸(1·6·7)만 builder가 쓴다 (`.claude/rules/handover.md`).

- contract_version: 1
- 생성 시각: 2026-11-13T12:36:46+09:00
- 기준 커밋: e6468cbed3351cb04b2dda8936444621e1093366

## 1. 한 줄 요약
FDIC 사무소 목록(`bigquery-public-data.fdic_banks.locations`)에서 개설일별 신규 지점 개설 건수(`new_branch_cnt`)를 일자별 전국 1행으로 만드는 일별 마트(`mart_daily_branch_openings`)다. 데이터 팀 내부 학습·PoC용이며 특정 업무 의사결정은 없고 파이프라인 검증이 목적이다 (요구서 §1).

## 2. 바뀐 것  ← 코드
기준점 `18c2e492` 대비 (git diff 18c2e492...HEAD). contract: 기준점 v1 → 지금 v1

| 구분 | 이름 | 변경 |
|---|---|---|
| 테이블 | thelook_raw.raw_locations | 그대로 |
| 테이블 | thelook_stg.stg_branch_opening | 그대로 |
| 테이블 | thelook_mart.mart_daily_branch_openings | 그대로 |
| task | raw_locations | 그대로 |
| task | gate_raw_mart_daily_branch_openings | 그대로 |
| task | stg_branch_opening | 그대로 |
| task | gate_stg_mart_daily_branch_openings | 그대로 |
| task | mart_daily_branch_openings | 그대로 |
| task | gate_mart_mart_daily_branch_openings | 그대로 |
| 파일 | dags/harness_daily.py | 변경 |
| 파일 | dags/sql/dq/gate_mart_mart_daily_branch_openings.sql | 신규 |
| 파일 | dags/sql/dq/gate_raw_mart_daily_branch_openings.sql | 신규 |
| 파일 | dags/sql/dq/gate_stg_mart_daily_branch_openings.sql | 신규 |
| 파일 | dags/sql/mart/mart_daily_branch_openings.sql | 신규 |
| 파일 | dags/sql/raw/raw_locations.sql | 신규 |
| 파일 | dags/sql/stg/stg_branch_opening.sql | 신규 |
| 파일 | docs/requirements/mart_daily_branch_openings_checks/l3/C-01.sql | 신규 |
| 파일 | docs/requirements/mart_daily_branch_openings_checks/l3/C-02.sql | 신규 |
| 파일 | docs/requirements/mart_daily_branch_openings_checks/l3/C-03.sql | 신규 |
| 파일 | docs/requirements/mart_daily_branch_openings_checks/l3/C-04.sql | 신규 |
| 파일 | docs/requirements/mart_daily_branch_openings_checks/l3/C-05.sql | 신규 |
| 파일 | docs/requirements/mart_daily_branch_openings_checks/l4/C-06.sql | 신규 |
| 파일 | docs/requirements/mart_daily_branch_openings_checks/l4/C-07.sql | 신규 |
| 파일 | docs/requirements/mart_daily_branch_openings_checks/l4/C-08.sql | 신규 |
| 파일 | docs/requirements/mart_daily_branch_openings_checks/l4/C-09.sql | 신규 |
| 파일 | docs/requirements/mart_daily_branch_openings_checks/l4/I-01.sql | 신규 |
| 파일 | docs/requirements/mart_daily_branch_openings_checks/l5/I-02.sql | 신규 |

## 3. 데이터 흐름  ← 코드 (DAG 의존성)
원천: bigquery-public-data.fdic_banks.locations

- (원천) → raw_locations
- raw_locations → stg_branch_opening
- stg_branch_opening → mart_daily_branch_openings

게이트: gate_raw_mart_daily_branch_openings (raw 층, 상류 raw_locations), gate_stg_mart_daily_branch_openings (stg 층, 상류 stg_branch_opening), gate_mart_mart_daily_branch_openings (mart 층, 상류 mart_daily_branch_openings)

OM 리니지 링크는 결재 후 L6 통과 시 docs/handover/ 반영 때 추가한다.

## 4. 검증 결과  ← 코드 (검증 사다리)
contract v1의 사다리 반복 1회

| 반복 | 판정 | task별 |
|---|---|---|
| 1 | pass | raw_locations pass, stg_branch_opening pass, mart_daily_branch_openings pass |

마지막 통과 반복 1 (task 3/3 통과, ds 2026-11-13)

| 단계 | 결과 | 수치 |
|---|---|---|
| L0 계약·DAG 구조 | 통과 | load_tasks 3, gate_tasks 3, tables 3, checks 11, traces 11 |
| L1 dry-run | 통과 | 스캔량 합 0 bytes (여러 문장 스크립트는 하한값) |
| L2 ai_dev 실행 | 통과 | 실행한 테이블 mart_daily_branch_openings, raw_locations, stg_branch_opening |
| L3 레이어 게이트 | 통과 | 검사 C-01, C-02, C-03, C-04, C-05 위반 0행 |
| L4 정합성 | 통과 | 검사 C-06, C-07, C-08, C-09, I-01 위반 0행 |
| L5 멱등성 | 통과 | 재실행 전후 행 수·체크섬 같음 (ds 파티션 행 수 합 184,383), 검사 I-02 위반 0행 |
| L6 OM 등록 | 결재 후 | 운영 DAG·OM 에이전트 실행 뒤 판정 |

### 비용  ← 코드 (.dev/cost.jsonl)
실행 1회 (RUN-001)

| 역할 | 호출 수 | 비용 합(USD, 정가 환산 추정) | 입력 토큰 | 출력 토큰 | bq 바이트 |
|---|---|---|---|---|---|
| builder | 1 | 0.6790 | 30 | 9,509 | 92,191,558 |
| verifier | 1 | 0.2221 | 8 | 6,187 | 0 |

## 5. 반려 이력  ← 코드 (.dev/rejections.jsonl)
`.dev/rejections.jsonl` (해결 = 같은 task가 그 뒤 반복에서 통과한 첫 반복, ladder_result 기준)

반려 없음

**개입 기록** (`.dev/interventions.jsonl`, 같은 마트, 해석 없이 그대로)

| ID | 시각 | 종류 | 단계 | 대상 | 분 | 메모 |
|---|---|---|---|---|---|---|
| H-0001 | 2026-11-13T11:15:23+09:00 | approval | approval_1 | PR 머지 18c2e49 | 2 | git 머지 기록에서 자동 |

## 6. 운영 방법
- **갱신 방식**: 매일 snapshot. 원천 전체를 당일 `snapshot_date`(= 실행일 ds) 파티션에 복사하고 전체를 다시 집계한다 (contract `load.mode` = `snapshot`, `schedule.refresh`).
- **실행 순서** (contract `dag`, DAG 파일 `dags/harness_daily.py`): `raw_locations` → `gate_raw_mart_daily_branch_openings` → `stg_branch_opening` → `gate_stg_mart_daily_branch_openings` → `mart_daily_branch_openings` → `gate_mart_mart_daily_branch_openings`. 층마다 게이트가 하나씩 있고 상류가 끝나야 다음 task가 돈다.
- **재실행**: 같은 날짜(ds)로 다시 돌려도 결과가 같다. 같은 ds로 2회 연속 실행한 뒤 mart의 행 수와 `new_branch_cnt` 체크섬이 같아야 한다 (R-06, 검사 I-02). 재실행은 당일 `snapshot_date` 파티션을 다시 만드는 방식이다.
- **장애 대응 기준**: 게이트가 실패하면 그 아래 task는 돌지 않는다. 게이트 검사는 C-01 ~ C-05(요구서 §4)이며, 어느 게이트가 어떤 문장을 어겼는지 보고 해당 층의 task부터 확인한다. 정합성 검사 C-06 ~ C-09, I-01은 원천과 mart를 대조하는 L4 검사다.
- **보관 기간**: raw·stg 7일, mart 90일 (요구서 §5).
- **운영 DAG 실행과 OM 등록(L6)**: 이 키트 범위 밖이다. 결재 후 별도로 진행한다 (요구서 §7).

## 7. 주의점과 알려진 데이터 특성
- **원천이 더 이상 갱신되지 않는다**: 테이블 마지막 수정 2022-10-17, 행 `last_updated` 최댓값 2022-10-14. 그래서 마트는 매일 같은 과거 일자별 건수를 다시 만든다 (요구서 §2, 인터뷰 기록).
- **날짜 축은 개설일이다**: `established_date`가 일자 축이고 `snapshot_date`는 실행일일 뿐 개설일과 무관하다. "일별 신규"는 실행일 기준이 아니다.
- **오래된 날짜가 정상이다**: 개설일 범위는 1784-01-01 ~ 2022-10-04이고 1900년 이전 개설일이 3,961건 있다. 결과에 옛날 날짜가 보이는 것이 정상이며 제외하지 않는다 (R-02).
- **제외 조건이 없다**: 본점(`main_office` TRUE, 4,756건), 모든 `service_type`, 1900년 이전 개설일을 모두 센다. 본점이 개설 건수에 포함되는 것은 요청자가 정한 것이다.
- **0건인 날짜는 행이 없다**: 달력 보정을 하지 않는다 (R-03, 요구서 §9). 개설일 서로 다른 날짜는 21,391개, 원천은 81,496행이다.
- **키는 `branch_fdic_uninum` 하나다**: 81,496건이 모두 고유하고 NULL이 없다. (`fdic_certificate_number`, `branch_number`) 조합은 2건이 겹쳐 키로 쓰지 않았다.
- **범위 밖**: 주·도시·기관별 차원 분해, 폐점·이전·합병 추적(원천에 폐점일 컬럼 없음), 지점 주소·기관명 등 상세 컬럼의 stg·mart 전달. 이런 요구는 이 마트로 답할 수 없고 새 요구서가 필요하다.
- **개인정보**: 개인 식별 컬럼 없음으로 확정돼 있다(주소류는 기관·지점 소재지). stg·mart에는 `branch_fdic_uninum`, `established_date`, `new_branch_cnt`만 전달한다 (`pii_columns.md`, 인터뷰 기록).

## 8. 링크  ← 코드
- OM 테이블: 결재 후 L6 통과 시 docs/handover/ 반영 때 추가
- 납품 산출물: 아직 없음 (out/deliverables/)
- 요구서: docs/requirements/mart_daily_branch_openings.md
- contract: docs/requirements/mart_daily_branch_openings.contract.json
- 인터뷰 기록: docs/requirements/mart_daily_branch_openings_interview.md
