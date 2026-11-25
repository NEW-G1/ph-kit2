"""/data-harness S9 원천 판정 시험. bq·gcloud는 가짜 runner로 바꾼다(실제 BigQuery 없음).
판정 규칙(reference/data_picking.md 2절 표)과 조회 방식(메타데이터만, dry-run 먼저, 비용 상한)을 고정한다."""
import csv
import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "ladder"))
import common  # noqa: E402

SCRIPT = ROOT / ".claude" / "skills" / "data-harness" / "scripts" / "check_source.py"
spec = importlib.util.spec_from_file_location("check_source", SCRIPT)
check_source = importlib.util.module_from_spec(spec)
spec.loader.exec_module(check_source)

MB = 1024 * 1024


def table(name, kind=1, size_mb=10, partition=None, pii=()):
    return {"name": name, "type": kind, "size_bytes": None if kind != 1 else int(size_mb * MB),
            "partition": partition, "pii": list(pii)}


def verdicts(tables, location="US", dev="US", dataset="bigquery-public-data.d", allow_large=False):
    head, rows = check_source.judge(dataset, location, dev, tables, allow_large)
    return head, {r["table"]: (r["verdict"], r["load"]) for r in rows}


def test_small_table_is_ok_snapshot():
    assert verdicts([table("daily_counts", size_mb=120)])[1] == {"daily_counts": ("가능", "snapshot")}


def test_exactly_limit_is_ok():
    t = table("t")
    t["size_bytes"] = common.MAX_BYTES
    assert verdicts([t])[1]["t"][0] == "가능"


def test_big_partitioned_is_out_of_this_guide():
    """500 MB 초과는 날짜 파티션이 있어도 불가(초보자 경로는 snapshot 하나)."""
    _, rows = check_source.judge("bigquery-public-data.d", "US", "US",
                                 [table("events", size_mb=3200, partition="event_date"), table("logs", size_mb=600)])
    assert {(r["verdict"], r["load"], r["reason"]) for r in rows} == {("불가", "-", "이 안내의 범위 밖(500 MB 초과)")}


def test_allow_large_keeps_old_judgement():
    v = verdicts([table("events", size_mb=3200, partition="event_date"), table("logs", size_mb=600)], allow_large=True)[1]
    assert v == {"events": ("조건부", "incremental"), "logs": ("불가", "-")}


def test_view_is_conditional_snapshot_only():
    assert verdicts([table("summary_view", kind=2)])[1] == {"summary_view": ("조건부", "snapshot")}


def test_external_is_no():
    assert verdicts([table("ext", kind=3)])[1]["ext"][0] == "불가"


def test_date_sharded_needs_two_or_more():
    _, v = verdicts([table("logs_20240101"), table("logs_20240102"), table("report_20240101"), table("plain")])
    assert v["logs_20240101"][0] == v["logs_20240102"][0] == "불가"
    assert v["report_20240101"][0] == "가능" and v["plain"][0] == "가능"


def test_pii_does_not_change_verdict():
    head, rows = check_source.judge("bigquery-public-data.d", "US", "US",
                                    [table("users", pii=["email"]), table("events", size_mb=900, partition="d", pii=["ip_address"])],
                                    allow_large=True)
    by = {r["table"]: r for r in rows}
    assert (by["users"]["verdict"], by["users"]["load"], by["users"]["reason"]) == ("가능", "snapshot", "")
    assert (by["events"]["verdict"], by["events"]["load"]) == ("조건부", "incremental")
    assert "개인정보" not in by["events"]["reason"]
    assert by["users"]["pii"] == ["email"] and by["events"]["pii"] == ["ip_address"]


def test_model_is_no_with_clear_reason():
    """__TABLES__에 1·2·3이 아닌 종류로 나오는 것(실데이터: austin_bikeshare의 ARIMA_PLUS 모델)."""
    _, rows = check_source.judge("bigquery-public-data.d", "US", "US", [{"name": "m", "type": 4, "size_bytes": 0,
                                                                          "partition": None, "pii": []}])
    assert (rows[0]["verdict"], rows[0]["kind"], rows[0]["size"]) == ("불가", "테이블 아님", "-")
    assert "ML 모델" in rows[0]["reason"]


