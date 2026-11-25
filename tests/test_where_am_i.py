"""/data-harness 현재 단계 판별 시험. 임시 폴더에 진짜 git 저장소를 만들어 단계마다 조건을 하나씩 채운다.
BigQuery·네트워크는 쓰지 않는다. origin/main은 git update-ref로 흉내 낸다."""
import importlib.util
import json
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / ".claude" / "skills" / "data-harness" / "scripts" / "where_am_i.py"
spec = importlib.util.spec_from_file_location("where_am_i", SCRIPT)
where_am_i = importlib.util.module_from_spec(spec)
spec.loader.exec_module(where_am_i)

KIT_SOURCE = {"project": "bigquery-public-data", "dataset": "kit_example", "location": "US"}
PICKED = {"project": "bigquery-public-data", "dataset": "picked_data", "location": "US"}


def sh(root, *args):
    p = subprocess.run(["git", "-c", "user.name=tester", "-c", "user.email=tester@example.com", *args],
                       cwd=root, capture_output=True, encoding="utf-8")
    assert p.returncode == 0, p.stderr
    return p.stdout.strip()


def write(root, rel, text):
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def config(source):
    return json.dumps({"schema_version": 1, "source": source, "datasets": {}, "retired_datasets": [], "om": {}})


def pii(source):
    return f"# 목록\n\n검토한 원천: `{source['project']}.{source['dataset']}`\n\n| 원천 테이블 | 컬럼 | 근거 |\n"


def contract(mart, version=1, mode="snapshot"):
    return json.dumps({"mart": mart, "version": version, "load": {"mode": mode}})


def commit(root, message="c"):
    sh(root, "add", "-A")
    sh(root, "commit", "-q", "--allow-empty", "-m", message)
    return sh(root, "rev-parse", "HEAD")


def publish(root):
    """지금 HEAD를 origin/main으로(사람이 push·머지한 것과 같은 상태)."""
    sh(root, "update-ref", "refs/remotes/origin/main", "HEAD")


def stage(root):
    return where_am_i.detect(root)["stage"]


@pytest.fixture
def kit(tmp_path):
    """키트 첫 커밋까지 한 폴더."""
    write(tmp_path, "dags/harness_config.json", config(KIT_SOURCE))
    write(tmp_path, "docs/architecture/pii_columns.md", pii(KIT_SOURCE))
    write(tmp_path, "docs/requirements/_template.contract.json", contract(""))
    sh(tmp_path, "init", "-q", "-b", "main")
    commit(tmp_path, "키트 첫 커밋")
    return tmp_path


@pytest.fixture
def ready(kit):
    """로그인 설정과 첫 push까지 한 폴더."""
    write(kit, ".kit_local.json", "{}")
    sh(kit, "config", "core.hooksPath", ".githooks")
    publish(kit)
    return kit


@pytest.fixture
def sourced(ready):
    """원천 결재까지 한 폴더."""
    write(ready, "dags/harness_config.json", config(PICKED))
    write(ready, "docs/architecture/pii_columns.md", pii(PICKED))
    commit(ready, "원천 변경")
    publish(ready)
    return ready


def test_empty_folder_is_s2(tmp_path):
    assert stage(tmp_path) == "S2"


def test_repo_without_commit_is_s2(tmp_path):
    sh(tmp_path, "init", "-q")
    assert stage(tmp_path) == "S2"


def test_first_commit_only_is_s3(kit):
    assert stage(kit) == "S3"


def test_kit_local_without_hooks_path_is_s3(kit):
    write(kit, ".kit_local.json", "{}")
    assert stage(kit) == "S3"


def test_no_origin_is_s5(kit):
    write(kit, ".kit_local.json", "{}")
    sh(kit, "config", "core.hooksPath", ".githooks")
    assert stage(kit) == "S5"


def test_source_unchanged_is_s6(ready):
    result = where_am_i.detect(ready)
    assert result["stage"] == "S6" and "kit_example" in result["detail"]


