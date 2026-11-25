"""/data-harness S1 프로그램 확인. Python, Claude Code, PowerShell, Git, gcloud, bq 버전을 읽어 기준표와 비교한다.

  python .claude/skills/data-harness/scripts/check_env.py [--json]

- 기준값은 reference/versions.md 하나에서 읽는다(최소·검증은 표, 설치 명령은 "설치" 절 코드 블록). 여기에 숫자를 적지 않는다
- 표준 라이브러리만 쓴다(requirements-dev 설치 전 S1에서 돈다). 오래된 Python에서도 읽히는 문법만 쓴다
  (낮은 Python이 이 파일을 열어 "부족"을 보여 줄 수 있게)
- Python은 이 스크립트를 돌린 인터프리터의 버전이다(사용자가 `python`으로 부른 것)
- 판정: 없음(못 찾음) / 부족(최소 미만) / 통과 / 통과(검증 밖: 검증한 가장 높은 버전보다 앞 두 자리가 높음) /
  통과(권장 미만: 최소가 없고 검증한 버전보다 낮음) / 확인 실패(실행 오류·시간 초과·버전을 읽지 못함)
- 종료 코드: 0 모두 통과, 1 없음·부족이 하나 이상, 2 그 밖에 확인 실패가 하나 이상. 표 아래에 없음·부족인 도구의 설치 명령을 적는다
- 바깥 명령은 run() 하나(시험에서 바꿔 끼운다). 아무것도 쓰지 않는다
"""
import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

VERSIONS = Path(__file__).resolve().parents[1] / "reference" / "versions.md"
TOOLS = ["python", "claude", "powershell", "git", "gcloud", "bq"]
LABEL = {"python": "Python", "claude": "Claude Code", "powershell": "PowerShell", "git": "Git",
         "gcloud": "gcloud", "bq": "bq"}
COMMANDS = {
    "claude": ["claude", "--version"],
    "powershell": ["powershell", "-NoProfile", "-Command", "$PSVersionTable.PSVersion.ToString()"],
    "git": ["git", "--version"],
    "gcloud": ["gcloud", "--version"],
    "bq": ["bq", "version"],
}
NUMBER = re.compile(r"(\d+(?:\.\d+)+)")
CELL = re.compile(r"(?<!\\)\|")
INSTALL_BLOCK = re.compile(r"^## 설치[^\n]*\n.*?^```\n(.*?)^```", re.M | re.S)
INSTALL_NO = re.compile(r"(\d+)번")
FAIL = ("없음", "부족")
TIMEOUT = 120


class Missing(Exception):
    """명령을 찾지 못함."""


def run(args, timeout=TIMEOUT):
    """(종료 코드, 표준 출력 + 표준 오류). 못 찾으면 Missing. 시험에서 바꿔 끼운다."""
    exe = shutil.which(args[0])
    if exe is None:
        raise Missing(args[0])
    p = subprocess.run([exe] + list(args[1:]), stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)
    out = p.stdout.decode("utf-8", "replace") + "\n" + p.stderr.decode("utf-8", "replace")
    return p.returncode, out


def load_table(path=None):
    """versions.md → {도구: {"min": 튜플 또는 None, "verified": [튜플...], "install": 문자열, ...}}.
    설치 칸의 "N번"은 설치 절 코드 블록의 N번째 줄이다(여럿이면 줄바꿈으로 잇는다). 번호가 없으면 칸 글자 그대로."""
    rows = {}
    doc = Path(path or VERSIONS).read_text(encoding="utf-8")
    block = INSTALL_BLOCK.search(doc)
    commands = [c.strip() for c in block.group(1).splitlines() if c.strip()] if block else []
    for line in doc.splitlines():
        if not line.startswith("|"):
            continue
        cells = [c.strip().replace("\\|", "|") for c in CELL.split(line.strip().strip("|"))]
        if len(cells) < 4 or cells[0] not in TOOLS:
            continue
        numbers = [int(n) for n in INSTALL_NO.findall(cells[3])]
        if any(not 1 <= n <= len(commands) for n in numbers):
            raise ValueError("versions.md 설치 절에 없는 번호: " + cells[0] + " " + cells[3])
        install = "\n".join(commands[n - 1] for n in numbers) or cells[3]
        rows[cells[0]] = {"min": None if cells[1] == "-" else parse(cells[1]), "min_text": cells[1],
                          "verified": [parse(v) for v in cells[2].split(",")], "verified_text": cells[2],
                          "install": install}
    missing = [t for t in TOOLS if t not in rows]
    if missing:
        raise ValueError("versions.md 표에 없는 도구: " + ", ".join(missing))
    return rows


