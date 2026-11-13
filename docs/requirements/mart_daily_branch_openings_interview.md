# 일별 신규 지점 개설 건수 마트 인터뷰 기록

- 요청: "bigquery-public-data.fdic_banks의 locations로 일별 신규 지점 개설 건수 마트가 필요해" (요청자 requester1)
- 인터뷰 일자: 2026-11-13
- 조회 방식: `ai-builder` 가장 계정으로 `bq show`(메타데이터)와 집계 쿼리 1건(dry-run 2,910,245 바이트 확인 후 `--maximum_bytes_billed=524288000`으로 실행). 데이터 값은 읽지 않고 개수·최솟값·최댓값만 확인

## 원천 조회 근거

### 메타데이터 (`bq show bigquery-public-data:fdic_banks.locations`)
| 항목 | 값 |
|---|---|
| 유형 | TABLE (뷰 아님) |
| 리전 | US (`source.location`과 같음) |
| 크기 | 22,105,760 바이트, 81,496행 |
| 날짜 파티션 | 없음 |
| 마지막 수정 | 2022-10-17 (lastModifiedTime 1665990638170) |
| 시간 컬럼 | `date_established` DATE, `last_updated` DATE |

### 집계 쿼리 결과 (`locations` 전체 1회 스캔)
| 항목 | 값 |
|---|---|
| 행 수 | 81,496 |
| `branch_fdic_uninum` 고유 수 / NULL 수 | 81,496 / 0 |
| `date_established` NULL 수 | 0 |
| `date_established` 최솟값 / 최댓값 | 1784-01-01 / 2022-10-04 |
| 개설일이 오늘 이후인 행 | 0 |
| 1900-01-01 이전 개설일 행 | 3,961 |
| `date_established` 서로 다른 날짜 수 | 21,391 |
| `main_office` TRUE / NULL | 4,756 / 0 |
| (`fdic_certificate_number`, `branch_number`) 고유 조합 | 81,494 (2건은 번호가 겹치거나 비어 있어 키로 쓰지 않음) |
| `last_updated` 최댓값 | 2022-10-14 |

### 적재 방식 판단
원천 22 MB로 500 MB 이하이고 날짜 파티션이 없으므로 기본안 `snapshot`이다. `incremental`은 날짜 파티션이 없어 고를 수 없다. 원천이 2022-10 이후 갱신되지 않아 매일 같은 값이 쌓인다.

### 개인정보
`docs/architecture/pii_columns.md`는 이 원천을 검토해 개인 식별 컬럼 없음(주소류는 기관·지점 소재지)으로 확정돼 있다. stg·mart에는 `branch_fdic_uninum`, `established_date`, `new_branch_cnt`만 전달한다.

## 질문과 답변
| # | 질문 | AI 기본안 | 요청자 답 |
|---|---|---|---|
| 1 | 마트의 행 단위(grain) | 일자별 전국 1행 | 기본안대로 |
| 2 | 본점(`main_office` TRUE, 4,756건)을 신규 지점 개설로 셀지 | 포함 | 기본안대로 (포함) |
| 3 | 1900년 이전 개설일(3,961건) 처리 | 그대로 포함 | 기본안대로 (포함) |
| 4 | 사무소 유형(`service_type`) 필터 | 전체 유형 포함 | 기본안대로 (전체 포함) |
| 5 | 누가 어떤 의사결정에 쓰나 | (선택지 제시) | 데이터 팀 내부 학습·PoC |
| 6 | 개설이 0건인 날짜 | 개설이 있는 날짜만 행 생성 | 기본안대로 |
| 7 | 갱신 주기·보관 기간 | 매일 snapshot, mart 90일 | 기본안대로 |

## 이 인터뷰로 정해진 것과 AI가 채운 것
- 요청자가 정함: 질문 1~7의 답
- AI가 채움 (요구서 §9 가정 목록에 기록): 지점 식별자는 `branch_fdic_uninum`, 개설일은 `date_established`, 테이블·컬럼 이름과 task 구성, 검사 문장(C-01~C-09, I-01~I-02)
- 테이블 구성은 `design_principles.md` §6 명명과 `task_design.md`(raw > stg > mart, 층마다 게이트 1개)를 따른다

## 사람이 결재 전에 알아 둘 점
- 이 원천은 2022-10 이후 갱신되지 않아, 마트는 매일 같은 과거 일자별 건수를 다시 만든다. "일별 신규"의 날짜 축은 실행일이 아니라 개설일이다
- 1784년부터 1900년 이전까지 개설일 3,961건이 일자 축에 포함된다. 결과 화면에서 오래된 날짜가 보이는 것이 정상이다
- (`fdic_certificate_number`, `branch_number`) 조합은 2건이 겹쳐 쓰지 않았다. 지점 키는 `branch_fdic_uninum` 하나다
