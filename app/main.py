import re
from app.database.seed import seed_database
from app.services.date_resolver import resolve_period
from app.tools.sql_tool import run_read_only_sql


MARKETS = ("NEMIA", "APAC", "AMER", "LATAM")


def _market(question: str) -> str | None:
    upper = question.upper()
    return next((market for market in MARKETS if market in upper), None)


def ask(question: str, today=None) -> dict:
    """Deterministic V1 question handler; replace its planner with an LLM agent later."""
    seed_database()
    market = _market(question)
    period = resolve_period(question, today=today)
    lower = question.lower()
    conditions, params = ["status = 'Submitted'"], []
    if market:
        conditions.append("market = ?")
        params.append(market)
    if period:
        conditions.extend(["submission_date >= ?", "submission_date < ?"])
        params.extend([period["start_date"].isoformat(), period["end_date"].isoformat()])
    where = " WHERE " + " AND ".join(conditions)

    if any(token in lower for token in ("revenue", "value")):
        sql = "SELECT COALESCE(SUM(revenue), 0) AS total_revenue FROM stories" + where
        value = run_read_only_sql(sql, tuple(params))[0]["total_revenue"]
        answer = f"Total submitted-story revenue is ${value:,.0f}."
    elif any(token in lower for token in ("by market", "each market")):
        sql = "SELECT market, COUNT(*) AS story_count FROM stories" + where + " GROUP BY market ORDER BY story_count DESC"
        rows = run_read_only_sql(sql, tuple(params))
        answer = "Submitted stories by market: " + ", ".join(f"{r['market']}: {r['story_count']}" for r in rows) + "."
    else:
        sql = "SELECT COUNT(*) AS story_count FROM stories" + where
        value = run_read_only_sql(sql, tuple(params))[0]["story_count"]
        qualifiers = ""
        if market:
            qualifiers += f" in {market}"
        if period:
            qualifiers += f" during {period['label']}"
        answer = f"{value} submitted stories{qualifiers}."
    return {"answer": answer, "sql": sql, "parameters": params, "period": period}
