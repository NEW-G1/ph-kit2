-- 자동 생성: scripts/ladder/gen_dq.py (결정 60). 직접 고치지 않는다.
-- 원본: docs/requirements/mart_daily_branch_openings_checks/l3/
ASSERT NOT {{ params.force_fail }} AS '[DQ-FORCE] 강제 실패 파라미터가 참';

ASSERT NOT EXISTS (
-- raw_locations 당일 파티션에 행이 1개 이상 있어야 한다. 0행이면 위반 1행을 돌려준다.
SELECT COUNT(*) AS row_cnt
FROM `{{ project }}.{{ dataset_raw }}.raw_locations`
WHERE snapshot_date = DATE('{{ ds }}')
HAVING COUNT(*) = 0
) AS '[C-01] raw_locations 당일 파티션에 행이 1개 이상 존재한다';