@pytest.mark.parametrize("n,text", [(15378, "1 MB 미만"), (0, "1 MB 미만"), (MB, "1 MB"), (318 * MB, "318 MB"),
                                    (None, "-"), (2048 * MB, "2.0 GB")])
def test_size_text(n, text):
    assert check_source.size_text(n) == text


@pytest.mark.parametrize("column,hit", [
    ("ip", True), ("ip_address", True), ("trip", False), ("trip_id", False), ("user_geom", True),
    ("first_name", True), ("username", False), ("Latitude", True), ("zipcode", False), ("birth_date", True),
])
def test_pii_word_rule(column, hit):
    assert bool(check_source.pii_candidates([column])) is hit


def test_other_region_makes_all_no():
    head, v = verdicts([table("a"), table("b")], location="EU", dev="US")
    assert head["verdict"] == "불가" and "리전 다름" in head["reason"]
    assert set(x[0] for x in v.values()) == {"불가"}


def test_region_compare_ignores_case():
    assert verdicts([table("a")], location="us", dev="US")[0]["verdict"] == "가능"


def test_rows_sorted_ok_conditional_no():
    head, rows = check_source.judge("bigquery-public-data.d", "US", "US",
                                    [table("z_no", kind=3), table("b_cond", kind=2), table("a_ok"), table("c_ok")])
    assert [r["table"] for r in rows] == ["a_ok", "c_ok", "b_cond", "z_no"]


def test_render_is_one_csv_line_per_table():
    head, rows = check_source.judge("bigquery-public-data.d", "EU", "US",
                                    [table("a", size_mb=900), dict(table("b", pii=["email", "phone"]), dates=["d1", "d2"],
                                                                   description="Trips, by day.")])
    lines = check_source.render(head, rows).splitlines()
    assert lines[2] == "테이블,종류,크기,날짜 파티션,적재 방식,날짜 칸,개인정보 후보,판정,이유,설명(원문)"
    cells = list(csv.reader(lines[3:]))
    assert [len(c) for c in cells] == [10, 10]
    assert cells[1][5] == "d1 d2" and cells[1][6] == "email phone" and cells[1][9] == "Trips, by day."


@pytest.mark.parametrize("text,out", [
    ("Data Updated On : 2021-09-10\nOverview: Tsunami data. More text.", "Tsunami data."),
    ("Overview: This dataset was created by NOAA.  Second.", "This dataset was created by NOAA."),
    ("Last updated: 2020-01-01\r\n2020-01-01\n\nTrips in the U.S. by day", "Trips in the U.S. by day"),
    ("According to NCEI:\n\"The database has quakes. It\"", "The database has quakes."),
    ("Updated hourly weather readings.", "Updated hourly weather readings."),
    ("Overview", ""), ("", ""), (None, ""),
])
def test_first_sentence(text, out):
    assert check_source.first_sentence(text) == out


def test_first_sentence_is_cut():
    assert len(check_source.first_sentence("a" * 500)) == check_source.TEXT_MAX


@pytest.mark.parametrize("value,out", [('"Line one.\\nLine two."', "Line one.\nLine two."),
                                       ('"It\\\'s fine"', "It's fine"), (None, "")])
def test_option_text(value, out):
    assert check_source.option_text(value) == out


