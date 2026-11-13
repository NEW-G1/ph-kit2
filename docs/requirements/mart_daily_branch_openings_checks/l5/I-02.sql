-- error_type: idempotency_break
-- task: mart_daily_branch_openings

-- 2회 연속 실행 뒤 mart 당일 파티션이 원천에서 다시 계산한 값과 행 수·건수 합계가 다르면 1행을 돌려준다.
-- 재실행에서 DELETE가 빠져 행이 겹쌓이면 행 수와 합계가 원천 기대값보다 커진다.
-- (2회 실행 사이의 행 수·체크섬 비교 자체는 사다리 스크립트가 한다)
SELECT m.mart_rows, m.mart_sum, o.src_days, o.src_cnt
FROM (
  SELECT COUNT(*) AS mart_rows, IFNULL(SUM(new_branch_cnt), 0) AS mart_sum
  FROM `{{ project }}.{{ dataset_mart }}.mart_daily_branch_openings`
  WHERE snapshot_date = DATE('{{ ds }}')
) AS m
CROSS JOIN (
  SELECT COUNT(DISTINCT date_established) AS src_days, COUNT(*) AS src_cnt
  FROM `bigquery-public-data.fdic_banks.locations`
) AS o
WHERE m.mart_rows != o.src_days
   OR m.mart_sum != o.src_cnt
