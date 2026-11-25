"""/data-harness S1 프로그램 확인 시험. 바깥 명령은 가짜 run으로 바꾼다.
기준값은 reference/versions.md 한 곳에서 읽고, 문서의 설치 명령이 그 표와 같은 글자인지도 본다."""
import importlib.util
import json
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / ".claude" / "skills" / "data-harness"
spec = importlib.util.spec_from_file_location("check_env", SKILL / "scripts" / "check_env.py")
check_env = importlib.util.module_from_spec(spec)
spec.loader.exec_module(check_env)

OUTPUT = {
    "claude": "2.1.331 (Claude Code)",
    "powershell": "5.1.26100.9818",
    "git": "git version 2.52.0.windows.1",
    "gcloud": "Google Cloud SDK 590.0.1\nbq 2.1.41\ncore 2026.10.22",
    "bq": "This is BigQuery CLI 2.1.41",
}
TOOL_OF = {tuple(v): k for k, v in check_env.COMMANDS.items()}


def fake(outputs=None, missing=(), codes=None, raises=None):
    outputs = dict(OUTPUT, **(outputs or {}))
    calls = []

    def run(args, timeout=check_env.TIMEOUT):
        tool = TOOL_OF[tuple(args)]
        calls.append(tool)
        if tool in missing:
            raise check_env.Missing(args[0])
        if raises and tool in raises:
            raise raises[tool]
        return (codes or {}).get(tool, 0), outputs[tool]
    return run, calls


@pytest.fixture
def table():
    return check_env.load_table()


def verdicts(monkeypatch, table, python=(3, 12, 6), **kw):
    run, _ = fake(**kw)
    monkeypatch.setattr(check_env, "run", run)
    rows = check_env.check(table, python)
    return {r["tool"]: r["verdict"] for r in rows}, rows


def test_table_has_every_tool_with_install_command(table):
    assert set(table) == set(check_env.TOOLS)
    assert table["python"]["min"] == (3, 10) and (3, 12, 6) in table["python"]["verified"]
    assert table["git"]["min"] == (2, 28) and table["claude"]["min"] is None
    assert all(table[t]["install"] for t in check_env.TOOLS)
    assert table["python"]["install"] == "winget install -e --id Python.Python.3.12 -v 3.12.6 --source winget"
    assert table["powershell"]["install"] == "Windows 10/11에 들어 있음"  # 번호가 없으면 칸 글자 그대로


def test_every_winget_install_names_source(table):
    """원천을 정하지 않으면 새 PC에서 인증서 오류(0x8a15005e)로 멈춘다(리허설)."""
    for rule in table.values():
        for line in rule["install"].splitlines():
            assert not line.startswith("winget ") or line.endswith(" --source winget")


def test_claude_install_prints_path_line(monkeypatch, table):
    _, rows = verdicts(monkeypatch, table, missing={"claude"})
    out = check_env.render(rows)
    assert "Claude Code: & (" in out and "Claude Code: [Environment]::SetEnvironmentVariable(\"Path\"" in out


def test_unknown_install_number_is_exit_2(monkeypatch, tmp_path, capsys):
    bad = tmp_path / "versions.md"
    bad.write_text(check_env.VERSIONS.read_text(encoding="utf-8").replace("아래 1번", "아래 9번"), encoding="utf-8")
    monkeypatch.setattr(check_env, "VERSIONS", bad)
    assert check_env.main([]) == 2
    assert "설치 절에 없는 번호" in capsys.readouterr().out


def test_all_found_passes(monkeypatch, table):
    v, rows = verdicts(monkeypatch, table)
    assert set(v.values()) == {"통과"} and check_env.exit_code(rows) == 0


def test_missing_tool_is_fail_with_install_line(monkeypatch, table):
    v, rows = verdicts(monkeypatch, table, missing={"git", "gcloud", "bq"})
    assert v["git"] == v["gcloud"] == v["bq"] == "없음" and check_env.exit_code(rows) == 1
    out = check_env.render(rows)
    assert "Git: winget install -e --id Git.Git -v 2.52.0 --source winget" in out
    assert out.count("winget install -e --id Google.CloudSDK --source winget") == 1  # gcloud·bq 같은 명령은 한 번만


