-- 자동 생성: scripts/ladder/gen_dq.py (결정 60). 직접 고치지 않는다.
-- 원본: docs/requirements/mart_daily_branch_openings_checks/l3/
ASSERT NOT {{ params.force_fail }} AS '[DQ-FORCE] 강제 실패 파라미터가 참';

ASSERT NOT EXISTS (
-- mart 당일 파티션에서 established_date가 둘 이상인 날짜를 돌려준다.
SELECT established_date, COUNT(*) AS row_cnt
FROM `{{ project }}.{{ dataset_mart }}.mart_daily_branch_openings`
WHERE snapshot_date = DATE('{{ ds }}')
GROUP BY established_date
HAVING COUNT(*) > 1
) AS '[C-04] mart_daily_branch_openings의 established_date는 당일 파티션 안에서 고유하다';

ASSERT NOT EXISTS (
-- mart 당일 파티션에서 new_branch_cnt가 1 미만이거나 NULL인 행을 돌려준다.
SELECT snapshot_date, established_date, new_branch_cnt
FROM `{{ project }}.{{ dataset_mart }}.mart_daily_branch_openings`
WHERE snapshot_date = DATE('{{ ds }}')
  AND (new_branch_cnt IS NULL OR new_branch_cnt < 1)
) AS '[C-05] mart_daily_branch_openings의 new_branch_cnt는 모든 행에서 1 이상이다';
