-- stg_branch_opening: raw_locations 당일 파티션에서 지점 키와 개설일만 골라 지점 1곳 = 1행으로 만든다.
-- 제외 조건 없음 (본점, 모든 service_type, 1900년 이전 개설일 포함). 상세 컬럼은 전달하지 않는다.
-- 적재 방식: snapshot (contract load.mode). 멱등 3문장 패턴 (sql_rules.md §1)

-- (1) 테이블이 없을 때만 생성
CREATE TABLE IF NOT EXISTS `{{ project }}.{{ dataset_stg }}.stg_branch_opening`
(
  snapshot_date DATE OPTIONS (description = '실행 날짜 (Airflow ds). 파티션 키'),
  branch_fdic_uninum STRING OPTIONS (description = 'FDIC가 지점에 부여한 고유 식별 번호. 지점 1곳의 키'),
  established_date DATE OPTIONS (description = '지점 개설일 (원천 date_established). 본점과 모든 사무소 유형 포함')
)
PARTITION BY snapshot_date
CLUSTER BY established_date, branch_fdic_uninum
OPTIONS (
  partition_expiration_days = 7,
  description = '지점 개설 정제. 소스: raw_locations (원천 bigquery-public-data.fdic_banks.locations). 한 snapshot_date 파티션 안에서 지점 1곳 = 1행'
);

-- (2) 당일 파티션 삭제
DELETE FROM `{{ project }}.{{ dataset_stg }}.stg_branch_opening`
WHERE snapshot_date = DATE('{{ ds }}');

-- (3) 당일 파티션 적재
INSERT INTO `{{ project }}.{{ dataset_stg }}.stg_branch_opening`
  (snapshot_date, branch_fdic_uninum, established_date)
SELECT
  DATE('{{ ds }}') AS snapshot_date,
  branch_fdic_uninum,
  date_established AS established_date
FROM `{{ project }}.{{ dataset_raw }}.raw_locations`
WHERE snapshot_date = DATE('{{ ds }}');
