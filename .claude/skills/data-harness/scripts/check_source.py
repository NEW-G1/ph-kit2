"""/data-harness S8·S9 원천 판정. 공개 데이터셋을 받아 테이블마다 이 키트로 쓸 수 있는지 판정한다.

  check_source.py --dataset <데이터셋>                    S9 판정표
  check_source.py --datasets a,b,c                       여러 데이터셋의 판정표를 한 번에
  check_source.py --datasets a,b,c --filter              S8 후보 거르기: 쓸 수 있는 데이터셋만, 뺀 개수는 이유마다
  check_source.py --dataset <데이터셋> --table <테이블>    테이블 하나의 설명과 칸 목록(이름, 타입, 설명)
  공통: --json. 판정표: --allow-large (손으로 하는 길의 옛 판정. 500 MB 초과 + 날짜 파티션을 incremental 조건부로)

- 메타데이터만 읽는다: 공개 데이터셋 목록과 리전(`bq ls`), 데이터셋·테이블 정보(`bq show`), `__TABLES__`(이름, 종류, 크기),
  `INFORMATION_SCHEMA.COLUMNS`(컬럼 이름·타입, 파티션 컬럼), `TABLE_OPTIONS`(테이블 설명). 데이터 값은 읽지 않는다
- bq는 사다리와 같은 common.Bq로 부른다: ai-builder 설정에서만, 쿼리마다 dry-run 먼저, 비용 상한(common.MAX_BYTES).
  인증 확인과 ai_dev 리전 조회는 실행마다 한 번. 여러 데이터셋은 같은 리전끼리 UNION ALL로 묶는다(BATCH개씩).
  묶음이 막히면 하나씩 다시 해 막힌 데이터셋만 "읽지 못함"으로 센다
- 데이터셋 설명을 한 번에 받는 SCHEMATA_OPTIONS는 공개 프로젝트의 datasets.get 권한이 없어 쓰지 못한다(dry-run 확인).
  거르기에서 남은 것만 `bq show`를 동시에 부른다. 설명 첫 줄이 형식 문구(Data Updated On 등)면 다음 문장을 낸다. 원문 그대로
- 기준값(500 MB, ai_dev)은 common·harness_config 상수에서 읽는다
- 판정(테이블마다): 외부 테이블 불가 / 테이블·뷰·외부가 아닌 것(ML 모델 등) 불가 / 날짜 분할(이름_YYYYMMDD가 2개 이상) 불가 /
  뷰 조건부(쓸 컬럼 dry-run이 500 MB 이하면 snapshot만) / 500 MB 이하 가능(snapshot) / 500 MB 초과 불가(이 안내의 범위 밖).
  --allow-large: 500 MB 초과 + 날짜 파티션 조건부(incremental, 일 단위 지표만) / 500 MB 초과 + 파티션 없음 불가.
  판정은 종류·크기·파티션·이름 모양으로만 정한다. 개인정보 후보(컬럼 이름을 밑줄로 나눈 단어가 PII_WORDS 중 하나)와
  날짜 칸(DATE·DATETIME·TIMESTAMP 컬럼)은 보이기만 하고 판정을 바꾸지 않는다(개인정보는 사람이 S11에서 확정)
- 데이터셋 판정: 위치가 공개 프로젝트가 아니거나 리전이 ai_dev와 다르면 모든 테이블이 불가
- 종료 코드: 0 쓸 수 있는 것이 1개 이상(거르기는 "가능" 테이블이 있는 데이터셋, 판정표는 가능·조건부 테이블), 1 없음,
  2 조회 실패(권한·네트워크·인증. 여럿이면 하나도 읽지 못했을 때). 사용 오류도 2
- 바깥 명령은 run() 하나(common.Bq의 runner). 시험에서 바꿔 끼운다
"""
import argparse
import csv
import io
import json
import re
import sys
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]  # <root>/.claude/skills/data-harness/scripts/check_source.py
sys.path.insert(0, str(ROOT / "scripts" / "ladder"))
import common  # noqa: E402
import harness_config  # noqa: E402

