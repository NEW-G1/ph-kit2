-- error_type: join_missing
-- task: mart_daily_branch_openings

-- mart 당일 new_branch_cnt 합계와 원천 locations 행 수가 다르면 1행을 돌려준다.
SELECT m.mart_sum, o.src_cnt
FROM (
  SELECT IFNULL(SUM(new_branch_cnt), 0) AS mart_sum
  FROM `{{ project }}.{{ dataset_mart }}.mart_daily_branch_openings`
  WHERE snapshot_date = DATE('{{ ds }}')
) AS m
CROSS JOIN (
  SELECT COUNT(*) AS src_cnt
  FROM `bigquery-public-data.fdic_banks.locations`
) AS o
WHERE m.mart_sum != o.src_cnt
