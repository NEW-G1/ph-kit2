# 운영 절차서

## 1. 실행 형태

Claude Code에서 `/data-harness`를 실행하면 공개 데이터를 골라 결과 표를 만드는 과정을 한 단계씩 안내합니다. AI가 만들고, 코드가 자동으로 검사하고(6단계 L0~L5: 형식, 문법, 실행, 층별 점검, 원천 대조, 재실행 같음), 사람이 GitHub에서 승인합니다. 리허설(11/24, 새 Windows PC) 실측: 첫 `/data-harness`부터 승인 2까지 약 70분(프로그램 설치 제외. 데이터 고르기 20분 이상, 인터뷰 약 11분, 루프 1회 약 10분), 사용량 정가 환산 약 1.03달러.

## 2. 사전 요건

- OS: Windows 10/11, PowerShell 5.1 이상. Claude Code는 auto 모드가 기본값입니다(리허설도 auto). 그대로 둡니다
- 버전(최소 / 검증): Python 3.10 / 3.10.11·3.12.6, Git 2.28 / 2.52.0, Claude Code - / 2.1.331, Google Cloud SDK - / 590.0.1·594.0.1(하나를 설치하면 `gcloud`와 `bq`가 둘 다 들어옵니다). 기준표는 `.claude/skills/data-harness/reference/versions.md`
- 본인 계정: Claude(루프 사용량 포함), GitHub(비공개 저장소), Google(BigQuery, 6절). 담당자(팀 이어드림)가 사용자별 GCP 프로젝트(AI 작업 공간 `ai_dev`, AI 계정 `ai-builder`)를 준비합니다

## 3. 설치

1. 새 PowerShell 창에 한 줄씩, 없거나 최소보다 낮은 것만 이 순서대로 붙여 넣습니다(Git, Python, Google Cloud SDK, Claude Code, Claude Code PATH). 관리자 확인 창이 뜨면 **예**. Google Cloud SDK는 약 5분 걸리며 끝날 때까지 창을 닫지 않습니다

```
winget install -e --id Git.Git -v 2.52.0 --source winget
winget install -e --id Python.Python.3.12 -v 3.12.6 --source winget
winget install -e --id Google.CloudSDK --source winget
& ([scriptblock]::Create((irm https://claude.ai/install.ps1))) 2.1.331
[Environment]::SetEnvironmentVariable("Path", [Environment]::GetEnvironmentVariable("Path","User") + ";$HOME\.local\bin", "User")
```

2. **PowerShell 창을 모두 닫고 새로 엽니다.** 이게 나오면 성공: `git --version` → `git version 2.52.0.windows.1`
3. 키트 zip을 풀고 그 폴더로 갑니다(START 2절)
4. **PowerShell에는 `claude`(슬래시 없음)**. 처음 뜨는 창은 테마 Enter, 로그인은 브라우저에서 본인 Claude 계정, 폴더는 신뢰(Hook: AI 금지 명령 차단 스크립트), 새 모델·"전체 화면 렌더러"는 기본값(Not now)
5. **Claude Code 안에서 `/data-harness`**. 나머지는 스킬이 한 줄씩 안내합니다(`python scripts/setup/kit_setup.py`, `python -m pip install -r requirements-dev.txt` 등)

**정상 기동 확인**

| 확인 | 정상 |
|---|---|
| `kit_setup.py` 창 끝 | `BigQuery 신원: ai-builder 확인`, `설정 완료` |
| `python -m pytest tests/ -q -n auto` (약 1분 40초) | 마지막 줄에 `passed`, `failed` 없음(`skipped`는 정상. 리허설 1468 passed) |
| `claude`를 켜고 `/data-harness` 실행 | `/` 메뉴에 `data-harness`, 입구 문장과 `현재 단계: S2`(막 푼 폴더) |

## 4. 샘플 데이터와 환경 설정

