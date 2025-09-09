import datetime
import pathlib
import sys

# Ensure repository root is on the path for imports when tests are executed
ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from api.schemas import EventIn  # noqa: E402
from pipeline.normalize import normalize as norm  # noqa: E402


def test_clean_text():
    raw = "<p>Hello   world!</p>"
    assert norm.clean_text(raw) == "Hello world!"


def test_detect_language():
    assert norm.detect_language("hello world") == "en"
    assert norm.detect_language("hola mundo") == "es"


def test_remove_pii():
    raw = "Contact me at test@example.com or 123-456-7890"
    cleaned = norm.remove_pii(raw)
    assert "test@example.com" not in cleaned
    assert "123-456-7890" not in cleaned
    assert "[EMAIL]" in cleaned
    assert "[PHONE]" in cleaned


def test_expand_urls(monkeypatch):
    def fake_urlopen(url):
        class Resp:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                pass

            def geturl(self):
                return "http://example.com/full"

        return Resp()

    monkeypatch.setattr(norm.urllib.request, "urlopen", fake_urlopen)
    text = "Visit http://bit.ly/x"
    assert norm.expand_urls(text) == "Visit http://example.com/full"


def test_normalize_sequence(monkeypatch):
    def fake_urlopen(url):
        class Resp:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                pass

            def geturl(self):
                return "http://example.com/full"

        return Resp()

    monkeypatch.setattr(norm.urllib.request, "urlopen", fake_urlopen)

    event = EventIn(
        event_id="1",
        ts=datetime.datetime.utcnow(),
        src="unit-test",
        content={"text": "<p>Hello test@example.com http://bit.ly/x</p>"},
        feats={},
        observed_ttp=[],
    )

    result = norm.normalize(event)
    assert result.content["text"] == "Hello [EMAIL] http://example.com/full"
    assert result.feats["lang"] == "en"


def test_normalize_unsupported_language():
    event = EventIn(
        event_id="2",
        ts=datetime.datetime.utcnow(),
        src="unit-test",
        content={"text": "hola mundo"},
        feats={},
        observed_ttp=[],
    )
    try:
        norm.normalize(event)
    except ValueError:
        return
    assert False, "Expected ValueError for unsupported language"
