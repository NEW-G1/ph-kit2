# 단계별 안내 (S0~S16)

`docs/kit/START.md`의 순서를 단계 번호로 나눈 것이다. 괄호는 START.md 절 번호. 명령은 START.md 원문이고, START.md가 바뀌면 이 파일도 같이 고친다.

단계마다 칸은 같다: **보여 줄 문장**(그대로 보여 줌), **스킬이 할 일**, **사람이 할 일**(명령은 한 칸에 한 줄, PowerShell), **성공 확인**, **실패하면**.

"보여 줄 문장"과 스킬이 사용자에게 하는 말은 SKILL.md "말하기 규칙"을 따른다. "보여 줄 문장"은 한 글자도 바꾸지 않고 그대로 출력한다(앞뒤에 덧붙이지 않음, SKILL.md 원칙 4).

새 창에서 키트 폴더로 가는 `cd`는 스킬이 현재 폴더의 전체 경로(`(Get-Location).Path`)를 채워 준다. 모양: `cd "C:\Users\사용자\ph-kit"`. START.md의 `cd $HOME\ph-kit`을 그대로 주지 않는다(폴더 이름·위치가 다를 수 있음).

---

## S0 입구

- 보여 줄 문장: 당신이 고른 공개 데이터로 결과 표를 만듭니다. AI가 만들고, 코드가 검사하고, 당신이 승인합니다(대시보드에는 '결재'로 표시). 끝나면 결과 표, 진행 화면(대시보드), 설명 문서를 받습니다. 당신이 할 일은 로그인, 데이터 고르기, 파일 한 줄 고치기, 개인정보 확인, 승인 3번입니다.
- 스킬이 할 일: 위 문장은 `where_am_i.py`가 출력한 것을 그대로 옮긴다(python이 없어 출력에 없을 때만 여기서. 두 곳이 같은지 시험이 본다). 현재 상태(where_am_i 출력)를 한 줄로 요약하고 만들기 / 이어하기를 묻는다(SKILL.md "입구"). 현재 단계가 S2 이전(S2, 비었음, 판별 실패)이면 묻지 않고 S1로 간다.
- 성공 확인: 고른 갈래의 첫 단계 문장이 나옴.
- 실패하면: 현재 상태가 "판별 실패"면 S1부터.

## S1 프로그램 확인 (1절)

- 보여 줄 문장: 필요한 프로그램이 있는지, 버전이 맞는지 봅니다. 없거나 낮은 것만 설치합니다.
- 스킬이 할 일:
  1. 현재 상태가 "S1 (Python 없음 또는 버전 부족)"이면 확인 스크립트를 돌릴 수 없다. `reference/versions.md` "설치" 절 코드 블록의 python 설치 명령 한 줄을 글자 그대로 주고 사람이 할 일 2·3으로 간다.
  2. 그 밖에는 아래를 돌리고 나온 표를 그대로 보인다. 판정은 스크립트 출력만 옮긴다(스킬이 버전을 비교하지 않는다).

```
python .claude/skills/data-harness/scripts/check_env.py
```

  3. 종료 0이면 S2로. 종료 1이면 표 아래 "설치할 것"의 줄만 사람에게 준다(판정이 "없음"·"부족"인 것만). 종료 2면 `reference/troubleshooting.md`의 설치 행.
  4. "통과(검증 밖)"·"통과(권장 미만)"은 통과다. 사용자에게는 "통과"만 말한다(검증한 버전과의 차이는 표에만 있다).
  5. 설치 명령을 줄 때 먼저 말한다: "관리자 확인 창이 뜨면 **예**를 누르세요(Git, Google Cloud SDK)", "Google Cloud SDK는 약 5분 걸립니다. 끝날 때까지 창을 닫지 마세요", "Google Cloud SDK 하나를 설치하면 `gcloud`와 `bq`가 둘 다 들어옵니다", "Claude Code를 설치할 때 `.local\bin is not in your PATH`가 나와도 괜찮습니다. 그다음 줄이 그 경로를 넣는 명령입니다". 설치할 것에 있는 것만 말한다.
