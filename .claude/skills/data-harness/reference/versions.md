# 설치할 프로그램과 버전

이 키트에 필요한 프로그램과 버전, 설치 명령입니다.

| 도구 | 최소 | 검증 | 설치 |
|---|---|---|---|
| git | 2.28 | 2.52.0 | 아래 1번 |
| python | 3.10 | 3.10.11, 3.12.6 | 아래 2번 |
| gcloud | - | 590.0.1, 594.0.1 | 아래 3번 |
| bq | - | 2.1.41, 2.1.42 | 아래 3번 |
| claude | - | 2.1.331 | 아래 4번, 5번 |
| powershell | 5.1 | 5.1.26100 | Windows 10/11에 들어 있음 |

- 최소: 이보다 낮으면 키트가 돌지 않습니다. `-`는 있기만 하면 됩니다(검증한 버전 이상 권장)
- 검증: 우리가 실제로 키트를 돌린 버전입니다
- Google Cloud SDK 하나를 설치하면 `gcloud`와 `bq`가 둘 다 들어옵니다

## 설치 (한 줄씩 붙여 넣기)

붙여 넣기 전에:

- 없거나 최소보다 낮은 것만, 아래 순서대로 설치합니다. Claude Code를 설치했으면 5번도 실행합니다
- 관리자 확인 창이 뜨면 **예**를 누릅니다(Git, Google Cloud SDK)
- Google Cloud SDK는 약 5분 걸립니다. 끝날 때까지 창을 닫지 않습니다
- Claude Code를 설치할 때 `.local\bin is not in your PATH`가 나와도 괜찮습니다. 그다음 줄이 그 경로를 넣는 명령입니다

새 PowerShell 창에 한 줄씩 붙여 넣습니다. 위에서부터 1번 Git, 2번 Python, 3번 Google Cloud SDK, 4번 Claude Code, 5번 Claude Code PATH입니다.

```
winget install -e --id Git.Git -v 2.52.0 --source winget
winget install -e --id Python.Python.3.12 -v 3.12.6 --source winget
winget install -e --id Google.CloudSDK --source winget
& ([scriptblock]::Create((irm https://claude.ai/install.ps1))) 2.1.331
[Environment]::SetEnvironmentVariable("Path", [Environment]::GetEnvironmentVariable("Path","User") + ";$HOME\.local\bin", "User")
```

설치가 끝나면 **PowerShell 창을 모두 닫고 새로 엽니다.** Claude Code를 켜 두었으면 그것도 닫고 다시 켭니다.

## 확인

새 창에서 한 줄씩 실행해 버전 숫자가 나오면 됩니다. `gcloud.cmd`로 부르는 것은 새 PC의 실행 정책에 막히지 않게 하려는 것입니다.

```
git --version
python --version
gcloud.cmd --version
claude --version
```

| 증상 | 할 일 |
|---|---|
| `claude`, `gcloud`가 "인식되지 않음" | 설치 뒤 PowerShell 창을 모두 닫고 새로 엽니다. `claude`만 그러면 설치 명령의 Claude Code PATH 한 줄을 실행하고 창을 새로 엽니다 |
| `python`을 치면 Microsoft Store가 열림, `Python` 한 단어만 나옴, 아무것도 안 나옴 | Windows의 가짜 python(앱 실행 별칭)이 먼저 잡혔습니다. Python이 없으면 Python 설치 명령. 설치했는데도 같으면 시작 메뉴에서 "Manage App Execution Aliases"(앱 실행 별칭 관리)를 열어 `python.exe`·`python3.exe`의 App Installer 항목을 끄고 창을 새로 엽니다 |
| "running scripts is disabled on this system"(PowerShell 스크립트 실행이 막힘) | PowerShell 실행 정책이 `.ps1` 파일을 막았습니다. 키트는 `.ps1`을 만들지 않습니다. `gcloud`에서 났으면 `gcloud.cmd`로 같은 명령을 실행합니다. 키트 스크립트와 Claude Code는 영향이 없습니다. 다른 명령에서 났으면 화면 문구를 담당자에게 알립니다 |

