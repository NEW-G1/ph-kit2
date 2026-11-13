-- error_type: join_missing
-- task: mart_daily_branch_openings

-- mart 당일 행 수와 원천 date_established의 서로 다른 날짜 수가 다르면 1행을 돌려준다.
SELECT m.mart_rows, o.src_days
FROM (
  SELECT COUNT(*) AS mart_rows
  FROM `{{ project }}.{{ dataset_mart }}.mart_daily_branch_openings`
  WHERE snapshot_date = DATE('{{ ds }}')
) AS m
CROSS JOIN (
  SELECT COUNT(DISTINCT date_established) AS src_days
  FROM `bigquery-public-data.fdic_banks.locations`
) AS o
WHERE m.mart_rows != o.src_days
