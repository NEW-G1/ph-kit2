검증 쿼리 8개를 `docs/requirements/mart_season_team_win_rate_checks/` 아래에 썼습니다. 판정은 하지 않았고, 쿼리는 실행하지 않았습니다. contract의 L3·L4·L5 항목은 모두 파일로 썼고, 빠진 항목은 없습니다.

| 단계 | 파일 | 내용 |
|---|---|---|
| l3 | `C-01.sql` | 마트에서 (season, team_id)가 겹치는 키를 돌려줍니다. |
| l3 | `C-02.sql` | 승률이 0~1 밖이거나 NULL인 행을 돌려줍니다. |
| l3 | `C-03.sql` | stg에서 (season, team_id, game_seq)가 겹치는 키와 team_id가 NULL이거나 빈 문자열인 행을 돌려줍니다. task는 `stg_team_game`입니다. |
| l4 | `C-04.sql` | 마트 경기 수 합계가 원천에서 팀 ID가 있는 줄 수와 다르면 한 줄을 돌려줍니다. |
| l4 | `C-05.sql` | 마트 이긴 경기 수 합계가 원천에서 팀 ID가 있고 `win`이 참인 줄 수와 다르면 한 줄을 돌려줍니다. |
| l4 | `C-06.sql` | 마트의 시즌·팀 조합 수가 원천의 고유 조합 수와 다르면 한 줄을 돌려줍니다. |
| l4 | `I-01.sql` | 이긴 수와 진 수의 합이 경기 수와 다른 행을 돌려줍니다. |
| l5 | `I-02.sql` | 2회 실행 뒤 마트 행 수와 경기 수 합계가 원천 기준과 다르면 한 줄을 돌려줍니다. |

머리말 `error_type`은 위반 성격에 맞춰 정했습니다. C-01·C-03은 `duplicate_rows`, C-02는 `range_violation`, I-02는 `idempotency_break`입니다. L4의 네 쿼리는 `runtime_error`로 두었습니다. `devlog.py`의 ERROR_TYPES에 원천 불일치에 딱 맞는 값이 없었습니다.

요구서와 contract에 적혀 있지 않아 제가 가정한 것이 네 가지 있습니다.
- **`snapshot_date` 컬럼:** contract의 `tables[].columns`에는 `snapshot_date`가 없습니다. 하지만 snapshot 모드의 `sql_rules.md` §1 패턴이 파티션 키로 요구하므로, 모든 층에서 `snapshot_date = DATE('{{ ds }}')`로 읽도록 썼습니다. builder가 이 컬럼을 두지 않으면 L3·L4가 실행 오류로 실패합니다.
- **빈 팀 ID 기준:** "팀 ID가 있는 줄"을 `team_id IS NOT NULL AND TRIM(team_id) != ''`로 정했습니다. 요구서에 NULL인지 빈 문자열인지 적혀 있지 않아서입니다.
- **원천 직접 조회:** 원천 경로는 contract의 `sources`에 있는 값 그대로 썼습니다.
- **합계 비교:** 비교하는 값이 모두 INT64 개수라 NUMERIC 변환은 쓰지 않았습니다.

사다리로 검증되지 않는 완료 조건은 두 가지입니다.
- **I-02의 체크섬 비교:** 쿼리 하나로는 첫 실행과 둘째 실행의 체크섬을 비교할 수 없습니다. 행 수·체크섬의 2회 비교는 `l5_idem.py`가 하고, `I-02.sql`은 이중 적재 흔적만 봅니다.
- **R-03의 "뺀 건수를 기록한다":** contract에는 그 건수를 담을 테이블이나 컬럼이 없어, 검사할 방법이 없습니다. 제외 자체는 C-04~C-06이 확인합니다.

이 둘과 L6(OM 등록), 산출물, 로그 항목은 사람이 결재 때 봐야 합니다.