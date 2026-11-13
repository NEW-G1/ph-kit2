-- error_type: join_missing
-- task: mart_daily_branch_openings

-- 날짜별 new_branch_cnt가 원천 집계와 다르거나 한쪽에만 있는 날짜를 돌려준다.
SELECT
  COALESCE(m.established_date, o.established_date) AS established_date,
  m.new_branch_cnt AS mart_cnt,
  o.src_cnt
FROM (
  SELECT established_date, new_branch_cnt
  FROM `{{ project }}.{{ dataset_mart }}.mart_daily_branch_openings`
  WHERE snapshot_date = DATE('{{ ds }}')
) AS m
FULL OUTER JOIN (
  SELECT date_established AS established_date, COUNT(DISTINCT branch_fdic_uninum) AS src_cnt
  FROM `bigquery-public-data.fdic_banks.locations`
  GROUP BY date_established
) AS o
  ON m.established_date = o.established_date
WHERE m.established_date IS NULL
   OR o.established_date IS NULL
   OR m.new_branch_cnt != o.src_cnt
