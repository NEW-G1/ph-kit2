-- error_type: duplicate_rows
-- task: mart_season_team_win_rate

-- C-01: 결과 표의 키(season, team_id)는 고유하다. 겹치는 키를 돌려준다.
SELECT season, team_id, COUNT(*) AS row_cnt
FROM `{{ project }}.{{ dataset_mart }}.mart_season_team_win_rate`
WHERE snapshot_date = DATE('{{ ds }}')
GROUP BY season, team_id
HAVING COUNT(*) > 1
