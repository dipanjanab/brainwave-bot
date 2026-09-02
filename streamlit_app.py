import streamlit as st
from app.agents.workflow import ask_agent


st.set_page_config(page_title="Brainwave Bot", page_icon="🧠", layout="centered")
st.title("🧠 Brainwave Bot")
st.caption("Ask governed questions about submitted business stories.")

question = st.text_input("Question", placeholder="How many NEMIA stories were submitted in FY26?")
if st.button("Ask Brainwave", type="primary", disabled=not question):
    result = ask_agent(question)
    st.success(result["answer"])
    st.caption(f"Execution mode: {result['mode']}")
    if result["period"]:
        p = result["period"]
        st.caption(f"Resolved period: {p['label']} · {p['start_date']} to {p['end_date']} (exclusive)")
    with st.expander("Show query trace"):
        st.code(result["sql"], language="sql")
        st.write({"parameters": result["parameters"]})

st.divider()
st.caption("Try: “How many stories were submitted in FY26?”, “NEMIA revenue in FY26”, or “submissions by market this year”.")
