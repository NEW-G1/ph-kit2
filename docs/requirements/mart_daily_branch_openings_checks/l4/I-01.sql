-- error_type: range_violation
-- task: mart_daily_branch_openings

-- mart의 개설일 최솟값·최댓값이 원천과 다르면 1행을 돌려준다. 날짜 필터가 걸렸는지 확인한다.
-- mart가 빈 경우 최솟값·최댓값이 NULL이므로 IS DISTINCT FROM으로 위반 처리한다.
SELECT m.min_d AS mart_min, o.min_d AS src_min, m.max_d AS mart_max, o.max_d AS src_max
FROM (
  SELECT MIN(established_date) AS min_d, MAX(established_date) AS max_d
  FROM `{{ project }}.{{ dataset_mart }}.mart_daily_branch_openings`
  WHERE snapshot_date = DATE('{{ ds }}')
) AS m
CROSS JOIN (
  SELECT MIN(date_established) AS min_d, MAX(date_established) AS max_d
  FROM `bigquery-public-data.fdic_banks.locations`
) AS o
WHERE m.min_d IS DISTINCT FROM o.min_d
   OR m.max_d IS DISTINCT FROM o.max_d