- 사람이 할 일:
  1. **새 PowerShell 창**에서 받은 설치 명령을 한 줄씩 실행한다(`winget`이 "인식되지 않음"이면 `reference/versions.md`의 "막힐 때 (winget)").
  2. 설치가 끝나면 **PowerShell 창을 모두 닫고 새로 연다.** Claude Code도 `/exit`로 닫고 키트 폴더에서 다시 `claude`를 켠 뒤 `/data-harness` > 이어하기.
  3. 다시 켠 뒤 스킬이 위 확인을 한 번 더 돌린다.
- 성공 확인: `check_env.py` 종료 0. 계정 없이 확인(SKILL.md)일 때는 `gcloud`·`bq`가 "없음"이어도 S2로 간다.
- 실패하면: `python`을 치면 `Python` 한 단어만 나오거나 Microsoft Store가 열림 → Windows의 가짜 python(앱 실행 별칭). `gcloud`가 "running scripts is disabled"로 막힘 → 실행 정책. 둘 다 `reference/troubleshooting.md`.

## S2 키트 준비 (2~3절 3번)

- 보여 줄 문장: 이 폴더에 변경 기록이 남게 합니다(git).
- 스킬이 할 일:
  1. 이미 저장소면(`.git` 있음, 커밋 1개 이상) 건너뛴다.
  2. git 이름·이메일이 등록돼 있는지 **있음/없음만** 본다. 값은 화면에 옮기지 않는다.

```
if (git config user.email) { "있음" } else { "없음" }; exit 0
```

  "없음"이어도 종료 0으로 끝난다(빨간 Error가 뜨지 않게).

  3. 있으면 스킬이 직접 돌린다.

```
git init -b main
```

```
git add .
```

```
git commit -m "키트 첫 커밋"
```

- 사람이 할 일: 이름·이메일이 없을 때만 새 PowerShell 창에서 아래 두 줄(따옴표 안만 본인 GitHub 아이디와 GitHub 이메일로 바꿈. 값은 채팅에 적지 않는다).

```
git config --global user.name "GitHub아이디"
```

```
git config --global user.email "GitHub이메일"
```

- 성공 확인: `git log --oneline -1`에 "키트 첫 커밋".
- 실패하면: 폴더가 이미 저장소면 건너뜀. 커밋이 이름·이메일 없음으로 실패하면 위 두 줄 뒤 다시.

계정 없이 확인은 여기서 끝난다: "여기부터는 GitHub와 Google 계정이 필요합니다. 계정 없이 확인은 여기까지입니다."

## S3 GitHub 저장소 (3절 1~2번)

- 보여 줄 문장: 승인은 GitHub에서 합니다. 빈 저장소를 하나 만듭니다.
- 스킬이 할 일: 현재 폴더 이름을 보여 준다(`Split-Path -Leaf (Get-Location)`). 저장소 이름은 이 이름과 같아야 한다(S4의 설정 스크립트가 폴더 이름으로 연결함).
- 사람이 할 일: 브라우저로 https://github.com 에 로그인 > 오른쪽 위 **+** > **New repository**. Repository name은 폴더 이름과 같게, **Private**, "Add a README file"은 **체크하지 않음**, **Create repository**.
- 성공 확인: 사용자가 "만들었음"이라고 답함.
- 실패하면: 이름이 폴더와 다르게 만들어졌으면 폴더 이름으로 다시 만든다.

## S4 로그인 설정 (3절 4번)

