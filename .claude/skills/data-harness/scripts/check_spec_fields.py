"""/data-harness S13 테이블 정의서 필수 칸 확인. 승인 1 커밋 전에 contract의 빈 칸을 찾는다(읽기 전용).

  python .claude/skills/data-harness/scripts/check_spec_fields.py docs/requirements/<마트>.contract.json [--json]

- 보는 칸은 정의서 생성기(scripts/deliverables/table_spec.py SOURCES)의 필수(*) 항목 가운데 contract에서 채우는 것이다:
  테이블 name_ko(한글 테이블명)·name·keys(PK 정보), 컬럼 name_ko(한글 컬럼명)·name·type. 같은지 시험이 본다.
  코드가 채우는 칸(소유자, Not Null, 개인정보 등)은 보지 않는다
- 컬럼 description도 본다. 정의서 항목은 아니지만 결과 표의 칸 설명이라 비우지 않는다(interview.md)
- 빈 칸: 없음, 빈 글자, 공백, 빈 목록, "미작성". L0는 name_ko가 없어도 통과하므로 여기서 본다
- 종료 코드: 0 통과, 1 빈 칸 있음, 2 파일을 읽지 못함·사용 오류
"""
import argparse
import json
import sys
from pathlib import Path

TABLE_FIELDS = (("name", "영문 테이블명"), ("name_ko", "한글 테이블명"), ("keys", "PK 정보"))
COLUMN_FIELDS = (("name", "영문 컬럼명"), ("name_ko", "한글 컬럼명"), ("type", "데이터 타입"), ("description", "설명"))
UNWRITTEN = "미작성"  # table_spec.UNWRITTEN과 같은 글자


def blank(value):
    if isinstance(value, str):
        return value.strip() in ("", UNWRITTEN)
    if isinstance(value, list):
        return not value or all(blank(v) for v in value)
    return True  # 없음, null, 글자·목록이 아닌 값


def items(value):
    return [v if isinstance(v, dict) else {} for v in value] if isinstance(value, list) else []


def label(value, where):
    return where if blank(value) or not isinstance(value, str) else value


def missing(contract):
    """빈 칸 목록 [{"table", "column"(테이블 칸이면 None), "field", "label"}]."""
    out = []
    tables = items(contract.get("tables"))
    if not tables:
        out.append({"table": "-", "column": None, "field": "tables", "label": "테이블 목록"})
    for i, t in enumerate(tables):
        table = label(t.get("name"), f"tables[{i}]")
        out += [{"table": table, "column": None, "field": f, "label": text} for f, text in TABLE_FIELDS if blank(t.get(f))]
        columns = items(t.get("columns"))
        if not columns:
            out.append({"table": table, "column": None, "field": "columns", "label": "컬럼 목록"})
        for j, c in enumerate(columns):
            column = label(c.get("name"), f"columns[{j}]")
            out += [{"table": table, "column": column, "field": f, "label": text}
                    for f, text in COLUMN_FIELDS if blank(c.get(f))]
    return out


def render(found):
    if not found:
        return "정의서 필수 칸 확인 통과: 빈 칸 0개"
    lines = [f"정의서 필수 칸 확인: 빈 칸 {len(found)}개", "테이블,컬럼,빈 칸"]
    return "\n".join(lines + [f"{m['table']},{m['column'] or '(테이블)'},{m['label']}({m['field']})" for m in found])


def main(argv=None):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass
    p = argparse.ArgumentParser(description="/data-harness S13 정의서 필수 칸 확인 (읽기 전용)")
    p.add_argument("contract", help="docs/requirements/<마트>.contract.json")
    p.add_argument("--json", action="store_true", help="JSON으로 출력")
    args = p.parse_args(argv)
    try:
        contract = json.loads(Path(args.contract).read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        print(f"확인 실패: contract를 읽지 못함 ({type(e).__name__})")
        return 2
    if not isinstance(contract, dict):
        print("확인 실패: contract가 객체가 아님")
        return 2
    found = missing(contract)
    print(json.dumps(found, ensure_ascii=False) if args.json else render(found))
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main())
