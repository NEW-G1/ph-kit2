-- 자동 생성: scripts/ladder/gen_dq.py (결정 60). 직접 고치지 않는다.
-- 원본: docs/requirements/mart_season_team_win_rate_checks/l3/
ASSERT NOT {{ params.force_fail }} AS '[DQ-FORCE] 강제 실패 파라미터가 참';

ASSERT NOT EXISTS (
-- C-01: 결과 표의 키(season, team_id)는 고유하다. 겹치는 키를 돌려준다.
SELECT season, team_id, COUNT(*) AS row_cnt
FROM `{{ project }}.{{ dataset_mart }}.mart_season_team_win_rate`
WHERE snapshot_date = DATE('{{ ds }}')
GROUP BY season, team_id
HAVING COUNT(*) > 1
) AS '[C-01] 결과 표의 키(시즌과 팀 ID)는 고유하다';

ASSERT NOT EXISTS (
-- C-02: 승률은 0 이상 1 이하이다. 범위를 벗어나거나 비어 있는 행을 돌려준다.
-- 경기 수는 1 이상이므로 승률이 NULL인 행도 위반으로 본다.
SELECT season, team_id, games_cnt, wins_cnt, win_rate
FROM `{{ project }}.{{ dataset_mart }}.mart_season_team_win_rate`
WHERE snapshot_date = DATE('{{ ds }}')
  AND (win_rate IS NULL OR win_rate < 0 OR win_rate > 1)
) AS '[C-02] 승률은 0 이상 1 이하이다';
