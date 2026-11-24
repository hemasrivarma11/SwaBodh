import pytest

from swabodh import explain

KEY = "gem-test-key-not-real"
FACTS = ["Average on habit days: 450.0 min.", "Difference: +20.6 min."]


class Resp:
    def __init__(self, status=200, text="Habit days averaged 450.0 min, a difference of +20.6 min.", bad=False):
        self.status_code = status
        self._text = text
        self._bad = bad

    def json(self):
        if self._bad:
            return {"promptFeedback": {}}
        return {"candidates": [{"content": {"parts": [{"text": self._text}]}}]}


@pytest.fixture()
def configured(monkeypatch):
    monkeypatch.setattr(explain, "GEMINI_API_KEY", KEY)
    monkeypatch.setattr(explain, "GEMINI_MODEL", "test-model")


def test_off_uses_template():
    r = explain._explain(FACTS, "fallback", False)
    assert r["source"] == "template" and r["text"] == "fallback"


def test_no_key_uses_template(monkeypatch):
    monkeypatch.setattr(explain, "GEMINI_API_KEY", "")
    r = explain._explain(FACTS, "fallback", True)
    assert r["source"] == "template" and "GEMINI_API_KEY" in r["note"]


def test_success_key_only_in_header(configured, monkeypatch):
    seen = {}

    def fake_post(url, **kw):
        seen["url"], seen["kw"] = url, kw
        return Resp()

    monkeypatch.setattr(explain.requests, "post", fake_post)
    r = explain._explain(FACTS, "fallback", True)
    assert r["source"] == "ai"
    assert KEY not in seen["url"] and "test-model:generateContent" in seen["url"]
    assert seen["kw"]["headers"]["x-goog-api-key"] == KEY
    assert KEY not in str(seen["kw"]["json"])


def test_invented_number_is_rejected(configured, monkeypatch):
    monkeypatch.setattr(explain.requests, "post", lambda *a, **k: Resp(text="Sleep rose by 99.9 min."))
    r = explain._explain(FACTS, "fallback", True)
    assert r["source"] == "template" and "99.9" in r["note"]


@pytest.mark.parametrize("status", [400, 401, 404, 429, 503])
def test_errors_fall_back_without_leaking_key(configured, monkeypatch, status):
    monkeypatch.setattr(explain.requests, "post", lambda *a, **k: Resp(status=status))
    r = explain._explain(FACTS, "fallback", True)
    assert r["source"] == "template" and KEY not in r["note"]


def test_network_error_and_empty_answer(configured, monkeypatch):
    def boom(*a, **k):
        raise explain.requests.ConnectionError(f"failed for {KEY}")

    monkeypatch.setattr(explain.requests, "post", boom)
    r = explain._explain(FACTS, "fallback", True)
    assert r["source"] == "template" and KEY not in r["note"]
    monkeypatch.setattr(explain.requests, "post", lambda *a, **k: Resp(bad=True))
    assert explain._explain(FACTS, "fallback", True)["source"] == "template"
