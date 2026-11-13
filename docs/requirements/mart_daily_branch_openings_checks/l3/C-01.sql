-- error_type: null_violation
-- task: raw_locations

-- raw_locations 당일 파티션에 행이 1개 이상 있어야 한다. 0행이면 위반 1행을 돌려준다.
SELECT COUNT(*) AS row_cnt
FROM `{{ project }}.{{ dataset_raw }}.raw_locations`
WHERE snapshot_date = DATE('{{ ds }}')
HAVING COUNT(*) = 0
