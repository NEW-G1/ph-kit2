-- error_type: null_violation
-- task: stg_branch_opening

-- stg 당일 파티션에서 established_date가 NULL인 행을 돌려준다.
SELECT snapshot_date, branch_fdic_uninum, established_date
FROM `{{ project }}.{{ dataset_stg }}.stg_branch_opening`
WHERE snapshot_date = DATE('{{ ds }}')
  AND established_date IS NULL
