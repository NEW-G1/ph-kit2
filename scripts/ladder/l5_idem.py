"""L5 멱등성 (03 §5.3).

L2를 마친 테이블의 ds 파티션 행 수·체크섬을 재고, 같은 ds로 task SQL을 한 번 더 실행한 뒤 다시 잰다.
파티션 컬럼은 contract에서 읽는다(snapshot이면 snapshot_date, incremental이면 load.partition_column, 결정 79).
다르면 idempotency_break. 같으면 _checks/l5/ 중 이 task의 쿼리를 실행한다.
반려 rung의 metrics.message는 행 수와 체크섬 같음/다름만 적는다(체크섬 값은 쓰지 않는다). 반려 기록 detail이 이 문장을 쓴다 (결정 49).
"""
import checks
import common
import l2_run
import load_mode


# 부동소수점(FLOAT64) 컬럼은 체크섬 전에 이 자릿수로 반올림한다. 부동소수점 합계는 더하는 순서에 따라 끝자리가 달라져
# 같은 SQL을 2번 돌려도 체크섬이 다를 수 있다(빌더가 고칠 수 없는 거짓 idempotency_break)
FLOAT_DIGITS = 6
FLOAT_TYPES = {"FLOAT64", "FLOAT"}


def float_columns(contract, table):
    """contract에서 그 테이블의 부동소수점(FLOAT64) 컬럼 이름. 없거나 못 읽으면 빈 튜플."""
    for t in contract.get("tables", []) if isinstance(contract.get("tables"), list) else []:
        if isinstance(t, dict) and t.get("name") == table and isinstance(t.get("columns"), list):
            return tuple(c["name"] for c in t["columns"] if isinstance(c, dict) and isinstance(c.get("name"), str)
                         and isinstance(c.get("type"), str) and c["type"].strip().upper() in FLOAT_TYPES)
    return ()


def snapshot_sql(project, dataset, table, partition_col, ds, floats=()):
    """행 수·체크섬 쿼리 문장(순수 함수). 사다리는 실제 값으로, 대시보드는 자리 표시로 부른다.
    floats(부동소수점(FLOAT64) 컬럼)가 있으면 그 컬럼만 FLOAT_DIGITS 자리로 반올림한 행으로 체크섬을 잰다."""
    source = f"`{project}.{dataset}.{table}`"
    if floats:
        rounded = ", ".join(f"ROUND({c}, {FLOAT_DIGITS}) AS {c}" for c in floats)
        source = f"(SELECT * REPLACE ({rounded}) FROM {source} WHERE {partition_col} = DATE('{ds}'))"
    return (f"SELECT COUNT(*) AS row_count, BIT_XOR(FARM_FINGERPRINT(TO_JSON_STRING(t))) AS checksum\n"
            f"FROM {source} AS t\n"
            f"WHERE {partition_col} = DATE('{ds}')")


def snapshot(ctx, table):
    sql = snapshot_sql(ctx.project, common.DEV_DATASET, table, load_mode.partition_column(ctx.contract), ctx.ds,
                       float_columns(ctx.contract, table))
    ctx.bq.dry_run(sql)
    rows = ctx.bq.run(sql, max_rows=1)
    row = rows[0] if rows else {}
    return {"row_count": row.get("row_count"), "checksum": row.get("checksum")}


def count_text(n):
    try:
        return f"{int(n):,}"
    except (TypeError, ValueError):
        return "없음" if n is None else str(n)


def break_message(first, second):
    same = "같음" if first["checksum"] == second["checksum"] else "다름"
    return (f"같은 ds로 2번 실행한 결과가 다름 (행 수 {count_text(first['row_count'])} → "
            f"{count_text(second['row_count'])}, 체크섬 {same})")


def run(ctx, task):
    table = common.table_of(ctx.contract, task["id"])["name"]
    try:
        first = snapshot(ctx, table)
        l2_run.execute(ctx, task)
        second = snapshot(ctx, table)
    except common.QueryError as e:
        return common.rung("L5", str(ctx.ds), {"message": str(e)}, e.error_type)
    if first != second:
        return common.rung("L5", str(ctx.ds), {"first": first, "second": second,
                                               "message": break_message(first, second),
                                               "evidence": [{"run": 1, **first}, {"run": 2, **second}]},
                           "idempotency_break")
    return checks.run_stage(ctx, task, "l5", {"row_count": first["row_count"]})