- 보여 줄 문장: Google 계정으로 로그인합니다. AI는 따로 만든 계정(ai-builder)으로 일하고, AI 전용 작업 공간(ai_dev)에만 쓸 수 있습니다.
- 사람이 할 일: **새 PowerShell 창**에서 키트 폴더로 간 뒤 실행(`cd`는 스킬이 전체 경로를 채워 줌). `GCP 프로젝트 ID:`를 물으면 담당자가 안내문으로 보낸 프로젝트 ID를 붙여 넣는다(소문자로 시작, 소문자·숫자·하이픈 6~30자. 형식 예: `my-project-id`). 안내문이 없으면 담당자에게 먼저 물어본다. "GitHub 아이디"를 물으면 입력. 브라우저가 열리면 **권한을 받은 본인 Google 계정**을 고르고 허용.

```
python scripts/setup/kit_setup.py
```

- 성공 확인: 그 창 끝에 `BigQuery 신원: ai-builder 확인`과 `설정 완료`. 사용자가 "됐음"이라고 하면 스킬이 다시 본다:
  - `.kit_local.json` 파일이 있는지(값은 읽어 옮기지 않음): `Test-Path .kit_local.json`
  - `git config core.hooksPath`가 `.githooks`인지
  - 설정 스크립트가 바꾼 Claude Code 설정(`.claude/settings.local.json`의 env)은 지금 세션에 바로 들어오지 않는다. **Claude Code를 `/exit`로 닫고 다시 켠 뒤 `/data-harness` > 이어하기**로 오게 한다.
- 실패하면: 창 끝에 `BigQuery 신원: (ai-builder 아님)`이 나오면 한 번 더 실행. 권한 오류면 화면 문구를 담당자에게.

## S5 올리기 (3절 5번)

- 보여 줄 문장: 만든 GitHub 저장소에 이 폴더를 올립니다.
- 사람이 할 일: S4와 같은 창에서. 로그인 창이 뜨면 GitHub에 로그인.

```
git push -u origin main
```

- 성공 확인: 스킬이 `git ls-remote origin main`으로 원격 main이 있는지 보고, `git remote get-url origin`의 끝 이름이 폴더 이름과 같은지 본다(주소를 파일에 적지 않음).
- 실패하면: 거절 → 저장소 이름이 폴더 이름과 같은지, 로그인한 GitHub 계정이 맞는지. origin 주소가 만든 저장소와 다르면 "올린 곳의 주소가 만든 저장소와 다릅니다"라고 말하고 담당자에게.

## S6 키트 시험 (4절)

- 보여 줄 문장: 이 PC에서 도구가 잘 도는지 시험합니다. 약 2분 걸리니 그동안 다음 단계로 갑니다.
- 스킬이 할 일: 도구 설치 뒤 시험을 **백그라운드**로 돌리고, 기다리는 동안 S7로 간다. 끝나면 마지막 줄을 보여 준다.

```
python -m pip install -r requirements-dev.txt
```

```
python -m pytest tests/ -q -n auto
```

- 성공 확인: 마지막 줄에 `passed`, `failed` 없음. `skipped` 수십 개는 정상(브라우저 시험).
- 실패하면: 실패 줄을 보여 주고 멈춘다. 스킬이 고치지 않는다. 담당자에게 그 줄을 보내게 한다.

## S7 내 ai_dev 리전

- 보여 줄 문장: 데이터는 저장된 지역(리전)이 있습니다. 같은 지역의 데이터만 쓸 수 있어 먼저 확인합니다.
- 스킬이 할 일: 아래 출력에서 `"location"` 값만 읽어 보여 준다. 다른 칸은 옮기지 않는다.

```
bq show --format=prettyjson ai_dev
```

- 성공 확인: 리전 값(예: US).
- 실패하면: 인증·권한 오류 → S4로(설정 스크립트 다시, Claude Code 다시 켜기).

## S8 데이터 고르기 (부록 A-1)

