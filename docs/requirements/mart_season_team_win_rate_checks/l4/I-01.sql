-- error_type: runtime_error
-- task: mart_season_team_win_rate

-- I-01: 이긴 경기 수 + 진 경기 수 = 치른 경기 수. 다른 행을 돌려준다(NULL도 위반).
SELECT season, team_id, games_cnt, wins_cnt, losses_cnt
FROM `{{ project }}.{{ dataset_mart }}.mart_season_team_win_rate`
WHERE snapshot_date = DATE('{{ ds }}')
  AND (wins_cnt + losses_cnt) IS DISTINCT FROM games_cnt