PUBLIC = "bigquery-public-data"
PII_WORDS = {"email", "name", "phone", "address", "ip", "latitude", "longitude", "lat", "lon",
             "birth", "postal", "zip", "geom"}
DATE_TYPES = {"DATE", "DATETIME", "TIMESTAMP"}
SHARD = re.compile(r"^(.+)_(\d{8})$")
NAME = re.compile(r"[A-Za-z0-9_]+")
TABLE_NAME = re.compile(r"[A-Za-z0-9_-]+")
KIND = {1: "테이블", 2: "뷰", 3: "외부"}
ORDER = {"가능": 0, "조건부": 1, "불가": 2}
MB = 1024 * 1024
# 설명 앞의 날짜·형식 문구. 이 줄은 건너뛴다
FORMAT_LINE = re.compile(r"(?:data\s+)?(?:last\s+)?updated\s*(?:on\b|:).*|[\d\s./:-]*", re.I)
LABEL_HEAD = re.compile(r"^(?:overview|description|about|summary)\s*(?::\s*|$)", re.I)
SENTENCE_END = re.compile(r"(?<=[.!?])\s+(?=[A-Z])")
TEXT_MAX = 200
BATCH = 20  # 한 쿼리에 묶는 데이터셋 수. INFORMATION_SCHEMA는 참조마다 최소 10 MB라 상한 500 MB 안에 둔다
WORKERS = 8  # 동시에 부르는 bq show 수. 이 PC에서 4·8·16의 걸린 시간이 비슷했다(개당 약 3초로 막힘)


class Stop(Exception):
    """조회 실패 (종료 코드 2)."""


def run(args, env, stdin=None):
    """bq·gcloud 실행 (종료 코드, 표준 출력, 표준 오류). 시험에서 바꿔 끼운다."""
    return common.subprocess_runner(args, env, stdin)


def size_text(n):
    if n is None:
        return "-"
    if n < MB:
        return "1 MB 미만"
    return f"{n / 1024 / MB:.1f} GB" if n >= 1024 * MB else f"{n / MB:.0f} MB"


def pii_candidates(columns):
    return [c for c in columns if set(c.lower().split("_")) & PII_WORDS]


def first_sentence(text):
    """설명의 첫 내용 문장(원문). 날짜·형식 문구 줄과 'Overview:' 같은 머리말은 건너뛴다. 없으면 빈 글자."""
    for line in re.split(r"[\r\n]+", text or ""):
        line = re.sub(r"\s+", " ", line).strip(" #*_\"")
        if FORMAT_LINE.fullmatch(line):
            continue
        line = LABEL_HEAD.sub("", line).strip()
        if line and not line.endswith(":"):  # "…:"로 끝나는 줄은 다음 내용의 머리말
            sentence = SENTENCE_END.split(line)[0]
            return sentence if len(sentence) <= TEXT_MAX else sentence[:TEXT_MAX - 3] + "..."
    return ""


def option_text(value):
    """TABLE_OPTIONS의 option_value(따옴표로 감싼 SQL 문자열)를 글자로. 풀지 못하면 바깥 따옴표만 뗀다."""
    value = (value or "").strip()
    try:
        out = json.loads(value)
        return out if isinstance(out, str) else value
    except ValueError:
        return value.strip('"').replace("\\n", "\n").replace('\\"', '"').replace("\\'", "'")


