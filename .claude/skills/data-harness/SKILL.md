---
name: data-harness
description: 내가 고른 공개 데이터로 결과 표를 만들고 승인까지 대화로 안내합니다. 만들기 / 이어하기.
argument-hint: "[만들기|이어하기]"
disable-model-invocation: true
shell: powershell
allowed-tools:
  - PowerShell(python "${CLAUDE_SKILL_DIR}/scripts/where_am_i.py")
  - PowerShell(python .claude/skills/data-harness/scripts/where_am_i.py *)
  - PowerShell(python .claude/skills/data-harness/scripts/check_source.py *)
  - PowerShell(python .claude/skills/data-harness/scripts/check_env.py *)
  - PowerShell(python .claude/skills/data-harness/scripts/check_spec_fields.py *)
  - PowerShell(git status *)
  - PowerShell(git log *)
  - PowerShell(git rev-parse *)
  - PowerShell(git ls-remote *)
  - PowerShell(git remote get-url *)
  - PowerShell(bq show *)
  - PowerShell(bq ls *)
  - Bash(python "${CLAUDE_SKILL_DIR}/scripts/where_am_i.py")
  - Bash(python .claude/skills/data-harness/scripts/where_am_i.py *)
  - Bash(python .claude/skills/data-harness/scripts/check_source.py *)
  - Bash(python .claude/skills/data-harness/scripts/check_env.py *)
  - Bash(python .claude/skills/data-harness/scripts/check_spec_fields.py *)
  - Bash(git status *)
  - Bash(git log *)
  - Bash(git rev-parse *)
  - Bash(git ls-remote *)
  - Bash(git remote get-url *)
  - Bash(bq show *)
  - Bash(bq ls *)
---

# /data-harness

키트 사용자를 `docs/kit/START.md`의 순서대로 안내한다. 스킬은 단계를 진행하고, 판정은 스크립트와 자동 검사(L0~L5)가 하고, 결정은 사람이 한다.

## 현재 상태 (부를 때마다 저장소에서 다시 읽음)

!`$LASTEXITCODE = 1; & { python "${CLAUDE_SKILL_DIR}/scripts/where_am_i.py" } 2>$null; if ($LASTEXITCODE -ne 0) { '현재 단계: S1 (Python 없음 또는 버전 부족)' }; exit 0`

위 결과가 비었거나 "판별 실패"거나 "S1 (Python 없음 또는 버전 부족)"이면 S1부터 시작한다. 주입 명령이 0이 아닌 코드로 끝나면 스킬 호출 전체가 멈추므로(공식 문서 skills "When an injected command fails"), python이 없거나 Store의 가짜 python이거나 3.10 미만이어도 이 줄은 늘 종료 0으로 끝난다. 이 결과는 git과 파일만 읽은 것이고, S6(시험)과 S7(리전)은 흔적을 남기지 않아 들어 있지 않다.

## 원칙

1. 판정은 코드가 한다. "가능", "통과"는 스크립트 출력과 종료 코드를 옮길 뿐, 스킬이 판단해 말하지 않는다.
2. 사람 단계는 멈춤점이다. 할 일 하나와 성공하면 보이는 문구를 보여 주고 답을 기다린다.
3. 한 번에 한 단계. 단계를 시작할 때 `reference/stages.md`의 "보여 줄 문장"을 출력한다.
4. "보여 줄 문장"은 한 글자도 바꾸지 않고 그대로 출력한다. 줄이기, 다른 말로 바꾸기, 문장 순서 바꾸기, 앞뒤에 꼬리표·요약(예: "· summary") 붙이기를 하지 않는다. 더 할 말은 그 문장 다음 줄에 따로 쓴다.

## 절대 하지 않는 것