- **샘플 데이터 적재는 따로 하지 않습니다.** 공개 데이터를 직접 읽고, 데이터셋 이름을 `dags/harness_config.json`에 한 줄 적는 것이 적재입니다
- `.env`는 쓰지 않습니다. 그 역할은 `kit_setup.py`가 만드는 두 파일이 하며, 커밋하지 않습니다: `.kit_local.json`의 `project`(담당자에게 받은 GCP 프로젝트 ID)·`cloudsdk_config`(키트 전용 gcloud 설정 폴더 경로)·`github`(GitHub 아이디, 없으면 null), `.claude/settings.local.json`의 `env.CLOUDSDK_CONFIG`(같은 폴더 경로)
- **계정 없이 확인**(모의 모드 대신): pip 뒤 아래 시험, `/data-harness` > 만들기로 S0~S2까지

```
python -m pytest tests/test_l0_contract.py tests/test_l0_dag.py tests/test_check_bash.py tests/test_check_write.py tests/test_state.py tests/test_where_am_i.py tests/test_check_source.py -q -n auto -p no:cacheprovider
```

## 5. 시작과 종료

- 시작: `/data-harness` → **만들기**·**이어하기**. 루프는 **만들기 창**, 대시보드는 **대시보드 창**(둘 다 새 PowerShell 창). **만들기 창은 끝날 때까지 닫지 마세요**(`통과`·`멈춤:`으로 끝). 종료: Claude Code는 `/exit`, 다음에 이어하기

## 6. 로그인과 권한

Google 계정 이메일을 알려 주시면 하루 안에 심사용 프로젝트 권한을 부여하고, 담당자가 프로젝트 ID와 사용할 Google 계정을 보내 드립니다. 비밀번호나 키 파일은 전달하지 않습니다. 본인 계정은 `ai_dev` 보기만 하고, 쿼리는 `ai-builder` 이름으로 대신 실행(가장, impersonation)합니다. `ai-builder`는 `ai_dev` 쓰기와 공개 데이터 읽기만 합니다. GitHub는 본인 계정을 씁니다.

## 7. 핵심 시나리오 (자세한 단계: `.claude/skills/data-harness/reference/stages.md`)

| 하면 | 나온다 |
|---|---|
| ① `/data-harness` 입력 | 입구 문장과 현재 단계 |
| ② 관심 주제 입력, 설정 한 줄·개인정보 확인 | 공개 데이터 후보 표, 판정표(가능·조건부·불가), 원천 승인 |
| ③ 인터뷰에 답하고 PR 머지 | 요구서 3파일, 승인 1 |
| ④ 루프 명령 실행 | 대시보드에서 진행 단계·반려·통과 |
| ⑤ 결과 PR 머지 | 콘솔의 결과 표 미리보기, 납품 문서 4종(정의서, 흐름도, 단위테스트 결과서, 인수인계), 승인 2 |

## 8. 데이터 초기화

zip을 새 폴더에 풀고 새 폴더 이름과 같은 이름의 새 GitHub 저장소를 만듭니다(START 부록 A-0). `ai_dev`는 만료 없음(기본 테이블·파티션 만료 모두 없음)이고, 비우기는 담당자(팀 이어드림)가 합니다.

## 9. 자주 생기는 문제

| 증상 | 해결 |
|---|---|
| 명령이 "인식되지 않음" | PowerShell 창을 모두 닫고 새로 연 뒤 다시 |
| `[on_stop]` 알림, 가장(impersonation) WARNING | 정상. 무시 |
| "Invalid username or token" | 자격 증명 관리자에서 `git:https://github.com` 삭제 후 다시 |
| 설정 스크립트 권한 오류 | 화면 문구를 담당자에게 |
| Squash 머지로 승인 기록 없음 | 담당자에게. 다음부터 **Merge pull request** |
| 같은 이름 테이블로 루프 멈춤 | 담당자에게 `ai_dev` 비우기 요청 뒤 같은 명령 |
| Claude 사용량 한도로 루프 멈춤 | 한도가 풀린 뒤 같은 명령(같은 `--ds`) |

전체 목록: `docs/kit/START.md` "자주 막히는 곳". 문서가 다르면 START.md를 따름

## 10. 문의

담당자(팀 이어드림, 주최 측 경유)에게 `out\dashboard.json`과 막힌 단계·상황을 보냅니다.
