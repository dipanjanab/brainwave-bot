from pathlib import Path
import re


KNOWLEDGE_DIR = Path(__file__).resolve().parents[2] / "knowledge"


def retrieve_business_context(question: str, limit: int = 2) -> str:
    """Return the most relevant local business definitions without sending data away."""
    tokens = {token.lower() for token in re.findall(r"[a-zA-Z0-9]+", question) if len(token) > 2}
    scored: list[tuple[int, str]] = []
    for document in KNOWLEDGE_DIR.glob("*.md"):
        content = document.read_text(encoding="utf-8")
        score = sum(token in content.lower() for token in tokens)
        if score:
            scored.append((score, content))
    return "\n\n---\n\n".join(content for _, content in sorted(scored, reverse=True)[:limit])