def test_source_changed_but_pii_not_reviewed_is_s11(ready):
    write(ready, "dags/harness_config.json", config(PICKED))
    assert stage(ready) == "S11"


def test_both_changed_but_not_merged_is_s12(ready):
    write(ready, "dags/harness_config.json", config(PICKED))
    write(ready, "docs/architecture/pii_columns.md", pii(PICKED))
    assert stage(ready) == "S12"
    commit(ready, "원천 변경")  # 커밋만 하고 push·머지 전
    assert stage(ready) == "S12"


def test_no_contract_is_s13(sourced):
    assert stage(sourced) == "S13"


def test_contract_not_merged_is_s14(sourced):
    write(sourced, "docs/requirements/m1.contract.json", contract("m1"))
    assert stage(sourced) == "S14"
    commit(sourced, "요구서")
    assert stage(sourced) == "S14"


@pytest.fixture
def approved(sourced):
    write(sourced, "docs/requirements/m1.contract.json", contract("m1", mode="incremental"))
    commit(sourced, "요구서")
    publish(sourced)
    return sourced


def test_approved_contract_without_loop_is_s15(approved):
    result = where_am_i.detect(approved)
    assert result["stage"] == "S15" and result["marts"][0]["detail"] == "루프 시작 전"
    assert result["marts"][0]["load"] == "incremental" and result["marts"][0]["last_ds"] is None


def test_loop_started_is_s15_running(approved):
    sh(approved, "checkout", "-q", "-b", "build")
    commit(approved, "loop: m1 v1 iteration 0 (검증 쿼리·게이트)\n\nLoop-Iteration-0: m1 v1")
    assert "진행 중" in where_am_i.detect(approved)["detail"]


def test_loop_halted_shows_reason_and_last_ds(approved):
    sh(approved, "checkout", "-q", "-b", "build")
    commit(approved, "loop: m1 v1 iteration 0 (검증 쿼리·게이트)\n\nLoop-Iteration-0: m1 v1")
    write(approved, ".dev/ladder_results/m1/raw_x-v1-1.json",
          json.dumps({"rungs": [{"rung": "L0", "ds": None}, {"rung": "L1", "ds": "2026-11-02"}], "verdict": "halt"}))
    commit(approved, "loop: m1 v1 멈춤 기록 (same_type_3x)")
    result = where_am_i.detect(approved)
    assert result["stage"] == "S15" and "same_type_3x" in result["detail"]
    assert result["marts"][0]["last_ds"] == "2026-11-02"
    assert "지난 --ds 2026-11-02" in where_am_i.render(result)


def test_old_version_loop_branch_asks_new_branch(approved):
    sh(approved, "checkout", "-q", "-b", "build")
    commit(approved, "iteration 0\n\nLoop-Iteration-0: m1 v1")
    sh(approved, "checkout", "-q", "main")
    write(approved, "docs/requirements/m1.contract.json", contract("m1", version=2))
    commit(approved, "요구서 수정")
    publish(approved)
    assert "build2" in where_am_i.detect(approved)["detail"]


def test_loop_passed_is_s16_then_merged_is_done(approved):
    sh(approved, "checkout", "-q", "-b", "build")
    commit(approved, "iteration 0\n\nLoop-Iteration-0: m1 v1")
    commit(approved, "loop: m1 v1 통과 (iteration 2, ds 2026-11-03)")
    result = where_am_i.detect(approved)
    assert result["stage"] == "S16" and result["marts"][0]["last_ds"] == "2026-11-03"
    publish(approved)  # 결재 2 머지
    assert stage(approved) == "완료"


def test_two_marts_reports_the_earliest(approved):
    sh(approved, "checkout", "-q", "-b", "build")
    commit(approved, "iteration 0\n\nLoop-Iteration-0: m1 v1")
    commit(approved, "loop: m1 v1 통과 (iteration 1)")
    publish(approved)
    write(approved, "docs/requirements/m2.contract.json", contract("m2"))
    result = where_am_i.detect(approved)
    assert result["stage"] == "S14"
    assert {m["mart"]: m["stage"] for m in result["marts"]} == {"m1": "완료", "m2": "S14"}