def judge_table(table, sharded, allow_large=False):
    """테이블 하나의 판정 dict. table: name, type, size_bytes, partition(날짜 파티션 컬럼 또는 None), pii(목록),
    dates(날짜 칸 목록)·description은 없어도 됨."""
    out = {"table": table["name"], "kind": KIND.get(table["type"], "?"), "size": size_text(table["size_bytes"]),
           "partition": table["partition"] or "없음", "load": "-", "dates": list(table.get("dates", ())),
           "pii": table["pii"], "verdict": "가능", "reason": "", "description": table.get("description", "")}
    limit = common.MAX_BYTES
    if table["type"] == 3:
        out.update(size="-", partition="-", verdict="불가", reason="BigQuery 밖 파일을 가리키는 외부 테이블. 읽는 양을 미리 알 수 없음")
    elif table["name"] in sharded:
        out.update(verdict="불가", reason="날짜로 나눠 저장한 테이블(같은 앞부분이 여러 개). 여러 테이블을 한 번에 읽지 않음")
    elif table["type"] == 2:
        out.update(size="-", partition="-", load="snapshot", verdict="조건부",
                   reason="뷰. 쓸 컬럼을 정한 뒤 dry-run으로 다시 판정(500 MB 이하면 snapshot만)")
    elif table["type"] != 1:
        out.update(kind="테이블 아님", size="-", partition="-", verdict="불가",
                   reason="테이블이나 뷰가 아님(ML 모델 등). 데이터를 읽어 올 수 없음")
    elif (table["size_bytes"] or 0) <= limit:
        out["load"] = "snapshot"
    elif not allow_large:
        out.update(verdict="불가", reason="이 안내의 범위 밖(500 MB 초과)")
    elif table["partition"]:
        out.update(load="incremental", verdict="조건부", reason="날짜별 추가 적재만. 일 단위 지표만")
    else:
        out.update(verdict="불가", reason="500 MB 초과이고 날짜 파티션 없음. 한 번에 읽으면 비용 상한을 넘음")
    return out


def judge(dataset_project, location, dev_location, tables, allow_large=False):
    """(데이터셋 판정 dict, 테이블 판정 목록). tables는 judge_table 입력 형식."""
    head = {"dataset": dataset_project, "location": location, "ai_dev_location": dev_location, "verdict": "가능", "reason": ""}
    if not dataset_project.startswith(PUBLIC + "."):
        head.update(verdict="불가", reason=f"{PUBLIC} 밖의 데이터셋")
    elif (location or "").upper() != (dev_location or "").upper():
        head.update(verdict="불가", reason=f"리전 다름: 이 데이터 {location} / ai_dev {dev_location}")
    prefixes = Counter(m.group(1) for t in tables for m in [SHARD.match(t["name"])] if m)
    sharded = {t["name"] for t in tables if (m := SHARD.match(t["name"])) and prefixes[m.group(1)] >= 2}
    rows = [judge_table(t, sharded, allow_large) for t in tables]
    if head["verdict"] == "불가":
        for r in rows:
            r.update(verdict="불가", reason=head["reason"])
    rows.sort(key=lambda r: (ORDER[r["verdict"]], r["table"]))
    return head, rows


# ---------- 조회 ----------

def query(bq, sql, max_rows=100000):
    bq.dry_run(sql)
    return bq.run(sql, max_rows=max_rows)


def tables_sql(d):
    return f"SELECT '{d}' AS dataset, table_id, type, size_bytes FROM `{PUBLIC}.{d}.__TABLES__`"


def columns_sql(d):
    return (f"SELECT '{d}' AS dataset, table_name, column_name, data_type, is_partitioning_column "
            f"FROM `{PUBLIC}.{d}`.INFORMATION_SCHEMA.COLUMNS")


def options_sql(d):
    return (f"SELECT '{d}' AS dataset, table_name, option_value "
            f"FROM `{PUBLIC}.{d}`.INFORMATION_SCHEMA.TABLE_OPTIONS WHERE option_name = 'description'")


def fetch(bq, datasets, select):
    """(행 목록, 읽지 못한 {데이터셋: 이유}). 묶음이 막히면 하나씩 다시 한다. 모두 같은 리전이어야 한다."""
    rows, failed = [], {}
    for i in range(0, len(datasets), BATCH):
        batch = datasets[i:i + BATCH]
        try:
            rows += query(bq, " UNION ALL ".join(select(d) for d in batch))
            continue
        except (common.HaltError, common.QueryError) as e:
            if len(batch) == 1:
                failed[batch[0]] = str(e)
                continue
        for d in batch:
            try:
                rows += query(bq, select(d))
            except (common.HaltError, common.QueryError) as e:
                failed[d] = str(e)
    return rows, failed


def by_dataset(rows):
    out = {}
    for row in rows:
        out.setdefault(row.get("dataset"), []).append(row)
    return out