- 보여 줄 문장: 관심 있는 주제를 말해 주세요. 누구나 쓸 수 있는 Google 공개 데이터에서 이 키트로 쓸 수 있는 것만 찾아 보여 드립니다. 고르는 건 당신입니다.
- 스킬이 할 일: 주제는 "채팅에 적어 주세요"로 받는다(선택지 창을 띄우지 않음). 후보를 찾기 전에 "후보를 찾는 데 1~2분 걸립니다"라고 먼저 말한다. `reference/data_picking.md` 1절대로 `check_source.py --datasets ... --filter`를 한 번 돌려 같은 리전이고 500 MB 이하 테이블이 1개 이상인 후보만 알파벳순으로, 한글 설명과 함께 보인다. 뺀 개수는 이유마다 한 줄. 추천하지 않는다.
- 사람이 할 일: 후보 중 하나를 고른다. 콘솔에서 직접 찾아도 된다(START 부록 A-1).
- 성공 확인: 사람이 데이터셋 이름 1개를 말함.
- 실패하면: 후보가 없으면 다른 단어로 다시. 목록 조회가 막히면 START 부록 A-1의 콘솔 절차로 고르게 하고 그 이름을 받는다.

## S9 되는지 판정 (부록 A-2)

- 보여 줄 문장: 고른 데이터를 쓸 수 있는지 코드가 확인합니다. 데이터 내용은 보지 않고 크기와 구조만 봅니다.
- 스킬이 할 일: 판정 스크립트를 돌리고 표를 그대로 보인다(`reference/data_picking.md` 2절). 이름만 연도·숫자로 다른 표가 많으면 2절 "이름만 다른 표 묶기"대로 한 줄로 묶고(예: "gsod1929 ~ gsod2024 (76개, 연도마다 한 표)"), 고르면 그중 하나(한 해)를 쓴다고 알려 준다. 표 아래에 쓸 수 있는 테이블의 한글 설명, 날짜 칸, 값의 뜻과 주의점을 덧붙인다. 테이블 하나의 설명·칸 목록은 같은 스크립트의 `--table 테이블이름`으로만 본다.

```
python .claude/skills/data-harness/scripts/check_source.py --dataset 데이터셋이름
```

- 사람이 할 일: 표를 보고 쓸 테이블을 말한다(적재 방식이 snapshot인 가능·조건부 중에서. 500 MB 넘는 표는 이 안내의 범위 밖).
- 성공 확인: 종료 0, 쓸 테이블의 적재 방식이 snapshot이고 판정이 가능 또는 조건부.
- 실패하면: 종료 1(모두 불가) → `reference/data_picking.md` 3절의 문장과 선택지. 종료 2(조회 실패) → "데이터 정보를 읽지 못했습니다. 데이터 문제가 아니라 연결이나 권한 문제입니다." S4 다시 또는 담당자.

## S10 설정 한 줄 (부록 A-3)

- 보여 줄 문장: 가져올 데이터 이름을 설정 파일에 적습니다. 이 파일은 사람만 고칠 수 있습니다. 메모장에서 따옴표 안의 이름 하나만 바꿔 주세요.
- 스킬이 할 일: `dags/harness_config.json`의 `"source"` 줄을 읽어 바꾸기 전·후 줄을 보여 준다(`"dataset"` 값만 다름, `"location"`은 S9 표의 리전과 같아야 함). 파일은 고치지 않는다.
- 사람이 할 일: 새 PowerShell 창(키트 폴더)에서 메모장으로 열어 `"dataset"` 값만 바꾸고 Ctrl+S, 닫기.

```
notepad dags\harness_config.json
```

- 성공 확인: 스킬이 형식 확인을 돌려 `원천 설정 형식 통과: bigquery-public-data.<고른 이름>`을 본다.

```
python -c "import sys; sys.path.insert(0, 'scripts/ladder'); import harness_config; harness_config.load(); print('원천 설정 형식 통과:', harness_config.source_prefix())"
```

- 실패하면: JSONDecodeError나 "키는 [...]여야 함" → 바꾼 줄을 전·후 줄과 한 글자씩 비교해 보여 주고 사람이 다시 고친다.

## S11 개인정보 확정 (부록 A-4)

