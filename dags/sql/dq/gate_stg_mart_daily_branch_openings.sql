-- 자동 생성: scripts/ladder/gen_dq.py (결정 60). 직접 고치지 않는다.
-- 원본: docs/requirements/mart_daily_branch_openings_checks/l3/
ASSERT NOT {{ params.force_fail }} AS '[DQ-FORCE] 강제 실패 파라미터가 참';

ASSERT NOT EXISTS (
-- stg 당일 파티션의 branch_fdic_uninum은 고유하고 NULL이 없어야 한다. 위반 키를 돌려준다.
SELECT branch_fdic_uninum, COUNT(*) AS row_cnt
FROM `{{ project }}.{{ dataset_stg }}.stg_branch_opening`
WHERE snapshot_date = DATE('{{ ds }}')
GROUP BY branch_fdic_uninum
HAVING branch_fdic_uninum IS NULL OR COUNT(*) > 1
) AS '[C-02] stg_branch_opening의 branch_fdic_uninum은 당일 파티션 안에서 고유하고 NULL이 없다';

ASSERT NOT EXISTS (
-- stg 당일 파티션에서 established_date가 NULL인 행을 돌려준다.
SELECT snapshot_date, branch_fdic_uninum, established_date
FROM `{{ project }}.{{ dataset_stg }}.stg_branch_opening`
WHERE snapshot_date = DATE('{{ ds }}')
  AND established_date IS NULL
) AS '[C-03] stg_branch_opening의 established_date에 NULL이 없다';