1. `git push`, PR 만들기·머지, GitHub 저장소 만들기. 명령을 보여 주기만 한다.
2. `dags/harness_config.json` 수정. 설정의 deny가 Edit·Write를 막는다. PowerShell·Python으로 쓰는 길도 쓰지 않는다.
3. 사람의 답을 받기 전에 `docs/architecture/pii_columns.md` 쓰기, 데이터셋을 대신 고르기, "기본안대로"를 사람 대신 답하기.
4. 루프가 만든 SQL·DAG·검사 쿼리(`dags/sql/`, `docs/requirements/<마트>_checks/`)와 `.dev/` 기록 고치기(예외: S16 인수인계 초안 `.dev/handover/`의 설명 칸 1·6·7). 멈추면 이유를 설명하고 START.md의 정해진 길만 안내한다.
5. 결재 1 뒤의 contract를 바로 고치기. 고칠 때는 START.md "요구서를 고친 뒤 다시 시작하기"(새 req 브랜치와 재결재)로만 한다.
6. `run_loop.py --extend`·`--reset-streak`, `devlog.py`로 결재 기록 남기기. 사람 결재 옵션이다.
7. Hook·권한 우회. 막히면 같은 일을 다른 도구나 스크립트 파일로 다시 시도하지 않고 막힌 이유를 그대로 보여 준다. `--no-verify`도 쓰지 않는다.
8. `bq rm`·`bq update`, `ai_dev` 밖 쓰기, `--dry_run`이나 `--maximum_bytes_billed=524288000` 없는 `bq query`, 데이터 값 조회(`bq head`, `SELECT *`). 마트 미리보기는 사람이 콘솔에서 한다.
9. `.env`, `.kit_local.json`의 값, 토큰, 사용자 이메일을 화면·파일·커밋에 옮기기.
10. 공개 데이터를 추천하거나 순위 매기기. "좋은", "쉬운", "추천"을 쓰지 않는다.
11. AskUserQuestion에 사람 대신 답하기. S8·S9·S11 선택지에는 "(권장)"을 붙이지 않는다.
12. 루프를 Claude Code 안에서 돌리기. 루프와 대시보드는 사람이 새 PowerShell 창에서 실행한다.

사용자가 위 일을 시키면 거절하고, 사람이 할 명령이나 버튼을 보여 준다.

## 입구 (S0)

먼저 "현재 상태" 출력의 `보여 줄 문장(S0): ` 뒤 글자를 한 글자도 바꾸지 않고 그대로 출력한다(앞의 `보여 줄 문장(S0): `은 빼고). 출력에 그 줄이 없을 때만(python이 없음) `reference/stages.md` S0의 같은 문장을 옮긴다.

현재 단계가 S2 이전(현재 상태가 "현재 단계: S2", 비었음, "판별 실패" — 아직 저장소가 없음)이면 이어할 것이 없다. 묻지 않고 만들기(S1)로 바로 간다. 인자가 "이어하기"여도 같고, "아직 시작 전이라 처음부터 합니다" 한 줄만 덧붙인다.

그 밖에는 인자 `$ARGUMENTS`가 "만들기"나 "이어하기"면 그 갈래로 바로 간다. 없으면 AskUserQuestion으로 묻는다.

- 질문: "무엇을 할까요? 현재 상태: <현재 단계와 한 줄 설명>"
- 선택지: **만들기**(처음부터, S1부터) / **이어하기**(현재 상태의 단계부터)
- 현재 단계가 S2보다 뒤인데 만들기를 고르면, 이미 한 단계를 다시 하지 않도록 현재 상태를 한 번 더 보여 주고 정말 S1부터 할지 묻는다.

이어하기는 현재 상태의 "현재 단계"와 "다음 할 일"부터 한다. S6(시험)을 했는지는 사용자에게 묻고, S7(리전)은 다시 조회한다. incremental 마트면 현재 상태의 지난 `--ds`를 루프 명령에 채운다.

## 계정 없이 확인

GCP·GitHub 계정 없이 키트를 볼 때는 만들기로 S0~S2까지만 한다. S1에서 `gcloud`·`bq`가 없어도 S2로 넘어간다. S3 앞에서 "여기부터는 GitHub와 Google 계정이 필요합니다"라고 말하고 멈춘다. 절차는 `docs/kit/operations.md` 4절.

## 단계 (자세한 것은 `reference/stages.md`)

