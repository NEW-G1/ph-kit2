-- mart_daily_branch_openings: stg_branch_opening 당일 파티션을 개설일별로 집계해 개설일 1일 = 1행으로 만든다.
-- 개설이 있는 날짜만 행이 생긴다 (달력 보정 없음). 제외 조건 없음.
-- 적재 방식: snapshot (contract load.mode). 멱등 3문장 패턴 (sql_rules.md §1)

-- (1) 테이블이 없을 때만 생성
CREATE TABLE IF NOT EXISTS `{{ project }}.{{ dataset_mart }}.mart_daily_branch_openings`
(
  snapshot_date DATE OPTIONS (description = '실행 날짜 (Airflow ds). 파티션 키'),
  established_date DATE OPTIONS (description = '지점 개설일. 이 날짜에 개설된 지점을 센다'),
  new_branch_cnt INT64 OPTIONS (description = '그 개설일에 개설된 지점의 고유 개수. 본점과 모든 사무소 유형, 1900년 이전 포함. 제외 조건 없음')
)
PARTITION BY snapshot_date
CLUSTER BY established_date
OPTIONS (
  partition_expiration_days = 90,
  description = '일별 신규 지점 개설 건수. 소스: stg_branch_opening (원천 bigquery-public-data.fdic_banks.locations). 한 snapshot_date 파티션 안에서 개설일 1일 = 1행 (개설이 있는 날짜만)'
);

-- (2) 당일 파티션 삭제
DELETE FROM `{{ project }}.{{ dataset_mart }}.mart_daily_branch_openings`
WHERE snapshot_date = DATE('{{ ds }}');

-- (3) 당일 파티션 적재
INSERT INTO `{{ project }}.{{ dataset_mart }}.mart_daily_branch_openings`
  (snapshot_date, established_date, new_branch_cnt)
SELECT
  DATE('{{ ds }}') AS snapshot_date,
  established_date,
  COUNT(DISTINCT branch_fdic_uninum) AS new_branch_cnt
FROM `{{ project }}.{{ dataset_stg }}.stg_branch_opening`
WHERE snapshot_date = DATE('{{ ds }}')
GROUP BY established_date;