def together(*calls):
    """인수 없는 함수들을 동시에 부르고 결과를 순서대로. 예외는 그대로 올린다."""
    with ThreadPoolExecutor(max_workers=len(calls)) as pool:
        return [f.result() for f in [pool.submit(c) for c in calls]]


def auth(bq):
    """ai-builder 확인(실행마다 한 번). 프로젝트 ID."""
    try:
        return bq.check_auth()
    except (common.HaltError, common.QueryError) as e:
        raise Stop(str(e)) from None


def dev_region(bq, project):
    """ai_dev 리전 조회. 실행마다 한 번."""
    try:
        return bq.dataset_location(project, harness_config.DEV_DATASET)
    except (common.HaltError, common.QueryError) as e:
        raise Stop(str(e)) from None


def public_locations(bq):
    """공개 데이터셋 {이름: 리전}. 목록 조회 한 번(쿼리가 아니라 스캔 비용 없음)."""
    code, out, err = bq.call(["bq", "ls", f"--project_id={PUBLIC}", "--max_results=1000", "--format=json"])
    if code != 0:
        raise Stop(f"공개 데이터셋 목록 조회 실패: {common.reason_text(err + out)}")
    try:
        return {r["datasetReference"]["datasetId"]: r.get("location") for r in json.loads(out)}
    except (ValueError, KeyError, TypeError):
        raise Stop("공개 데이터셋 목록을 읽지 못함") from None


def show_all(bq, datasets):
    """데이터셋마다 정보(dict) 또는 실패 이유(글자). 동시에 부른다."""
    def one(d):
        try:
            return bq.dataset_info(PUBLIC, d)
        except (common.HaltError, common.QueryError) as e:
            return str(e)
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        return dict(zip(datasets, pool.map(one, datasets)))


def table_inputs(tables, columns=(), options=()):
    """한 데이터셋의 조회 행 → judge 입력 목록."""
    cols_of, described = {}, {o.get("table_name"): option_text(o.get("option_value")) for o in options}
    for c in columns:
        cols_of.setdefault(c.get("table_name"), []).append(c)
    out = []
    for t in tables:
        name = t.get("table_id")
        cols = cols_of.get(name, [])
        dated = [c for c in cols if str(c.get("data_type", "")).upper() in DATE_TYPES]
        partition = next((c["column_name"] for c in dated if c.get("is_partitioning_column") == "YES"), None)
        out.append({"name": name, "type": int(t.get("type") or 0),
                    "size_bytes": None if t.get("size_bytes") in (None, "") else int(t["size_bytes"]),
                    "partition": partition, "dates": [c["column_name"] for c in dated],
                    "pii": pii_candidates([c.get("column_name", "") for c in cols]),
                    "description": first_sentence(described.get(name, ""))})
    return out


def check_datasets(bq, datasets, allow_large=False):
    """([(데이터셋 판정, 테이블 판정 목록)...], 읽지 못한 {데이터셋: 이유})."""
    project = auth(bq)
    dev, infos = together(lambda: dev_region(bq, project), lambda: show_all(bq, datasets))
    results, failed, regions = {}, {}, {}
    for d, info in infos.items():
        location = info.get("location") if isinstance(info, dict) else None
        if not location:
            failed[d] = info if isinstance(info, str) else "리전을 읽지 못함"
            continue
        regions.setdefault(location.upper(), []).append((d, location, first_sentence(info.get("description"))))
    for members in regions.values():
        names, parts = [m[0] for m in members], []
        for rows, bad in together(*[lambda s=s: fetch(bq, names, s) for s in (tables_sql, columns_sql, options_sql)]):
            parts.append(by_dataset(rows))
            failed.update(bad)
        for d, location, text in members:
            if d not in failed:
                head, rows = judge(f"{PUBLIC}.{d}", location, dev, table_inputs(*(p.get(d, []) for p in parts)), allow_large)
                head["description"] = text
                results[d] = (head, rows)
    return [results[d] for d in datasets if d in results], failed