class FakeBq:
    """gcloud·bq 응답 흉내. 받은 명령을 calls에 남긴다."""

    def __init__(self, tables, columns, public_location="US", dev_location="US", fail=None):
        self.tables, self.columns = tables, columns
        self.locations = {"proj-x:ai_dev": dev_location, "bigquery-public-data:d": public_location}
        self.fail = fail
        self.calls = []

    def __call__(self, args, env, stdin=None):
        self.calls.append((list(args), stdin))
        if args[:2] == ["gcloud", "auth"]:
            return 0, "person@example.com\n", ""
        if args[-1] == "auth/impersonate_service_account":
            return 0, "ai-builder@proj-x.iam.gserviceaccount.com\n", ""
        if args[-1] == "project":
            return 0, "proj-x\n", ""
        if args[:2] == ["bq", "show"]:
            if self.fail == "show":
                return 1, "", "Access Denied: Dataset bigquery-public-data:d"
            return 0, json.dumps({"location": self.locations[args[-1]]}), ""
        if "--dry_run" in args:
            return 0, json.dumps({"statistics": {"totalBytesProcessed": "10485760"}}), ""
        rows = (self.tables if "__TABLES__" in stdin else
                [] if "TABLE_OPTIONS" in stdin else self.columns)
        return 0, json.dumps([dict(r, dataset="d") for r in rows]), ""


def fake_bq(**kw):
    fake = FakeBq(**kw)
    return fake, common.Bq(runner=fake, env={"CLOUDSDK_CONFIG": "x"})


TABLES = [{"table_id": "orders", "type": "1", "size_bytes": str(50 * MB)},
          {"table_id": "events", "type": "1", "size_bytes": str(2048 * MB)},
          {"table_id": "v_summary", "type": "2", "size_bytes": "0"}]
COLUMNS = [{"table_name": "orders", "column_name": "order_id", "data_type": "INT64", "is_partitioning_column": "NO"},
           {"table_name": "events", "column_name": "ip_address", "data_type": "STRING", "is_partitioning_column": "NO"},
           {"table_name": "events", "column_name": "event_date", "data_type": "DATE", "is_partitioning_column": "YES"}]


def test_main_end_to_end(capsys):
    fake, bq = fake_bq(tables=TABLES, columns=COLUMNS)
    assert check_source.main(["--dataset", "d", "--json"], bq=bq) == 0
    out = json.loads(capsys.readouterr().out)
    by = {r["table"]: r for r in out["tables"]}
    assert by["orders"]["verdict"] == "가능" and by["orders"]["load"] == "snapshot"
    assert by["events"]["verdict"] == "불가" and by["events"]["partition"] == "event_date"
    assert by["events"]["dates"] == ["event_date"] and by["orders"]["dates"] == []
    assert by["events"]["pii"] == ["ip_address"] and by["v_summary"]["kind"] == "뷰"


def test_queries_are_metadata_only_dry_run_first_and_capped(capsys):
    fake, bq = fake_bq(tables=TABLES, columns=COLUMNS)
    check_source.main(["--dataset", "d"], bq=bq)
    assert_safe_queries(fake, 3)


def assert_safe_queries(fake, kinds):
    """조회마다 dry-run 다음 본 실행, 상한, 메타데이터만(동시에 돌아 명령이 섞이므로 SQL별로 본다)."""
    queries = {}
    for args, sql in fake.calls:
        if args[:2] == ["bq", "query"]:
            queries.setdefault(sql, []).append(args)
    assert len(queries) == kinds
    for sql, (dry, real) in queries.items():
        assert "--dry_run" in dry and "--dry_run" not in real
        assert f"--maximum_bytes_billed={common.MAX_BYTES}" in dry and f"--maximum_bytes_billed={common.MAX_BYTES}" in real
        assert any(x in sql for x in ("__TABLES__", "INFORMATION_SCHEMA.COLUMNS", "INFORMATION_SCHEMA.TABLE_OPTIONS"))
        assert "SELECT *" not in sql.upper()


def test_all_no_exits_1(capsys):
    fake, bq = fake_bq(tables=TABLES, columns=COLUMNS, public_location="EU")
    assert check_source.main(["--dataset", "d"], bq=bq) == 1
    assert "리전 다름" in capsys.readouterr().out


