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


class BrainwaveState(TypedDict, total=False):
    question: str
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
    return {"result": ask(state["question"]), "mode": "deterministic"}


def formulate_answer(state: BrainwaveState) -> BrainwaveState:
    result = state["result"]
    if not os.getenv("OPENAI_API_KEY"):
        return {"answer": result["answer"], "mode": "deterministic (no API key configured)"}
    try:
        from langchain_openai import ChatOpenAI

        model = ChatOpenAI(model=os.getenv("BRAINWAVE_MODEL", "gpt-5.6-luna"), temperature=0)
        prompt = f"{SYSTEM_PROMPT}\n\nBusiness context:\n{state['context'] or 'None'}\n\nQuestion: {state['question']}\nVerified result: {result['answer']}"
        response = model.invoke(prompt)
        return {"answer": response.content, "mode": "LangGraph + OpenAI"}
    except Exception:
        # A model outage must never prevent the verified SQL answer from being returned.
        return {"answer": result["answer"], "mode": "deterministic fallback"}


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


def ask_agent(question: str) -> dict:
    """Public agent entry point for API/UI callers."""
    state = _workflow.invoke({"question": question})
    return {
        "answer": state["answer"],
        "sql": state["result"]["sql"],
        "parameters": state["result"]["parameters"],
        "period": state["result"]["period"],
        "context": state["context"],
        "mode": state["mode"],
    }
