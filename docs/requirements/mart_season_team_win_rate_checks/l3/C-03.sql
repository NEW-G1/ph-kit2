-- error_type: duplicate_rows
-- task: stg_team_game

-- C-03: 정리 표의 키(season, team_id, game_seq)는 고유하고 team_id는 비어 있지 않다.
-- 키가 겹치는 행과 team_id가 NULL 또는 빈 글자인 행을 돌려준다.
SELECT 'duplicate_key' AS violation, CAST(season AS STRING) AS season, team_id, CAST(game_seq AS STRING) AS game_seq, COUNT(*) AS row_cnt
FROM `{{ project }}.{{ dataset_stg }}.stg_team_game`
WHERE snapshot_date = DATE('{{ ds }}')
GROUP BY season, team_id, game_seq
HAVING COUNT(*) > 1

UNION ALL

SELECT 'empty_team_id' AS violation, CAST(season AS STRING) AS season, team_id, CAST(game_seq AS STRING) AS game_seq, 1 AS row_cnt
FROM `{{ project }}.{{ dataset_stg }}.stg_team_game`
WHERE snapshot_date = DATE('{{ ds }}')
  AND (team_id IS NULL OR TRIM(team_id) = '')
