import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from app.agents.workflow import _invoke_llm, _llm_timeout_seconds, formulate_answer


STATE = {
    "question": "How many stories were submitted?",
    "context": "Submitted stories only.",
    "result": {"answer": "7 submitted stories."},
}


class WorkflowFallbackTests(unittest.TestCase):
    def test_timeout_returns_verified_answer(self):
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test"}), patch(
            "app.agents.workflow._invoke_llm", side_effect=TimeoutError("too slow")
        ):
            result = formulate_answer(STATE)

        self.assertEqual(result["answer"], "7 submitted stories.")
        self.assertEqual(result["mode"], "deterministic fallback (LLM timeout)")

    def test_other_llm_failure_returns_verified_answer(self):
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test"}), patch(
            "app.agents.workflow._invoke_llm", side_effect=RuntimeError("provider unavailable")
        ):
            result = formulate_answer(STATE)

        self.assertEqual(result["answer"], "7 submitted stories.")
        self.assertEqual(result["mode"], "deterministic fallback (LLM error)")

    def test_llm_has_deadline_and_no_retries(self):
        fake_model = unittest.mock.Mock()
        fake_model.invoke.return_value = SimpleNamespace(content="LLM answer")
        with patch.dict(
            os.environ,
            {"OPENAI_API_KEY": "test", "BRAINWAVE_LLM_TIMEOUT_SECONDS": "3.5"},
        ), patch("langchain_openai.ChatOpenAI", return_value=fake_model) as model_class:
            answer = _invoke_llm(STATE)

        self.assertEqual(answer, "LLM answer")
        self.assertEqual(model_class.call_args.kwargs["timeout"], 3.5)
        self.assertEqual(model_class.call_args.kwargs["max_retries"], 0)

    def test_invalid_timeout_uses_default(self):
        with patch.dict(os.environ, {"BRAINWAVE_LLM_TIMEOUT_SECONDS": "invalid"}):
            self.assertEqual(_llm_timeout_seconds(), 10.0)


if __name__ == "__main__":
    unittest.main()