def filter_datasets(bq, datasets):
    """S8 후보 거르기: ai_dev와 같은 리전이고 "가능"(500 MB 이하, snapshot) 테이블이 1개 이상인 데이터셋만."""
    project = auth(bq)
    dev, locations = together(lambda: dev_region(bq, project), lambda: public_locations(bq))
    failed = {d: "공개 데이터셋 목록에 없음" for d in datasets if not locations.get(d)}
    known = [d for d in datasets if d not in failed]
    same = [d for d in known if locations[d].upper() == dev.upper()]
    rows, bad = fetch(bq, same, tables_sql)
    failed.update(bad)
    grouped = by_dataset(rows)
    kept, too_big = [], []
    for d in same:
        if d in bad:
            continue
        _, judged = judge(f"{PUBLIC}.{d}", locations[d], dev, table_inputs(grouped.get(d, [])))
        usable = sum(r["verdict"] == "가능" for r in judged)
        if usable:
            kept.append({"dataset": d, "location": locations[d], "usable_tables": usable})
        else:
            too_big.append(d)
    kept.sort(key=lambda k: k["dataset"])
    infos = show_all(bq, [k["dataset"] for k in kept])
    for k in kept:
        info = infos[k["dataset"]]
        k["description"] = first_sentence(info.get("description")) if isinstance(info, dict) else ""
    return {"ai_dev_location": dev, "asked": len(datasets), "candidates": kept,
            "dropped": {"region": sorted(set(known) - set(same)), "size": sorted(too_big), "unreadable": sorted(failed)}}


def walk(fields, prefix=""):
    """스키마 칸 목록. 중첩 칸은 a.b로 편다."""
    for c in fields or []:
        name = prefix + c.get("name", "")
        yield {"column": name, "type": c.get("type", "") + (" 반복" if c.get("mode") == "REPEATED" else ""),
               "description": re.sub(r"\s+", " ", c.get("description") or "").strip()}
        yield from walk(c.get("fields"), name + ".")


def table_detail(bq, dataset, table):
    auth(bq)
    code, out, err = bq.call(["bq", "show", "--format=json", f"{PUBLIC}:{dataset}.{table}"])
    if code != 0:
        raise Stop(f"{dataset}.{table} 조회 실패: {common.reason_text(err + out)}")
    try:
        info = json.loads(out.strip().splitlines()[-1])
        columns = list(walk(info.get("schema", {}).get("fields")))
    except (ValueError, IndexError, AttributeError):
        raise Stop(f"{dataset}.{table} 조회 결과를 읽지 못함") from None
    return {"table": f"{PUBLIC}.{dataset}.{table}", "columns": columns,
            "description": re.sub(r"\s+", " ", info.get("description") or "").strip()}


# ---------- 출력 ----------

def csv_line(values):
    """쉼표가 든 칸만 따옴표로 감싼 한 줄."""
    buf = io.StringIO()
    csv.writer(buf, lineterminator="").writerow(values)
    return buf.getvalue()


def render(head, rows):
    lines = [f"데이터셋: {head['dataset']}, 리전 {head['location']} (ai_dev {head['ai_dev_location']}), 판정 {head['verdict']}"
             + (f", {head['reason']}" if head["reason"] else ""),
             f"설명(원문): {head.get('description') or '없음'}",
             "테이블,종류,크기,날짜 파티션,적재 방식,날짜 칸,개인정보 후보,판정,이유,설명(원문)"]
    for r in rows:
        lines.append(csv_line([r["table"], r["kind"], r["size"], r["partition"], r["load"], " ".join(r["dates"]) or "없음",
                               " ".join(r["pii"]) or "없음", r["verdict"], r["reason"], r["description"]]))
    return "\n".join(lines)


def render_filter(result):
    drop = result["dropped"]
    lines = [f"후보 {len(result['candidates'])}개 (물어본 것 {result['asked']}개, ai_dev 리전 {result['ai_dev_location']})",
             "데이터셋,리전,쓸 수 있는 테이블 수,설명(원문)"]
    lines += [csv_line([c["dataset"], c["location"], c["usable_tables"], c["description"]]) for c in result["candidates"]]
    lines += ["", f"리전이 달라서 뺀 것 {len(drop['region'])}개",
              f"500 MB 이하 테이블이 없어서 뺀 것 {len(drop['size'])}개",
              f"정보를 읽지 못한 것 {len(drop['unreadable'])}개"]
    return "\n".join(lines)