@pytest.mark.parametrize("python,verdict", [
    ((3, 9, 13), "부족"), ((3, 10, 0), "통과"), ((3, 12, 9), "통과"), ((3, 13, 1), "통과(검증 밖)"),
])
def test_python_versions(monkeypatch, table, python, verdict):
    assert verdicts(monkeypatch, table, python=python)[0]["python"] == verdict


def test_git_below_minimum_is_fail(monkeypatch, table):
    v, rows = verdicts(monkeypatch, table, outputs={"git": "git version 2.27.0.windows.1"})
    assert v["git"] == "부족" and check_env.exit_code(rows) == 1


def test_claude_below_verified_is_pass_with_note(monkeypatch, table):
    """Claude Code는 근거 있는 최소가 없다: 검증 버전보다 낮으면 권장 미만(통과)."""
    v, rows = verdicts(monkeypatch, table, outputs={"claude": "2.1.300 (Claude Code)"})
    assert v["claude"] == "통과(권장 미만)" and check_env.exit_code(rows) == 0


@pytest.mark.parametrize("kw", [
    {"codes": {"bq": 1}},
    {"outputs": {"powershell": "알 수 없는 출력"}},
    {"raises": {"gcloud": subprocess.TimeoutExpired("gcloud", 1)}},
    {"raises": {"git": OSError("막힘")}},
])
def test_unreadable_is_check_failure(monkeypatch, table, kw):
    v, rows = verdicts(monkeypatch, table, **kw)
    assert "확인 실패" in v.values() and check_env.exit_code(rows) == 2
    assert "담당자" in check_env.render(rows)


def test_missing_wins_over_check_failure(monkeypatch, table):
    _, rows = verdicts(monkeypatch, table, missing={"git"}, codes={"bq": 1})
    assert check_env.exit_code(rows) == 1


def test_main_json_and_exit(monkeypatch, capsys):
    run, calls = fake(missing={"claude"})
    monkeypatch.setattr(check_env, "run", run)
    assert check_env.main(["--json"], python_version=(3, 10, 11)) == 1
    rows = json.loads(capsys.readouterr().out)
    assert [r["tool"] for r in rows] == check_env.TOOLS and "python" not in calls  # Python은 자기 버전


def test_bad_table_is_exit_2(monkeypatch, tmp_path, capsys):
    bad = tmp_path / "versions.md"
    bad.write_text("| 도구 | 최소 | 검증 | 설치 |\n| python | 3.10 | 3.12.6 | x |\n", encoding="utf-8")
    monkeypatch.setattr(check_env, "VERSIONS", bad)
    assert check_env.main([]) == 2
    assert "기준표" in capsys.readouterr().out


def test_real_run_uses_which(monkeypatch):
    monkeypatch.setattr(check_env.shutil, "which", lambda name: None)
    with pytest.raises(check_env.Missing):
        check_env.run(["git", "--version"])


def test_script_parses_on_old_python():
    """낮은 Python에서도 이 파일이 열려 '부족'을 보여 줘야 한다: 3.8 이후 문법(:=, match, f'{x=}')을 쓰지 않는다."""
    source = (SKILL / "scripts" / "check_env.py").read_text(encoding="utf-8")
    assert ":=" not in source and "\nmatch " not in source and 'f"' not in source and "f'" not in source


@pytest.mark.parametrize("doc", ["docs/kit/START.md", "docs/kit/operations.md"])
def test_docs_use_same_install_commands(table, doc):
    """설치 명령은 versions.md가 기준이다. 문서는 같은 글자를 쓴다(PowerShell은 설치 명령이 없다)."""
    lines = (ROOT / doc).read_text(encoding="utf-8").splitlines()
    for tool in ("python", "claude", "git", "gcloud"):
        for command in table[tool]["install"].splitlines():
            assert command in lines, (doc, tool)
