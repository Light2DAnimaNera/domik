import os
import tempfile
import types
import sys
from pathlib import Path

import importlib

# Prepare temporary DB

temp_db = tempfile.NamedTemporaryFile(delete=False)
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

def setup_module(module):
    import shared.config as config
    config.DB_PATH = temp_db.name
    import shared.database as database
    importlib.reload(database)
    database.init_db()


def teardown_module(module):
    os.unlink(temp_db.name)

class DummyUser:
    def __init__(self, uid):
        self.id = uid


def test_previous_summary_exists(monkeypatch):
    class DummyClient:
        def __init__(self, *args, **kwargs):
            self.chat = types.SimpleNamespace(completions=types.SimpleNamespace(create=lambda *a, **kw: types.SimpleNamespace(choices=[types.SimpleNamespace(message=types.SimpleNamespace(content='ok'))])))

    dummy_openai = types.SimpleNamespace(Client=DummyClient)
    monkeypatch.setitem(sys.modules, 'openai', dummy_openai)
    from shared.database import get_connection
    from shared.session_manager import SessionManager
    import shared.gpt_client as gpt_client

    user = DummyUser(1)
    conn = get_connection()
    conn.execute(
        "INSERT INTO sessions (telegram_id, idx, date_start, date_end, summary, active) "
        "VALUES (?, 1, 's', 'e', 'old summary', 0)",
        (user.id,)
    )
    conn.commit()
    conn.close()

    sid = SessionManager.start(user)
    assert SessionManager.session_summary(sid) == 'old summary'

    captured = {}

    class DummyClient:
        def __init__(self, *args, **kwargs):
            self.chat = types.SimpleNamespace(completions=types.SimpleNamespace(create=self.fake_create))

        def fake_create(self, model, messages, timeout=30, max_tokens=None):
            captured['messages'] = messages
            return types.SimpleNamespace(choices=[types.SimpleNamespace(message=types.SimpleNamespace(content='ok'))])

    monkeypatch.setattr(gpt_client, 'openai', types.SimpleNamespace(Client=DummyClient))

    client = gpt_client.GptClient()
    client.ask('ctx', 'hi', SessionManager.session_summary(sid))

    assert captured['messages'][0]['content'].startswith('### CONTEXT_PREVIOUS_SESSION_START')
    assert captured['messages'][1]['content'].startswith('♀Ω∇')


def test_no_previous_summary(monkeypatch):
    class DummyClient:
        def __init__(self, *args, **kwargs):
            self.chat = types.SimpleNamespace(completions=types.SimpleNamespace(create=lambda *a, **kw: types.SimpleNamespace(choices=[types.SimpleNamespace(message=types.SimpleNamespace(content='ok'))])))

    dummy_openai = types.SimpleNamespace(Client=DummyClient)
    monkeypatch.setitem(sys.modules, 'openai', dummy_openai)
    from shared.session_manager import SessionManager
    import shared.gpt_client as gpt_client

    user = DummyUser(2)
    sid = SessionManager.start(user)
    assert SessionManager.session_summary(sid) == ''

    captured = {}

    class DummyClient:
        def __init__(self, *args, **kwargs):
            self.chat = types.SimpleNamespace(completions=types.SimpleNamespace(create=self.fake_create))

        def fake_create(self, model, messages, timeout=30, max_tokens=None):
            captured['messages'] = messages
            return types.SimpleNamespace(choices=[types.SimpleNamespace(message=types.SimpleNamespace(content='ok'))])

    monkeypatch.setattr(gpt_client, 'openai', types.SimpleNamespace(Client=DummyClient))

    client = gpt_client.GptClient()
    client.ask('ctx', 'hi', SessionManager.session_summary(sid))

    assert not captured['messages'][0]['content'].startswith('### CONTEXT_PREVIOUS_SESSION_START')
    assert captured['messages'][0]['content'].startswith('♀Ω∇')