- 보여 줄 문장: 이름, 이메일, 주소, 전화번호, 정확한 위치처럼 사람을 알아볼 수 있는 칸은 결과로 넘기지 않습니다. 막을 칸을 골라 주세요.
- 스킬이 할 일: S9 판정표의 "개인정보 후보" 칸(컬럼 이름만)을 AskUserQuestion 여러 개 선택으로 묻는다(SKILL.md 질문 방식, 권장 표시 없음). 선택지는 `테이블.컬럼`과 "없음 (개인정보로 볼 컬럼이 없다)". 후보가 4개를 넘으면 테이블별로 나눠 한 번에 최대 4질문, 질문마다 후보 3개 + "이 테이블에는 없음".
  - "없음"과 컬럼을 함께 고르면 파일을 쓰지 않고 다시 묻는다(`(없음)` 행과 컬럼 행을 함께 두면 L0가 멈춤).
  - "기타"로 후보 밖 컬럼을 더하면 `INFORMATION_SCHEMA.COLUMNS` 조회로 있는지 확인한 뒤 쓴다.
  - **답을 받은 뒤에만** `docs/architecture/pii_columns.md`를 고친다: "검토한 원천" 줄을 설정의 source와 같게, 표에는 고른 컬럼만(근거 칸에 사람의 답), 모두 "없음"이면 `| (없음) | | 모든 테이블의 컬럼 이름 검토, 개인 식별 컬럼 없음 |` 행 하나, 표 아래 "확인 기록" 줄은 새 원천을 확인한 방법과 날짜로. 표 형식(칸 순서, 백틱)은 바꾸지 않는다.
- 성공 확인: 스킬이 돌려 `원천 설정과 개인정보 목록 형식 통과: ...`.

```
python -c "import sys; sys.path.insert(0, 'scripts/ladder'); import harness_config, l0_contract; harness_config.load(); l0_contract.load_pii(); print('원천 설정과 개인정보 목록 형식 통과:', harness_config.source_prefix())"
```

- 실패하면: "두 종류를 함께 둠" → `(없음)` 행과 컬럼 행 중 하나만. "검토한 원천 ... 다름" → 검토한 원천 줄을 설정과 같게.

## S12 원천 승인 (부록 A-5)

- 보여 줄 문장: 방금 바꾼 설정을 GitHub에서 승인합니다.
- 스킬이 할 일:
  1. `docs/kit/source_checklist.md`의 칸을 채운다: 원천·리전·테이블 크기·날짜 파티션·개인정보 검토는 S9·S11 결과로, 데이터 소유자 승인 칸은 "공개 데이터, 요청자 확인", 운영 비용 칸은 "키트 범위 밖(운영 실행 없음)". 데이터 값은 적지 않는다. 다른 파일은 고치지 않는다.
  2. 사전 점검: `git status --porcelain`에서 바뀐 파일이 `dags/harness_config.json`, `docs/architecture/pii_columns.md`, `docs/kit/source_checklist.md` 세 개(그리고 `.dev/` 기록)뿐인지. 그 밖의 파일이 있으면 멈추고 목록과 "이 파일은 어느 단계에서 생겼는지"를 보여 준다.
  3. 브랜치와 커밋:

```
git checkout -b source
```

```
git add -A
```

```
git commit -m "원천 변경"
```

- 사람이 할 일(이 순서로 안내): ① 새 PowerShell 창에서 push, ② GitHub에서 **Compare & pull request** > **Create pull request** > **Files changed**에서 세 파일 훑어보기, ③ 꼭 초록 **Merge pull request** > **Confirm merge**. 커밋·push 안내 전에는 머지를 말하지 않는다.

```
git push -u origin source
```

- 성공 확인: 사람이 "머지했음" → 스킬이 맞춘다.

```
git checkout main
```

