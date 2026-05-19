from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = PROJECT_ROOT / "backend"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.core.chatbot_financial_topics import (  # noqa: E402
    CHATBOT_FINANCIAL_TOPIC_CATALOG,
    get_financial_keywords,
    get_financial_modules,
    get_financial_topic_keys,
)
from app.core.chatbot_scope import is_financial_question  # noqa: E402


def test_financial_topic_catalog_contains_core_project_topics():
    topics = get_financial_topic_keys()

    expected = {
        "var",
        "cvar",
        "capm",
        "markowitz",
        "garch",
        "perri",
        "black_scholes",
        "nelson_siegel",
        "benchmark",
        "macro_financiero",
        "kyc",
        "roboadvisor",
    }

    assert expected.issubset(set(topics))


def test_financial_topic_catalog_has_keywords_and_descriptions():
    for topic_key, payload in CHATBOT_FINANCIAL_TOPIC_CATALOG.items():
        assert topic_key
        assert payload["label"]
        assert payload["description"]
        assert payload["keywords"]


def test_financial_keywords_feed_scope_detector():
    keywords = get_financial_keywords()

    assert "var" in keywords
    assert "capm" in keywords
    assert "perri" in keywords
    assert is_financial_question("Explícame Perri institucional") is True


def test_financial_modules_feed_scope_detector():
    modules = get_financial_modules()

    assert "risk" in modules
    assert "portfolio" in modules
    assert "valuation" in modules
    assert is_financial_question("Explícame esto", module="portfolio") is True
