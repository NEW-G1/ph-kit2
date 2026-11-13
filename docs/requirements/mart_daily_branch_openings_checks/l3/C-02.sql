-- error_type: duplicate_rows
-- task: stg_branch_opening

-- stg 당일 파티션의 branch_fdic_uninum은 고유하고 NULL이 없어야 한다. 위반 키를 돌려준다.
SELECT branch_fdic_uninum, COUNT(*) AS row_cnt
FROM `{{ project }}.{{ dataset_stg }}.stg_branch_opening`
WHERE snapshot_date = DATE('{{ ds }}')
GROUP BY branch_fdic_uninum
HAVING branch_fdic_uninum IS NULL OR COUNT(*) > 1
