# Brainwave Bot

A local, governed data-Q&A prototype for business-story reporting.

## What works now

- A seeded SQLite database of business stories.
- Fiscal-year resolution for an April–March financial year.
- Parameterized, read-only SQL execution with table allowlisting.
- A LangGraph workflow: local business-context retrieval → date resolution → governed SQL → answer formulation.
- A deterministic fallback when no OpenAI API key is configured.

## Run it

```powershell
python -m unittest discover -s tests -v
streamlit run streamlit_app.py
```

## Example questions

- `How many NEMIA stories were submitted in FY26?`
- `What is NEMIA revenue in FY26?`
- `Show submissions by market this year`

## Next phase

Copy `.env.example` to `.env` and add an OpenAI key to enable LLM answer formulation. The model never receives direct database access; application code continues to resolve dates and execute only validated, parameterized SQL.
