"""/data-harness 현재 단계 판별 (읽기 전용). SKILL.md가 부를 때마다 이 출력을 받아 시작한다.

  python .claude/skills/data-harness/scripts/where_am_i.py [--root <저장소>] [--json]

- git과 파일만 읽는다. BigQuery·네트워크는 부르지 않고, 아무것도 쓰지 않는다
- 아래 순서로 보고 처음으로 성립하지 않는 단계를 현재 단계로 낸다(단계 번호는 reference/stages.md)
  S2 git 저장소·커밋 1개 이상 / S3~S4 .kit_local.json과 core.hooksPath=.githooks / S5 origin/main /
  S6~S9 원천 설정이 첫 커밋과 다름(시험·리전·고르기·판정은 흔적이 없어 S6부터) / S11 pii_columns.md의 검토한 원천이 설정과 같음 /
  S12 두 파일이 origin/main에도 같음 / S13 contract 있음 / S14 contract가 origin/main과 같음 /
  S15 iteration 0 커밋(Loop-Iteration-0: <마트> v<버전>) → 통과·멈춤 커밋 / S16 통과 커밋이 origin/main에 있음
- 마트가 여럿이면 마트마다 보고 가장 앞 단계를 낸다
- 지난 --ds: .dev/ladder_results/<마트>/의 가장 최근 결과에서, 없으면 통과 커밋 메시지에서
- 판별 중 오류가 나도 종료 코드 0(스킬 호출이 멈추지 않게). 그때는 "판별 실패"를 출력한다
- Python이 3.10 미만이면 판별하지 않고 "현재 단계: S1 (Python 없음 또는 버전 부족)"을 내고 종료 0.
  python이 없거나 Store 별칭이면 이 파일이 돌지 못하므로 SKILL.md 주입 명령이 같은 문장을 낸다
- 글자 출력의 마지막 줄은 늘 "보여 줄 문장(S0): <문장>"이다(판별 실패, 낮은 Python에서도). 스킬은 그 문장을 그대로 옮긴다.
  stages.md S0와 같은 글자(시험이 본다). --json에는 넣지 않는다
- 바깥 명령은 run() 하나로 모은다(시험에서 바꿔 끼움)
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]  # <root>/.claude/skills/data-harness/scripts/where_am_i.py
CONFIG = "dags/harness_config.json"
PII = "docs/architecture/pii_columns.md"
REQ_DIR = "docs/requirements"
KIT_LOCAL = ".kit_local.json"
REVIEWED = re.compile(r"^검토한 원천:\s*`([^`]+)`", re.M)
VERSION = re.compile(r'"version"\s*:\s*(\d+)')
LADDER_FILE = re.compile(r"-v(\d+)-(\d+)\.json$")
MIN_PYTHON = (3, 10)  # reference/versions.md의 python 최소와 같다(시험이 본다)
PYTHON_LOW = "현재 단계: S1 (Python 없음 또는 버전 부족)"  # SKILL.md 주입 명령의 대체 문장과 같은 글자
S0_LABEL = "보여 줄 문장(S0): "
S0_TEXT = ("당신이 고른 공개 데이터로 결과 표를 만듭니다. AI가 만들고, 코드가 검사하고, 당신이 승인합니다(대시보드에는 '결재'로 표시). "
           "끝나면 결과 표, 진행 화면(대시보드), 설명 문서를 받습니다. "
           "당신이 할 일은 로그인, 데이터 고르기, 파일 한 줄 고치기, 개인정보 확인, 승인 3번입니다.")

TITLES = {
    "S2": "키트 폴더를 git 저장소로 만들기",
    "S3": "GitHub 저장소 만들기(S3)와 로그인 설정(S4)",
    "S5": "GitHub에 처음 올리기",
    "S6": "키트 시험(S6), ai_dev 리전(S7), 데이터 고르기(S8), 되는지 판정(S9)",
    "S11": "개인정보 목록 확정",
    "S12": "원천 변경 결재(source 브랜치 머지)",
    "S13": "인터뷰로 요구서 만들기",
    "S14": "결재 1(요구서 PR 머지)",
    "S15": "루프(AI 작성과 자동 검사)",
    "S16": "결과 확인과 결재 2(구현 PR 머지)",
    "완료": "결재 2까지 끝남",
}
NEXT = {
    "S2": "S1 프로그램 확인 뒤 git init과 첫 커밋",
    "S3": "GitHub에 폴더 이름과 같은 빈 저장소를 만들고 kit_setup.py 실행",
    "S5": "git push -u origin main",
    "S6": "키트 시험(이미 했으면 건너뛸지 묻기) → ai_dev 리전 조회 → 데이터 고르기",
    "S11": "개인정보 후보를 묻고 답을 받은 뒤 pii_columns.md 고치기",
    "S12": "체크리스트를 채워 source 브랜치에 커밋, 사람이 push·PR·머지 뒤 git pull",
    "S13": "만들고 싶은 것을 묻고 인터뷰 시작",
    "S14": "req 브랜치에 요구서 커밋, 사람이 push·PR·머지 뒤 git pull",
    "S16": "생성기 실행과 콘솔 미리보기 안내, 사람이 build push·PR·머지",
    "완료": "끝나고 담당자에게 보낼 것(dashboard.py --json) 안내",
}
ORDER = ["S2", "S3", "S5", "S6", "S11", "S12", "S13", "S14", "S15", "S16", "완료"]


def run(args, cwd):
    """(종료 코드, 표준 출력). 시험에서 바꿔 끼운다."""
    p = subprocess.run(args, cwd=cwd, capture_output=True, encoding="utf-8", errors="replace")
    return p.returncode, p.stdout


def git(root, *args):
    code, out = run(["git", *args], root)
    return out.strip() if code == 0 else None


def show(root, ref, path):
    """ref의 파일 내용. 없으면 None."""
    code, out = run(["git", "show", f"{ref}:{path}"], root)
    return out if code == 0 else None


def source_of(text):
    if text is None:
        return None
    try:
        s = json.loads(text)["source"]
        return f"{s['project']}.{s['dataset']}"
    except (ValueError, KeyError, TypeError):
        return None


def reviewed_of(text):
    m = REVIEWED.search(text or "")
    return m.group(1) if m else None


def read(root, rel):
    path = Path(root) / rel
    return path.read_text(encoding="utf-8") if path.is_file() else None


def marts(root):
    folder = Path(root) / REQ_DIR
    if not folder.is_dir():
        return []
    return sorted(f.name[:-len(".contract.json")] for f in folder.glob("*.contract.json") if not f.name.startswith("_"))


def commits(root, ref, needle):
    """ref 이력에서 메시지에 needle이 든 커밋의 전체 메시지 목록(새것부터)."""
    out = git(root, "log", ref, "--fixed-strings", f"--grep={needle}", "--format=%B%x00")
    return [m.strip() for m in (out or "").split("\0") if m.strip()]


def last_ds(root, mart):
    """가장 최근 사다리 결과의 판정 날짜. 없으면 통과 커밋 메시지의 ds."""
    folder = Path(root) / ".dev" / "ladder_results" / mart
    found = []
    for f in folder.glob("*.json") if folder.is_dir() else []:
        m = LADDER_FILE.search(f.name)
        if m:
            found.append((int(m.group(1)), int(m.group(2)), f.stat().st_mtime, f))
    for *_, f in sorted(found, reverse=True):
        try:
            rungs = json.loads(f.read_text(encoding="utf-8")).get("rungs", [])
        except ValueError:
            continue
        for rung in rungs:
            if isinstance(rung, dict) and rung.get("ds"):
                return rung["ds"]
    for msg in commits(root, "--branches", f"loop: {mart} v"):
        m = re.search(r" 통과 \(iteration \d+, ds (\d{4}-\d{2}-\d{2})\)", msg)
        if m:
            return m.group(1)
    return None


def mart_stage(root, mart):
    """마트 하나의 (단계, 상태 설명)."""
    rel = f"{REQ_DIR}/{mart}.contract.json"
    local = read(root, rel)
    if local != show(root, "origin/main", rel):
        return "S14", "contract가 origin/main과 다름(결재 1 전이거나 git pull 전)"
    m = VERSION.search(local)
    version = m.group(1) if m else "?"
    passed = re.compile(rf"^loop: {re.escape(mart)} v{version} 통과", re.M)
    if any(passed.search(msg) for msg in commits(root, "origin/main", f"loop: {mart} v{version} 통과")):
        return "완료", f"v{version} 통과 커밋이 origin/main에 머지됨"
    if any(passed.search(msg) for msg in commits(root, "--branches", f"loop: {mart} v{version} 통과")):
        return "S16", f"v{version} 루프 통과, 결재 2 전"
    trailer = f"Loop-Iteration-0: {mart} v{version}"
    if not commits(root, "--branches", trailer):
        old = commits(root, "--branches", f"Loop-Iteration-0: {mart} v")
        note = "예전 버전의 루프 브랜치가 있음, 새 이름(build2 등)으로" if old else "루프 시작 전"
        return "S15", note
    halted = re.compile(rf"^loop: {re.escape(mart)} v{version} 멈춤 기록 \((.*)\)", re.M)
    for msg in commits(root, "--branches", f"loop: {mart} v{version} 멈춤 기록"):
        h = halted.search(msg)
        if h:
            return "S15", f"루프 멈춤({h.group(1)}). 그 뒤 다시 실행했다면 진행 중일 수 있음"
    return "S15", "루프 진행 중이거나 중단됨(통과·멈춤 커밋 없음)"


def detect(root):
    root = Path(root)
    result = {"stage": None, "detail": "", "marts": []}

    def done(stage, detail=""):
        result.update(stage=stage, detail=detail)
        return result

    if not (root / ".git").exists() or git(root, "rev-parse", "--verify", "HEAD") is None:
        return done("S2", "git 저장소가 아니거나 커밋이 없음")
    if not (root / KIT_LOCAL).is_file() or git(root, "config", "core.hooksPath") != ".githooks":
        return done("S3", "로그인 설정(.kit_local.json, 커밋 검사 켜기)이 아직 없음")
    if git(root, "rev-parse", "--verify", "refs/remotes/origin/main") is None:
        return done("S5", "원격 origin/main이 없음")
    source = source_of(read(root, CONFIG))
    roots = (git(root, "rev-list", "--max-parents=0", "HEAD") or "").split()
    first = source_of(show(root, roots[-1], CONFIG)) if roots else None
    if source is None:
        return done("S6", f"{CONFIG}를 읽지 못함")
    if source == first:
        return done("S6", f"원천이 키트 첫 커밋과 같음({source})")
    if reviewed_of(read(root, PII)) != source:
        return done("S11", f"pii_columns.md의 검토한 원천이 설정({source})과 다름")
    if (source_of(show(root, "origin/main", CONFIG)) != source
            or reviewed_of(show(root, "origin/main", PII)) != source):
        return done("S12", "원천 설정이나 개인정보 목록이 origin/main과 다름")
    names = marts(root)
    if not names:
        return done("S13", "요구서 contract가 없음")
    stages = []
    for mart in names:
        contract = read(root, f"{REQ_DIR}/{mart}.contract.json")
        try:
            mode = (json.loads(contract).get("load") or {}).get("mode") or "snapshot"
        except (ValueError, AttributeError):
            mode = "?"
        stage, detail = mart_stage(root, mart)
        info = {"mart": mart, "stage": stage, "detail": detail, "load": mode}
        if mode == "incremental":
            info["last_ds"] = last_ds(root, mart)
        result["marts"].append(info)
        stages.append((ORDER.index(stage), stage, detail))
    _, stage, detail = min(stages)
    return done(stage, detail)


def render(result):
    stage = result["stage"]
    lines = [f"현재 단계: {stage} ({TITLES.get(stage, '')})"]
    if result["detail"]:
        lines.append(f"근거: {result['detail']}")
    for m in result["marts"]:
        line = f"마트: {m['mart']} - {m['stage']}, {m['detail']}, 적재 방식 {m['load']}"
        if m["load"] == "incremental":
            line += f", 지난 --ds {m.get('last_ds') or '없음'}"
        lines.append(line)
    if stage in NEXT:
        lines.append(f"다음 할 일: {NEXT[stage]}")
    elif stage == "S15":
        lines.append("다음 할 일: 루프 사전 점검 뒤 새 PowerShell 창에서 루프 실행(멈춤이면 troubleshooting.md)")
    lines.append("참고: S6(시험)·S7(리전)은 흔적을 남기지 않는다. S7은 다시 조회하고 S6은 했는지 묻는다")
    return "\n".join(lines)


def main(argv=None, version=None):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass
    if (version or sys.version_info) < MIN_PYTHON:  # 낮은 Python: 판별하지 않고 S1로 보낸다(종료 0, 주입이 멈추지 않게)
        print(PYTHON_LOW)
        print(S0_LABEL + S0_TEXT)
        return 0
    p = argparse.ArgumentParser(description="/data-harness 현재 단계 판별 (읽기 전용)")
    p.add_argument("--root", default=str(ROOT))
    p.add_argument("--json", action="store_true", help="JSON으로 출력")
    args = p.parse_args(argv)
    try:
        result = detect(args.root)
    except Exception as e:  # noqa: BLE001 - 주입이 멈추지 않게 어떤 오류도 0으로 끝낸다
        print(f"판별 실패: {type(e).__name__}. S1부터 시작한다")
        print(S0_LABEL + S0_TEXT)
        return 0
    print(json.dumps(result, ensure_ascii=False) if args.json else render(result) + "\n" + S0_LABEL + S0_TEXT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