```
git pull origin main
```

  - `git log origin/main -1 --format=%P`의 부모가 2개인지(머지 커밋). 1개면 "이번 승인은 기록이 자동으로 남지 않습니다"라고 말하고 담당자에게 알리게 한다.
  - main의 `dags/harness_config.json` source가 고른 데이터셋인지.

## S13 인터뷰 (5절, 부록 A-6)

- 보여 줄 문장: 무엇을 보고 싶은지 한 줄로 말해 주세요(예: "OO별 OO 수를 보고 싶다"). AI가 데이터를 살펴보고 기본안을 제안합니다. 괜찮으면 "기본안대로"를 고르세요.
- 스킬이 할 일: `reference/interview.md`대로 고정 조회 → 질문 → 파일 3개(`docs/requirements/<마트>.md`, `<마트>.contract.json`, `<마트>_interview.md`) → L0 통과. 인터뷰 중 쓸 테이블이 바뀌면 S9 판정을 다시 돌린다. 만들 마트의 예는 컬럼 이름에서 3개를 보여 주되 고르는 것은 사람이다(incremental이면 일 단위 지표인 예만).
- 성공 확인: 파일 3개, 아래 L0 종료 0.

```
python scripts/ladder/l0_contract.py docs/requirements/마트이름.contract.json
```

  이어서 정의서에 빈 칸이 남지 않는지 본다(커밋 전, 종료 0이어야 S14로 감).

```
python .claude/skills/data-harness/scripts/check_spec_fields.py docs/requirements/마트이름.contract.json
```

- 실패하면: 저장 때 Hook의 L0 오류가 돌아오면 그 자리에서 고친다(결재 1 전이라 허용). 빈 칸(종료 1)은 나온 칸을 채우고 새로 채운 한글 이름을 사용자에게 한 번 확인받는다. 커밋 전에 두 확인을 한 번 더 돌린다.

## S14 승인 1 (6절)

- 보여 줄 문장: 인터뷰로 만든 요구서를 승인합니다(승인 1). 이후 AI는 이 요구서대로만 만듭니다.
- 스킬이 할 일: 사전 점검(`git status --porcelain`이 `docs/requirements/`와 `.dev/` 밖 파일 없음, 현재 브랜치 main, S13의 L0와 `check_spec_fields.py`가 종료 0). 그 뒤:

```
git checkout -b req
```

```
git add -A
```

```
git commit -m "요구서"
```

  커밋이 pre-commit의 L0로 막히면 오류 줄로 contract를 고치고 다시 커밋한다(`--no-verify` 쓰지 않음).
- 사람이 할 일: 새 PowerShell 창에서 push, GitHub에서 **Compare & pull request** > **Create pull request** > **Files changed**에서 요구서 파일 훑어보기 > 초록 **Merge pull request** > **Confirm merge**.

```
git push -u origin req
```

- 성공 확인: "머지했음" → 스킬이 `git checkout main`, `git pull origin main`, 머지 커밋 부모 2개 확인, main의 contract가 origin/main과 같은지. 결재 기록은 다음 단계 루프가 시작할 때 자동으로 남는다.

## S15 루프 (7절)

- 보여 줄 문장: 이제 AI가 만들고 코드가 6번 검사합니다. 통과하지 못하면 AI가 다시 만듭니다. 시간이 걸리므로 새 창 두 개에서 실행하고, 대시보드로 진행을 봅니다.
- 사전 점검(통과해야 명령을 보여 줌):
  1. `git status --porcelain`이 비었는지. 아니면 파일 목록을 보여 준다(`docs/requirements` 안이면 S14처럼 PR로, 그 밖이면 담당자).
  2. main이 origin/main과 같은지(`git rev-parse main origin/main`).
  3. 작업 브랜치 이름: `build`가 없으면 `build`. 있고 그 브랜치의 iteration 0 커밋 뒤에 origin/main의 contract가 바뀌었으면 `build2`, `build3`처럼 새 이름(START "요구서를 고친 뒤 다시 시작하기" 4번). 브랜치가 없어도 확인 명령은 종료 0으로 끝낸다.
  4. contract `load.mode`가 incremental이면 `--ds`를 채운다. 이어하기면 where_am_i의 "지난 --ds". 처음이면 인터뷰에서 정한 날짜(원천에 데이터가 있는 날짜).
  5. `bq ls ai_dev`로 만들 테이블(contract의 raw·stg·mart 이름)과 같은 이름이 있는지 본다. 있으면 "AI 전용 작업 공간에 같은 이름의 예전 표가 있습니다. AI는 표를 지울 수 없습니다. 담당자에게 비워 달라고 요청해 주세요"라고 말하고 멈춘다.
  6. "AI가 일하는 동안 당신의 Claude 사용량이 쓰입니다."