그 밖의 막힘은 `docs/kit/START.md` "자주 막히는 곳"을 봅니다.

## 막힐 때 (winget)

| 증상 | 할 일 |
|---|---|
| `winget`이 "인식되지 않음" | 이 PC에 winget이 아직 등록되지 않았습니다. `Add-AppxPackage -RegisterByFamilyName -MainPackage Microsoft.DesktopAppInstaller_8wekyb3d8bbwe` 뒤 창을 새로 엽니다. 그래도 없으면 Microsoft Store에서 "앱 설치 관리자(App Installer)"를 설치합니다(https://apps.microsoft.com/detail/9nblggh4nns1) |
| `winget`이 `0x8a15005e : 서버 인증서가 필요한 값과 일치하지 않습니다`로 멈춤 | 명령 끝에 `--source winget`을 붙여 다시 실행합니다(설치 명령에는 이미 붙어 있습니다) |
| `winget`이 `--include-unknown`을 안내함 | 설치 명령을 두 번 치면 나오는 문구입니다. 이미 설치된 것이니 무시합니다 |

## 근거

- git: 최소는 `git init -b main`(START 3절). git-scm.com git-init 문서: 2.27에 `-b` 없음, 2.28에 있음
- python: 최소는 `scripts/loop/agent.py`·`state.py`의 dataclass 필드 `int | None`(3.10 문법, `from __future__` 없음). 3.13 이상은 실행해 보지 않음. winget 패키지는 PATH에 넣음(winget-pkgs 3.12.6 manifest `PrependPath=1`)
- gcloud: winget에 최신 1개만 있어 버전을 고정할 수 없음(`winget show --id Google.CloudSDK --versions`, 11/24 기준 594.0.1)
- bq: Google Cloud SDK에 들어 있음
- claude: 스킬의 `shell:` 필드가 생긴 버전을 변경 기록에서 찾지 못함. 참고로 `${CLAUDE_SKILL_DIR}` 2.1.69, `allowed-tools` YAML 목록 2.1.0. 설치 명령은 code.claude.com/docs/en/setup "Install a specific version", PATH 한 줄은 11/24 리허설(새로 포맷한 Windows PC)에서 성공. Git for Windows 없이도 돌지만(setup: 없으면 PowerShell 도구를 씀) 키트에는 Git이 필요함
- powershell: 키트 명령이 Windows PowerShell 5.1 문법 기준
- winget: 등록 명령은 Microsoft Learn "Use WinGet to install and manage applications", `--source`는 같은 곳의 "install" 문서
- 가짜 python: `WindowsApps\python.exe --version`이 `Python`만 내고 종료 코드 9009(재현). 별칭 끄기는 docs.python.org "Using Python on Windows". 한국어 화면의 메뉴 이름은 확인하지 못함
- 실행 정책: `-ExecutionPolicy Restricted`에서 `gcloud`는 막히고 `gcloud.cmd`는 돎(재현). 키트 스크립트는 `.cmd`를 찾아 부름
- 검증한 PC: 회사 PC(Windows 11), 집 PC(Windows 11, Python 3.12.6), 새로 포맷한 Windows PC(11/24 리허설: Python 3.12.6, Git 2.52.0, Google Cloud SDK 594.0.1, bq 2.1.42, Claude Code 2.1.331)

## 고칠 때

이 파일이 버전과 설치 명령 기준의 한 곳이다. `scripts/check_env.py`는 맨 위 표와 "설치" 절의 코드 블록을 읽는다(설치 칸의 "N번" = 코드 블록의 N번째 줄). 명령을 고치면 START.md 1절과 operations.md 3절도 같은 글자로 고친다(시험이 같은지 본다).