def test_errors_still_exit_zero(monkeypatch, capsys):
    def boom(root):
        raise RuntimeError("x")
    monkeypatch.setattr(where_am_i, "detect", boom)
    assert where_am_i.main(["--root", "."]) == 0
    out = capsys.readouterr().out
    assert "판별 실패" in out and out.rstrip("\n").endswith(where_am_i.S0_LABEL + where_am_i.S0_TEXT)


@pytest.mark.parametrize("version", [(3, 9, 13), (3, 8, 0)])
def test_low_python_goes_to_s1_and_exits_zero(monkeypatch, capsys, version):
    monkeypatch.setattr(where_am_i, "detect", lambda root: pytest.fail("낮은 Python에서는 판별하지 않는다"))
    assert where_am_i.main([], version=version) == 0
    assert capsys.readouterr().out.strip().splitlines() == [
        "현재 단계: S1 (Python 없음 또는 버전 부족)", where_am_i.S0_LABEL + where_am_i.S0_TEXT]


def test_s0_text_is_last_line_and_json_is_unchanged(ready, capsys):
    assert where_am_i.main(["--root", str(ready)]) == 0
    lines = capsys.readouterr().out.strip().splitlines()
    assert lines[0].startswith("현재 단계: S6") and lines[-1] == where_am_i.S0_LABEL + where_am_i.S0_TEXT
    assert sum(line.startswith(where_am_i.S0_LABEL) for line in lines) == 1
    where_am_i.main(["--root", str(ready), "--json"])
    assert json.loads(capsys.readouterr().out)["stage"] == "S6"


def test_s0_text_matches_stages_and_skill_copies_output():
    """S0 문장은 where_am_i가 낸다. stages.md S0(python이 없을 때 쓰는 사본)와 같은 글자, SKILL.md는 출력의 그 줄을 옮긴다."""
    stages = (SCRIPT.parents[1] / "reference" / "stages.md").read_text(encoding="utf-8")
    s0 = stages.split("## S0 ")[1].split("## S1 ")[0]
    assert f"- 보여 줄 문장: {where_am_i.S0_TEXT}\n" in s0
    skill = (SCRIPT.parents[1] / "SKILL.md").read_text(encoding="utf-8")
    assert f"`{where_am_i.S0_LABEL}`" in skill and where_am_i.S0_TEXT not in skill


def test_low_python_text_and_minimum_match_skill_and_versions():
    """세 곳이 같아야 한다: SKILL.md 주입 대체 문장, where_am_i 문장, versions.md python 최소."""
    skill = (SCRIPT.parents[1] / "SKILL.md").read_text(encoding="utf-8")
    inject = [line for line in skill.splitlines() if line.startswith("!`")]
    assert len(inject) == 1 and where_am_i.PYTHON_LOW in inject[0] and inject[0].rstrip().endswith("exit 0`")
    versions = (SCRIPT.parents[1] / "reference" / "versions.md").read_text(encoding="utf-8")
    row = next(line for line in versions.splitlines() if line.startswith("| python |"))
    assert row.split("|")[2].strip() == ".".join(map(str, where_am_i.MIN_PYTHON))


def test_render_has_stage_and_next(ready):
    text = where_am_i.render(where_am_i.detect(ready))
    assert text.startswith("현재 단계: S6") and "다음 할 일:" in text


def test_reads_only(ready):
    """판별은 파일을 만들거나 바꾸지 않는다."""
    before = sorted((p.relative_to(ready).as_posix(), p.stat().st_mtime_ns)
                    for p in ready.rglob("*") if p.is_file() and ".git" not in p.parts)
    where_am_i.detect(ready)
    after = sorted((p.relative_to(ready).as_posix(), p.stat().st_mtime_ns)
                   for p in ready.rglob("*") if p.is_file() and ".git" not in p.parts)
    assert before == after