- 스킬이 할 일: `git checkout -b build`(또는 3번의 이름).
- 사람이 할 일: **새 PowerShell 창 두 개**(만들기 창, 대시보드 창). 두 창 모두 먼저 창 제목 명령, 그다음 스킬이 전체 경로를 채운 `cd`를 실행한다.
  - **만들기 창**(루프). "만들기 창은 끝날 때까지 닫지 마세요. `PS`로 시작하는 줄이 다시 보이면 Claude Code에 '끝났음'만 적어 주세요"라고 말한다(통과·멈춤은 스킬이 기록으로 판단한다):

```
$Host.UI.RawUI.WindowTitle = "만들기 창 - 닫지 마세요"
```

```
python scripts/loop/run_loop.py
```

    incremental이면 스킬이 날짜를 채운 줄을 준다(예: `python scripts/loop/run_loop.py --ds 2026-11-10`).
  - **대시보드 창**: 아래 순서 그대로. 마지막 줄(`--watch`)은 끝나지 않고 기록이 바뀔 때마다 화면을 다시 만든다(끌 때 Ctrl+C). 그래서 화면 열기(`start`)를 그 앞에 둔다.

```
$Host.UI.RawUI.WindowTitle = "대시보드 창"
```

```
python scripts/metrics/dashboard.py
```

```
start out\dashboard.html
```

```
python scripts/metrics/dashboard.py --watch
```

  사용자에게 말한다: "첫 검사 결과가 나오기 전 몇 분은 대시보드가 바뀌지 않는 것이 정상입니다. 처음 볼 곳은 '검사 사다리' 표입니다."

  대시보드에서 볼 것 3가지(사용자에게 이렇게 말함):
  1. 지금 어느 단계인지
  2. 검사를 통과 못 해 다시 만든 횟수
  3. 결재 1·2(승인) 상태

- 성공 확인: 사용자가 "끝났음"이라고 하면 스킬이 기록으로 판단한다(SKILL.md "루프 지켜보기" 1·2번). 통과면 커밋 `loop: <마트> v<N> 통과`가 있다. 사용자에게 통과·멈춤을 판단하게 하거나 루프 끝에 나온 인수인계 명령을 치게 하지 않는다(S16에서 스킬이 한다). 사용자가 "어떻게 돼 가?"라고 하면 SKILL.md "루프 지켜보기".
- 실패하면: `멈춤:` 줄 → `reference/troubleshooting.md`. 사용량 한도·네트워크면 풀린 뒤 같은 명령(같은 `--ds`). 창에 `HARNESS_ROLE`이 남았다고 거절하면 루프 메시지의 `Remove-Item Env:HARNESS_ROLE`.

## S16 결과 확인과 승인 2 (8~9절)

