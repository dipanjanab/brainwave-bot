"""LangGraph orchestration. The LLM plans; deterministic code owns access control."""
import os
from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from app.main import ask
from app.rag.retriever import retrieve_business_context
from app.services.date_resolver import resolve_period


SYSTEM_PROMPT = """You are the Brainwave data-Q&A planner. Return a concise answer only.
Use the supplied business context for definitions. Fiscal dates and SQL execution are handled
by application code. Never claim data that was not returned by the SQL tool."""

DEFAULT_LLM_TIMEOUT_SECONDS = 10.0


class BrainwaveState(TypedDict, total=False):
    question: str
    market: str | None
    context: str
    period_label: str | None
    result: dict
    answer: str
    mode: str


def retrieve_context(state: BrainwaveState) -> BrainwaveState:
    return {"context": retrieve_business_context(state["question"])}


def resolve_dates(state: BrainwaveState) -> BrainwaveState:
    period = resolve_period(state["question"])
    return {"period_label": period["label"] if period else None}


def query_data(state: BrainwaveState) -> BrainwaveState:
    # The existing handler is the only route to SQL: it parameterizes values and validates SQL.
    return {
        "result": ask(state["question"], market=state.get("market")),
        "mode": "deterministic",
    }


def _llm_timeout_seconds() -> float:
    """Return a safe timeout even when the environment value is invalid."""
    try:
        timeout = float(os.getenv("BRAINWAVE_LLM_TIMEOUT_SECONDS", DEFAULT_LLM_TIMEOUT_SECONDS))
        return timeout if timeout > 0 else DEFAULT_LLM_TIMEOUT_SECONDS
    except (TypeError, ValueError):
        return DEFAULT_LLM_TIMEOUT_SECONDS


def _invoke_llm(state: BrainwaveState) -> str:
    from langchain_openai import ChatOpenAI

    model = ChatOpenAI(
        model=os.getenv("BRAINWAVE_MODEL", "gpt-5.6-luna"),
        temperature=0,
        timeout=_llm_timeout_seconds(),
        max_retries=0,
    )
    prompt = f"{SYSTEM_PROMPT}\n\nBusiness context:\n{state['context'] or 'None'}\n\nQuestion: {state['question']}\nVerified result: {state['result']['answer']}"
    response = model.invoke(prompt)
    return response.content


def _is_timeout(error: Exception) -> bool:
    """Recognize built-in and provider-specific timeout exceptions."""
    current: BaseException | None = error
    while current is not None:
        if isinstance(current, TimeoutError) or "timeout" in type(current).__name__.lower():
            return True
        current = current.__cause__ or current.__context__
    return False


def formulate_answer(state: BrainwaveState) -> BrainwaveState:
    result = state["result"]
    if not os.getenv("OPENAI_API_KEY"):
        return {"answer": result["answer"], "mode": "deterministic (no API key configured)"}
    try:
        return {"answer": _invoke_llm(state), "mode": "LangGraph + OpenAI"}
    except Exception as error:
        # Model failures must never prevent the verified SQL answer from being returned.
        reason = "LLM timeout" if _is_timeout(error) else "LLM error"
        return {"answer": result["answer"], "mode": f"deterministic fallback ({reason})"}


def build_workflow():
    graph = StateGraph(BrainwaveState)
    graph.add_node("retrieve_context", retrieve_context)
    graph.add_node("resolve_dates", resolve_dates)
    graph.add_node("query_data", query_data)
    graph.add_node("formulate_answer", formulate_answer)
    graph.add_edge(START, "retrieve_context")
    graph.add_edge("retrieve_context", "resolve_dates")
    graph.add_edge("resolve_dates", "query_data")
    graph.add_edge("query_data", "formulate_answer")
    graph.add_edge("formulate_answer", END)
    return graph.compile()


_workflow = build_workflow()


def ask_agent(question: str, market: str | None = None) -> dict:
    """Public agent entry point for API/UI callers."""
    state = _workflow.invoke({"question": question, "market": market})
    return {
        "answer": state["answer"],
        "sql": state["result"]["sql"],
        "parameters": state["result"]["parameters"],
        "period": state["result"]["period"],
        "context": state["context"],
        "mode": state["mode"],
    }
