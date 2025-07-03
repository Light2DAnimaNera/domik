import os
import sys
import time
import tempfile
from pathlib import Path
import types
import importlib

# Setup temporary DB

temp_db = tempfile.NamedTemporaryFile(delete=False)
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def setup_module(module):
    import config
    config.DB_PATH = temp_db.name
    import database
    importlib.reload(database)
    database.init_db()


def teardown_module(module):
    os.unlink(temp_db.name)


class DummyUser:
    def __init__(self, uid):
        self.id = uid


class DummyBot:
    def __init__(self):
        self.sent = []

    def send_message(self, chat_id, text):
        self.sent.append((chat_id, text))


def test_session_expires(monkeypatch):
    class DummyClient:
        def __init__(self, *args, **kwargs):
            self.chat = types.SimpleNamespace(completions=types.SimpleNamespace(create=lambda *a, **kw: types.SimpleNamespace(choices=[types.SimpleNamespace(message=types.SimpleNamespace(content='ok'))])))

    dummy_openai = types.SimpleNamespace(Client=DummyClient)
    monkeypatch.setitem(sys.modules, 'openai', dummy_openai)
    from session_manager import SessionManager
    import summarizer

    monkeypatch.setattr(summarizer, 'make_summary', lambda sid: ('', ''))

    user = DummyUser(42)
    sid = SessionManager.start(user)
    assert sid

    # Move last activity into the past
    SessionManager._activity[user.id] = time.time() - 601

    bot = DummyBot()
    SessionManager.expire_idle(bot, 600)

    assert not SessionManager.active(user.id)
    assert bot.sent