- 보여 줄 문장: AI가 만든 결과 표를 직접 보고 설명 문서를 확인한 뒤 승인합니다(승인 2). 이것으로 끝입니다.
- 스킬이 할 일 (1) 인수인계 초안: 루프는 초안을 만들지 않고 만드는 명령만 알려 준다. 스킬이 build 브랜치에서 차례로 한다.
  1. `python scripts/handover/make_facts.py --mart <마트>` → `.dev/handover/<브랜치>.md`(사실 칸 2·3·4·5·8을 코드가 채움)
  2. `.claude/rules/handover.md`대로 설명 칸(1 한 줄 요약, 6 운영 방법, 7 주의점)만 채운다. 사실 칸은 한 글자도 고치지 않는다. 데이터 값은 넣지 않는다
  3. `python scripts/handover/make_facts.py --mart <마트> --check`가 종료 0인지
  4. `git add .dev/handover/<브랜치>.md` 뒤 `git commit -m "인수인계 초안: <마트>"`(build 브랜치). 그다음 사람이 push한다
- 스킬이 할 일 (2) 납품 문서: 생성기를 돌리고 문서마다 여는 명령을 `start "경로"`로 준다(경로만 보일 때는 "위치(명령 아님):"). 문서 핵심을 채팅에 먼저 요약하고(데이터 값 없음), 문서마다 볼 곳 하나와 확인할 질문 하나를 말한다:
  - 테이블 정의서(결과 표의 칸 설명): 볼 곳 "컬럼 정보", 질문 "칸마다 한글 이름과 설명이 있나요?"
  - 흐름도(데이터가 지나가는 길): 볼 곳 원천에서 결과 표까지의 순서, 질문 "내가 고른 데이터에서 시작하나요?"
  - 단위테스트 결과서(검사 결과): 볼 곳 검사 결과 칸, 질문 "통과하지 못한 검사가 있나요?"
  - 인수인계 초안(다음 담당자를 위한 설명): 볼 곳 "7 주의점", 질문 "알아 둘 주의점을 읽었나요?"

```
python scripts/deliverables/flow_diagram.py
```

```
python scripts/deliverables/table_spec.py
```

```
python scripts/deliverables/unit_test_report.py
```

- 사람이 할 일:
  1. 콘솔(`start "https://console.cloud.google.com/bigquery"`)에서 안내 창(Gemini)이 뜨면 X로 닫고, 프로젝트 > `ai_dev` > `mart_`로 시작하는 테이블 > **미리보기**(START 8절 4번). 쿼리 버튼은 누르지 않는다.
  2. `start "out\deliverables"`로 문서를 연다(스킬이 전체 경로를 채워 줌).
  3. 승인 2 전 확인 목록 3개: ① 결과 표 미리보기의 숫자가 말이 된다 ② 정의서에 빈 칸이 없다 ③ 인수인계 초안의 주의점을 읽었다. 하나라도 아니면 머지하지 않고 스킬에 말한다.
  4. 새 PowerShell 창에서 push, GitHub에서 **Compare & pull request** > **Create pull request** > **Files changed**에서 바뀐 파일과 `.dev/handover/` 훑어보기 > 초록 **Merge pull request** > **Confirm merge**.

```
git push -u origin build
```

- 성공 확인: "머지했음" → 스킬이 `git checkout main`, `git pull origin main`, 머지 커밋 부모 2개, `python scripts/metrics/dashboard.py --json` 뒤(`--no-sync`를 붙이지 않는다) `out/dashboard.json`에서 결재 2가 완료로 보이는지. 사용자에게는 "대시보드의 '운영'과 'L6' 칸이 대기인 것은 정상입니다"라고 말한다(키트 범위 밖).
- 보관 기간을 물으면: `bq show --format=prettyjson ai_dev`에서 `defaultTableExpirationMs`·`defaultPartitionExpirationMs`만 읽는다. 둘 다 없으면 "`ai_dev`는 만료 없음(기본 테이블·파티션 만료 모두 없음), 비우기는 담당자가 합니다", 있으면 그 값(밀리초)을 날짜 수로 바꿔 말한다.
- 실패하면: 승인 2가 대기 → `git pull`을 했는지, Squash·Rebase 머지였는지(troubleshooting).
- 끝: START "끝나고 담당자에게 보낼 것"(`python scripts/metrics/dashboard.py --json` 뒤 `out\dashboard.json`)을 안내한다.
