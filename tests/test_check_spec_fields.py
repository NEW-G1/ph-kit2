"""/data-harness S13 정의서 필수 칸 확인 시험. 보는 칸이 정의서 생성기(table_spec.py)와 같은지도 본다."""
import copy
import importlib.util
import json
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "deliverables"))
import table_spec  # noqa: E402

SCRIPT = ROOT / ".claude" / "skills" / "data-harness" / "scripts" / "check_spec_fields.py"
spec = importlib.util.spec_from_file_location("check_spec_fields", SCRIPT)
check = importlib.util.module_from_spec(spec)
spec.loader.exec_module(check)

CONTRACT = {"tables": [{"name": "mart_x", "name_ko": "결과 표", "keys": ["day"], "columns": [
    {"name": "day", "name_ko": "날짜", "type": "DATE", "description": "집계한 날"},
    {"name": "cnt", "name_ko": "건수", "type": "INT64", "description": "그날 건수"}]}]}


def run(tmp_path, contract, *argv):
    path = tmp_path / "m.contract.json"
    path.write_text(json.dumps(contract, ensure_ascii=False), encoding="utf-8")
    return check.main([str(path), *argv])


def test_full_contract_passes(tmp_path, capsys):
    assert run(tmp_path, CONTRACT) == 0
    assert "통과" in capsys.readouterr().out


@pytest.mark.parametrize("value", [None, "", "  ", "미작성"])
@pytest.mark.parametrize("where,field", [("table", "name_ko"), ("column", "name_ko"), ("column", "type"),
                                         ("column", "description")])
def test_blank_is_found(tmp_path, capsys, where, field, value):
    c = copy.deepcopy(CONTRACT)
    target = c["tables"][0] if where == "table" else c["tables"][0]["columns"][1]
    target[field] = value
    assert run(tmp_path, c, "--json") == 1
    found = json.loads(capsys.readouterr().out)
    assert [(m["table"], m["column"], m["field"]) for m in found] == [
        ("mart_x", None if where == "table" else "cnt", field)]


def test_missing_key_and_every_column_reported(tmp_path, capsys):
    """리허설: 한글 이름이 하나도 없으면 칸마다 한 줄씩 나온다."""
    c = copy.deepcopy(CONTRACT)
    for target in [c["tables"][0], *c["tables"][0]["columns"]]:
        del target["name_ko"]
    c["tables"][0]["keys"] = []
    assert run(tmp_path, c) == 1
    out = capsys.readouterr().out
    assert "빈 칸 4개" in out and "mart_x,cnt,한글 컬럼명(name_ko)" in out and "mart_x,(테이블),PK 정보(keys)" in out


@pytest.mark.parametrize("tables", [None, [], "x", ["x"], [{"name": "a", "columns": None}], [{"columns": [3]}]])
def test_odd_shapes_are_blank_not_crash(tmp_path, tables):
    assert run(tmp_path, {"tables": tables}) == 1


def test_unreadable_exits_2(tmp_path, capsys):
    bad = tmp_path / "bad.json"
    bad.write_text("{", encoding="utf-8")
    assert check.main([str(bad)]) == 2 and check.main([str(tmp_path / "none.json")]) == 2
    assert run(tmp_path, []) == 2


def test_template_is_blank(tmp_path):
    assert check.main([str(ROOT / "docs" / "requirements" / "_template.contract.json")]) == 1


def test_fields_match_table_spec():
    """정의서 필수(*) 항목 가운데 contract의 tables·columns에서 오는 칸을 모두 본다."""
    need = {"tables": {}, "columns": {}}
    for _, name, required, source, *_ in table_spec.SOURCES:
        m = re.match(r"contract (tables|columns)\[\]\.(\w+)", source)
        if required and m:
            need[m.group(1)][m.group(2)] = name
    assert need["tables"] and need["columns"]
    assert dict(check.TABLE_FIELDS) == need["tables"]
    assert {f: n for f, n in check.COLUMN_FIELDS if f != "description"} == need["columns"]
    assert check.UNWRITTEN == table_spec.UNWRITTEN
