-- error_type: join_missing
-- task: stg_branch_opening

-- stg 당일 행 수와 원천 locations 행 수가 다르면 1행을 돌려준다.
SELECT s.stg_cnt, o.src_cnt
FROM (
  SELECT COUNT(*) AS stg_cnt
  FROM `{{ project }}.{{ dataset_stg }}.stg_branch_opening`
  WHERE snapshot_date = DATE('{{ ds }}')
) AS s
CROSS JOIN (
  SELECT COUNT(*) AS src_cnt
  FROM `bigquery-public-data.fdic_banks.locations`
) AS o
WHERE s.stg_cnt != o.src_cnt