def test_query_failure_exits_2(capsys):
    fake, bq = fake_bq(tables=TABLES, columns=COLUMNS, fail="show")
    assert check_source.main(["--dataset", "d"], bq=bq) == 2
    assert "연결이나 권한 문제" in capsys.readouterr().out


def test_not_ai_builder_exits_2(capsys):
    def runner(args, env, stdin=None):
        if args[:2] == ["gcloud", "auth"]:
            return 0, "person@example.com\n", ""
        return 0, "(unset)\n", ""
    bq = common.Bq(runner=runner, env={"CLOUDSDK_CONFIG": "x"})
    assert check_source.main(["--dataset", "d"], bq=bq) == 2


def test_other_project_is_no_without_query(capsys):
    assert check_source.main(["--dataset", "other-proj.d"], bq=object()) == 1
    assert "bigquery-public-data 밖" in capsys.readouterr().out


def test_bad_name_is_usage_error(capsys):
    assert check_source.main(["--dataset", "d; drop"], bq=object()) == 2


def test_public_prefix_accepted(capsys):
    fake, bq = fake_bq(tables=TABLES, columns=COLUMNS)
    assert check_source.main(["--dataset", "bigquery-public-data.d"], bq=bq) == 0


# ---------- 여러 데이터셋과 후보 거르기 ----------

class ManyBq:
    """데이터셋 여럿. data: {이름: (리전, [(테이블, 종류, MB)])}. denied는 조회가 막힌 데이터셋."""

    def __init__(self, data, denied=()):
        self.data, self.denied, self.calls = data, set(denied), []

    def __call__(self, args, env, stdin=None):
        self.calls.append((list(args), stdin))
        if args[:2] == ["gcloud", "auth"]:
            return 0, "person@example.com\n", ""
        if args[-1] == "auth/impersonate_service_account":
            return 0, "ai-builder@proj-x.iam.gserviceaccount.com\n", ""
        if args[-1] == "project":
            return 0, "proj-x\n", ""
        if args[:2] == ["bq", "ls"]:
            return 0, json.dumps([{"datasetReference": {"datasetId": d}, "location": v[0]}
                                  for d, v in self.data.items()]), ""
        if args[:2] == ["bq", "show"]:
            name = args[-1].split(":")[1]
            if "." in name:
                return 0, json.dumps({"description": "Trip rows.", "schema": {"fields": [
                    {"name": "id", "type": "INTEGER", "description": "Row id"},
                    {"name": "geo", "type": "RECORD", "mode": "REPEATED", "fields": [{"name": "x", "type": "FLOAT"}]}]}}), ""
            if name == "ai_dev":
                return 0, json.dumps({"location": "US"}), ""
            return 0, json.dumps({"location": self.data[name][0], "description": f"About {name} data."}), ""
        names = [d for d in self.data if f"'{d}'" in stdin]
        if self.denied & set(names):
            return 1, "", "Access Denied: Dataset"
        if "--dry_run" in args:
            return 0, json.dumps({"statistics": {"totalBytesProcessed": "0"}}), ""
        if "__TABLES__" not in stdin:
            return 0, "[]", ""
        return 0, json.dumps([{"dataset": d, "table_id": t, "type": str(k), "size_bytes": str(int(mb * MB))}
                              for d in names for t, k, mb in self.data[d][1]]), ""

    def count(self, *head):
        return sum(args[:len(head)] == list(head) for args, _ in self.calls)


MANY = {"b_ok": ("US", [("t", 1, 10), ("big", 1, 900)]), "a_ok": ("us", [("t", 1, 1)]), "eu": ("EU", [("t", 1, 1)]),
        "big": ("US", [("t", 1, 900), ("v", 2, 0)]), "shard": ("US", [("l_20240101", 1, 1), ("l_20240102", 1, 1)])}


def many(**kw):
    fake = ManyBq(MANY, **kw)
    return fake, common.Bq(runner=fake, env={"CLOUDSDK_CONFIG": "x"})