def render_table(detail):
    lines = [f"테이블: {detail['table']}", f"설명(원문): {detail['description'] or '없음'}", "칸,타입,설명(원문)"]
    return "\n".join(lines + [csv_line([c["column"], c["type"], c["description"]]) for c in detail["columns"]])


def parse_args(argv):
    p = argparse.ArgumentParser(description="/data-harness S8·S9 원천 판정 (메타데이터만)")
    which = p.add_mutually_exclusive_group(required=True)
    which.add_argument("--dataset", help=f"{PUBLIC} 안의 데이터셋 이름 (앞에 {PUBLIC}. 를 붙여도 됨)")
    which.add_argument("--datasets", help="데이터셋 이름 여럿(쉼표로)")
    p.add_argument("--filter", action="store_true", help="S8 후보 거르기: 쓸 수 있는 데이터셋만")
    p.add_argument("--table", help="테이블 하나의 설명과 칸 목록 (--dataset과 함께)")
    p.add_argument("--allow-large", action="store_true", help="손으로 하는 길: 500 MB 초과 + 날짜 파티션을 조건부로")
    p.add_argument("--json", action="store_true", help="JSON으로 출력")
    args = p.parse_args(argv)
    if args.table and (not args.dataset or args.filter):
        p.error("--table은 --dataset과만 함께 쓴다")
    if args.allow_large and (args.filter or args.table):
        p.error("--allow-large는 판정표에만 쓴다")
    return args


def main(argv=None, bq=None):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass
    args = parse_args(argv)

    def out(data, text):
        print(json.dumps(data, ensure_ascii=False) if args.json else text)

    datasets = []
    for dataset in [args.dataset] if args.dataset else [d.strip() for d in args.datasets.split(",") if d.strip()]:
        if "." in dataset or ":" in dataset:
            project, _, dataset = dataset.replace(":", ".").partition(".")
            if project != PUBLIC:
                head, rows = judge(f"{project}.{dataset}", None, None, [])
                out({"dataset": head, "tables": rows}, render(head, rows))
                return 1
        if not NAME.fullmatch(dataset):
            print(f"멈춤: 데이터셋 이름은 영문·숫자·밑줄만: {dataset!r}", file=sys.stderr)
            return 2
        if dataset not in datasets:
            datasets.append(dataset)
    if not datasets or (args.table and not TABLE_NAME.fullmatch(args.table)):
        print("멈춤: 데이터셋이나 테이블 이름이 맞지 않음", file=sys.stderr)
        return 2
    if bq is None:
        common.apply_kit_local()
        bq = common.Bq(runner=run)
    try:
        if args.table:
            detail = table_detail(bq, datasets[0], args.table)
            out(detail, render_table(detail))
            return 0
        if args.filter:
            result = filter_datasets(bq, datasets)
            if len(result["dropped"]["unreadable"]) == len(datasets):
                raise Stop("읽을 수 있는 데이터셋이 없음")
            out(result, render_filter(result))
            return 0 if result["candidates"] else 1
        results, failed = check_datasets(bq, datasets, args.allow_large)
        if not results:
            raise Stop("; ".join(f"{d}: {why}" for d, why in failed.items()))
    except Stop as e:
        print(f"조회 실패: {e}", file=sys.stderr)
        print("데이터 정보를 읽지 못했습니다. 데이터 문제가 아니라 연결이나 권한 문제입니다.")
        return 2
    items = [{"dataset": head, "tables": rows} for head, rows in results]
    text = "\n\n".join(render(head, rows) for head, rows in results)
    if failed:
        text += "\n\n정보를 읽지 못한 것: " + " ".join(sorted(failed))
    out(items[0] if args.dataset else {"results": items, "unreadable": sorted(failed)}, text)
    return 0 if any(r["verdict"] != "불가" for _, rows in results for r in rows) else 1


if __name__ == "__main__":
    sys.exit(main())