def parse(text):
    m = NUMBER.search(text)
    if not m:
        raise ValueError("버전 숫자가 없음: " + repr(text))
    return tuple(int(x) for x in m.group(1).split("."))


def text(version):
    return ".".join(str(x) for x in version)


def judge(found, rule):
    """found: 버전 튜플. rule: load_table의 한 행."""
    if rule["min"] is not None and found[:len(rule["min"])] < rule["min"]:
        return "부족"
    top = max(rule["verified"])[:2]  # 검증 밖은 앞 두 자리로 본다(3.12.8은 3.12.6과 같은 줄)
    if found[:2] > top:
        return "통과(검증 밖)"
    low = min(rule["verified"])
    if rule["min"] is None and found[:len(low)] < low:
        return "통과(권장 미만)"
    return "통과"


def find_version(tool, python_version=None):
    """(버전 튜플 또는 None, 판정 대신 쓸 말 또는 None)."""
    if tool == "python":
        return tuple((python_version or sys.version_info)[:3]), None
    try:
        code, out = run(COMMANDS[tool])
    except Missing:
        return None, "없음"
    except (OSError, subprocess.SubprocessError):
        return None, "확인 실패"
    m = NUMBER.search(out)
    if code != 0 or not m:
        return None, "확인 실패"
    return tuple(int(x) for x in m.group(1).split(".")), None


def check(table, python_version=None):
    rows = []
    for tool in TOOLS:
        rule = table[tool]
        found, verdict = find_version(tool, python_version)
        rows.append({"tool": tool, "label": LABEL[tool], "found": text(found) if found else "-",
                     "min": rule["min_text"], "verified": rule["verified_text"],
                     "verdict": verdict or judge(found, rule), "install": rule["install"]})
    return rows


def exit_code(rows):
    if any(r["verdict"] in FAIL for r in rows):
        return 1
    if any(r["verdict"] == "확인 실패" for r in rows):
        return 2
    return 0


def render(rows):
    lines = ["도구,찾은 버전,최소 버전,검증한 버전,판정"]
    for r in rows:
        lines.append(",".join([r["label"], r["found"], r["min"], r["verified"].replace(", ", " "), r["verdict"]]))
    need = [r for r in rows if r["verdict"] in FAIL]
    if need:
        lines += ["", "설치할 것(새 PowerShell 창에서 한 줄씩. 설치 뒤 창을 닫고 새로 열고 Claude Code도 다시 켭니다):"]
        seen = set()
        for r in need:
            if r["install"] not in seen:
                seen.add(r["install"])
                lines += [r["label"] + ": " + line for line in r["install"].splitlines()]
    if any(r["verdict"] == "확인 실패" for r in rows):
        lines += ["", "확인 실패: 버전을 읽지 못한 도구가 있습니다. 창을 새로 연 뒤 다시 실행하고, 같으면 담당자에게 이 표를 보냅니다."]
    return "\n".join(lines)


def main(argv=None, python_version=None):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass
    p = argparse.ArgumentParser(description="/data-harness S1 프로그램 확인(버전 기준: reference/versions.md)")
    p.add_argument("--json", action="store_true")
    args = p.parse_args(argv)
    try:
        table = load_table()
    except (OSError, ValueError) as e:
        print("확인 실패: 버전 기준표를 읽지 못함 (" + str(e) + ")")
        return 2
    rows = check(table, python_version)
    print(json.dumps(rows, ensure_ascii=False) if args.json else render(rows))
    return exit_code(rows)


if __name__ == "__main__":
    sys.exit(main())