def test_filter_keeps_usable_and_counts_dropped(capsys):
    fake, bq = many()
    assert check_source.main(["--datasets", "b_ok,a_ok,eu,big,shard,gone", "--filter", "--json"], bq=bq) == 0
    out = json.loads(capsys.readouterr().out)
    assert [(c["dataset"], c["usable_tables"], c["description"]) for c in out["candidates"]] == [
        ("a_ok", 1, "About a_ok data."), ("b_ok", 1, "About b_ok data.")]
    assert out["dropped"] == {"region": ["eu"], "size": ["big", "shard"], "unreadable": ["gone"]}
    assert_safe_queries(fake, 1)  # __TABLES__ 한 번에 묶음
    assert fake.count("bq", "ls") == 1 and fake.count("gcloud", "auth") == 1
    shown = sorted(a[-1].split(":")[1] for a, _ in fake.calls if a[:2] == ["bq", "show"])
    assert shown == ["a_ok", "ai_dev", "b_ok"]  # 설명은 남은 것만, ai_dev는 한 번


def test_filter_text_lists_counts(capsys):
    _, bq = many()
    check_source.main(["--datasets", "b_ok,eu,big", "--filter"], bq=bq)
    out = capsys.readouterr().out
    assert "리전이 달라서 뺀 것 1개" in out and "500 MB 이하 테이블이 없어서 뺀 것 1개" in out and "읽지 못한 것 0개" in out


def test_filter_denied_dataset_is_unreadable_only(capsys):
    fake, bq = many(denied={"big"})
    assert check_source.main(["--datasets", "a_ok,b_ok,big", "--filter", "--json"], bq=bq) == 0
    out = json.loads(capsys.readouterr().out)
    assert [c["dataset"] for c in out["candidates"]] == ["a_ok", "b_ok"] and out["dropped"]["unreadable"] == ["big"]


def test_filter_none_exits_1_and_all_unreadable_exits_2(capsys):
    assert check_source.main(["--datasets", "eu,big", "--filter"], bq=many()[1]) == 1
    assert check_source.main(["--datasets", "big", "--filter"], bq=many(denied={"big"})[1]) == 2


def test_datasets_table_uses_one_query_per_kind(capsys):
    fake, bq = many()
    assert check_source.main(["--datasets", "a_ok,b_ok,eu", "--json"], bq=bq) == 0
    out = json.loads(capsys.readouterr().out)
    assert [r["dataset"]["verdict"] for r in out["results"]] == ["가능", "가능", "불가"]
    assert_safe_queries(fake, 6)  # 리전 2개 × 3종
    assert fake.count("gcloud", "auth") == 1


def test_batches_split(monkeypatch):
    monkeypatch.setattr(check_source, "BATCH", 2)
    fake, bq = many()
    rows, failed = check_source.fetch(bq, ["a_ok", "b_ok", "big"], check_source.tables_sql)
    assert not failed and {r["dataset"] for r in rows} == {"a_ok", "b_ok", "big"}
    assert_safe_queries(fake, 2)


def test_table_detail(capsys):
    fake, bq = many()
    assert check_source.main(["--dataset", "a_ok", "--table", "t"], bq=bq) == 0
    out = capsys.readouterr().out
    assert "Trip rows." in out and "id,INTEGER,Row id" in out and "geo,RECORD 반복," in out and "geo.x,FLOAT," in out
    assert fake.count("bq", "query") == 0


@pytest.mark.parametrize("argv", [["--datasets", "a,b", "--table", "t"], ["--dataset", "a", "--datasets", "b"], [],
                                  ["--datasets", "a", "--filter", "--allow-large"]])
def test_usage_errors(argv):
    with pytest.raises(SystemExit) as e:
        check_source.main(argv, bq=object())
    assert e.value.code == 2


@pytest.mark.parametrize("argv", [["--dataset", "a", "--table", "t;x"], ["--datasets", "a,b`c"], ["--datasets", ","]])
def test_bad_names_never_reach_bq(argv):
    assert check_source.main(argv, bq=object()) == 2
