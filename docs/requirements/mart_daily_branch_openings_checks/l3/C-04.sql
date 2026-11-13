-- error_type: duplicate_rows
-- task: mart_daily_branch_openings

-- mart 당일 파티션에서 established_date가 둘 이상인 날짜를 돌려준다.
SELECT established_date, COUNT(*) AS row_cnt
FROM `{{ project }}.{{ dataset_mart }}.mart_daily_branch_openings`
WHERE snapshot_date = DATE('{{ ds }}')
GROUP BY established_date
HAVING COUNT(*) > 1