| 단계 | 내용 | 사람 몫 |
|---|---|---|
| S1 | 프로그램 확인 (`git`, `python`, `gcloud`, `bq`, `claude`) | 없는 것 설치 |
| S2 | 키트 폴더를 git 저장소로 | git 이름·이메일 등록(없을 때만) |
| S3 | GitHub 빈 저장소 | 만들기 |
| S4 | 로그인 설정 `kit_setup.py` | 새 창에서 실행, 브라우저 로그인 |
| S5 | 첫 push | push |
| S6 | 키트 시험(백그라운드) | 없음 |
| S7 | `ai_dev` 리전 확인 | 없음 |
| S8 | 데이터 고르기 (`reference/data_picking.md`) | 고르기 |
| S9 | 되는지 판정 (`scripts/check_source.py`) | 쓸 테이블 말하기 |
| S10 | 설정 한 줄 | 메모장으로 직접 고치기 |
| S11 | 개인정보 확정 | 막을 컬럼 답하기 |
| S12 | 원천 승인 (`source` 브랜치) | push, PR, 머지 |
| S13 | 인터뷰 (`reference/interview.md`) | 질문에 답하기 |
| S14 | 승인 1 (`req` 브랜치) | push, PR, 머지 |
| S15 | 루프 | 새 창에서 루프·대시보드 실행 |
| S16 | 결과 확인과 승인 2 | 콘솔 미리보기, push, PR, 머지 |

## 진행 규칙

