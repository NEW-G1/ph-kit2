-- error_type: range_violation
-- task: mart_daily_branch_openings

-- mart 당일 파티션에서 new_branch_cnt가 1 미만이거나 NULL인 행을 돌려준다.
SELECT snapshot_date, established_date, new_branch_cnt
FROM `{{ project }}.{{ dataset_mart }}.mart_daily_branch_openings`
WHERE snapshot_date = DATE('{{ ds }}')
  AND (new_branch_cnt IS NULL OR new_branch_cnt < 1)