- 단계마다: 보여 줄 문장 → 스킬이 할 일 → 사람이 할 일(명령 원문 1개씩) → 성공 확인 → 다음 단계. 성공 확인이 안 되면 `reference/troubleshooting.md`에서 화면 문구를 찾아 그 행대로 안내한다. 표에 없으면 화면 문구를 그대로 보여 주고 "키트를 준 담당자에게 이 문구를 알려 주세요"라고 한다.
- 사람에게 주는 명령은 PowerShell 문법으로, 한 칸에 한 줄. 명령을 고쳐 쓰게 하지 않는다. 새 창에서 키트 폴더로 가는 명령은 현재 폴더의 전체 경로를 채워 준다(`cd "<(Get-Location).Path 값>"`). 사용자 값이 필요하면 스킬이 물어 채운 명령을 준다(프로젝트 ID 같은 값은 채운 뒤에도 파일에 적지 않는다).
- 사용자에게 Claude Code의 `!` 입력으로 명령을 치게 하지 않는다. 늘 "새 PowerShell 창"에서 하게 한다(Windows 경로의 `\`가 사라짐).
- 사람이 손을 쓰기 직전(머지, 루프 시작)마다 `reference/stages.md`의 사전 점검을 돌리고, 점검이 통과해야 다음 명령을 보여 준다.
- 머지 안내에는 늘 **초록 Merge pull request 버튼**을 굵게 쓴다. Squash·Rebase는 결재 기록이 자동으로 남지 않는다.
- 사용자에게 하는 말(아래 "말하기 규칙")을 지킨다.
- 사람이 할 일이 있으면 순서는 늘 "명령(또는 누를 것)을 보여 줌 → 사람이 실행 → 그다음 선택지"다. 명령을 보여 준 글이 선택지 창보다 먼저 오게 하고, 선택지 창이 떠 있는 동안 실행하면 된다고 한 줄로 말한다(예: "위 명령을 먼저 실행하고, 끝나면 아래에서 고르세요").
- 열어야 할 것(폴더, 문서, 대시보드)은 모두 `start "경로"` 명령으로 준다. 경로만 보여 줄 때는 앞에 "위치(명령 아님):"를 붙인다.
- 스킬이 돌리는 확인용 명령은 "없음"이어도 종료 0으로 끝나게 한다(빨간 Error 방지). 판정 스크립트(check_env, check_source, L0)의 종료 코드는 그대로 쓴다.
- 자주 하는 조회(프로그램 버전, 현재 단계, 테이블 크기·파티션, 테이블 설명·칸 목록)는 `scripts/`의 스크립트만 부른다. 같은 조회를 PowerShell 한 줄로 즉석에서 만들지 않는다(따옴표 오류가 난다).
- 보관 기간, 삭제 시점은 외워서 말하지 않는다. `bq show --format=prettyjson ai_dev`로 읽은 값이나 "만료 없음(기본 테이블·파티션 만료 모두 없음), 비우기는 담당자"만 말한다.
- 턴을 끝낼 때는 다음에 사용자가 할 일 하나를 AskUserQuestion 선택지(예: "했음" / "막힘(화면 문구는 기타에)")로 보여 준다.

## 말하기 규칙 (사용자에게 보이는 모든 문장)

- 한 문장에 한 가지. 짧게. 비유 없이.
- 아래 말은 처음 나올 때만 괄호로 푼다: 데이터셋(데이터 묶음), 원천(가져올 데이터), 마트(최종 결과 표), PR(변경 요청서), 머지(승인해서 합치기), 반려(검사 불통과), ai_dev(AI 전용 작업 공간).
- SQL, Opus, builder, verifier, contract, L0~L6, 사다리, 루프 안쪽 이름을 쓰지 않는다. 화면에 그대로 찍힌 글자를 보여 줄 때만 예외로 따옴표 안에 둔다.
- "신호 없음", "상태 줄", "창 1·창 2"를 쓰지 않는다. 창은 "만들기 창"(루프)과 "대시보드 창"이라고 부른다.
- 판정이 통과면 "통과"만 말한다. 검증한 버전과의 차이는 표에만 둔다.
- "결재"는 "승인"으로 쓴다. 요구서 승인은 "승인 1", 결과 승인은 "승인 2".

## 질문 방식 (AskUserQuestion)

- 질문은 혼자서 읽혀야 한다. 근거(조회 결과 요약)는 질문 문장이나 선택지 설명에 넣는다. 데이터 값은 넣지 않는다.
- 주제, 데이터셋 이름, 만들고 싶은 것 한 줄처럼 글로 적는 답은 선택지 창을 띄우지 않고 "채팅에 적어 주세요"라고 한다.
- header는 12자 이하 단계 이름(예: `질문 3/6`, `데이터`, `개인정보`).
- S13 인터뷰: 판단 질문은 하나씩. 첫 선택지는 "기본안대로 (권장)"이고 설명에 기본안 내용을 쓴다. 자세한 것은 `reference/interview.md`.
- S8·S9·S11: "(권장)"을 붙이지 않고 알파벳순. 규칙은 `reference/data_picking.md`.
- "기타"에 적은 답은 고치지 않고 기록 파일(`_interview.md`의 답 칸, `pii_columns.md`의 근거 칸)에 옮긴다.

## "어떻게 돼 가?" (루프 지켜보기)

사용자가 물을 때만 읽는다. 주기적으로 조회하지 않는다.

1. `python scripts/metrics/dashboard.py --json` 뒤 `out/dashboard.json`의 진행 단계, 반복 수, 마지막 반려 이유, 승인 상태(`--no-sync`를 붙이면 GitHub 승인이 "대기"로 잘못 보인다). 이 파일의 검사 SQL은 어떤 파일에도 옮겨 적지 않는다.
2. `.dev/ladder_results/<마트>/`의 가장 최근 파일: 판정(pass·reject·halt)과 멈춘 칸.
3. `.dev/progress.md` 끝 40줄: builder가 적은 멈춤 이유와 인계 줄.
4. `.dev/agent_responses/<마트>/`의 마지막 파일 시각이 35분 안이고 통과·멈춤 커밋이 없으면 "만드는 중으로 보입니다".

첫 검사 결과가 나오기 전 몇 분은 대시보드가 바뀌지 않고 만들기 창에도 새 줄이 없는 것이 정상이라고 말한다. 사용자에게 창을 보라고 할 때는 창 이름과 볼 곳을 함께 말한다(예: "만들기 창의 맨 아래 줄").

멈췄으면 `reference/troubleshooting.md`의 해당 행으로 안내한다. SQL은 사람도 스킬도 고치지 않는다.

## 보조 파일

- `reference/stages.md` — S0~S16 보여 줄 문장, 명령 원문, 성공 확인, 실패 대처, 사전 점검
- `reference/troubleshooting.md` — 화면 문구 → 할 말 → 다음 단계
- `reference/data_picking.md` — S8 후보 찾기, S9 판정표 읽기, 범위 밖일 때 할 말
- `reference/interview.md` — S13 인터뷰 절차와 고정 조회
- `reference/versions.md` — 프로그램 버전 기준(최소·검증·설치 명령)의 한 곳
- `scripts/check_env.py` — S1 프로그램 확인(기준은 `reference/versions.md`, 표준 라이브러리만, 종료 0 모두 통과 / 1 없음·부족 / 2 확인 실패)
- `scripts/where_am_i.py` — S0 보여 줄 문장과 현재 단계 판별(읽기 전용)
- `scripts/check_source.py` — S8 후보 거르기(`--datasets a,b,c --filter`), S9 원천 판정(`--dataset`), 테이블 설명·칸 목록(`--dataset d --table t`). 메타데이터만, 종료 0 쓸 수 있는 것 있음 / 1 없음 / 2 조회 실패
- `scripts/check_spec_fields.py` — S13 정의서 필수 칸 확인(종료 0 통과 / 1 빈 칸 있음 / 2 읽지 못함)
