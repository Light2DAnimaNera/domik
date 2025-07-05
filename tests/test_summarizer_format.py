import os
import sys
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


def test_make_summary_adds_timestamps(monkeypatch):
    import database
    import summarizer

    monkeypatch.setattr(summarizer, "client", types.SimpleNamespace(make_summary=lambda ft: "ok"))

    conn = database.get_connection()
    conn.execute(
        "INSERT INTO sessions (telegram_id, idx, date_start, date_end, summary, active) VALUES (1, 1, '', '', '', 1)"
    )
    sid = conn.execute("SELECT id FROM sessions").fetchone()[0]
    conn.execute(
        "INSERT INTO messages (session_id, role, content, created) VALUES (?, ?, ?, ?)",
        (sid, "user", "hi", "01-02-24 03-04"),
    )
    conn.execute(
        "INSERT INTO messages (session_id, role, content, created) VALUES (?, ?, ?, ?)",
        (sid, "assistant", "hello", "01-02-24 03-05"),
    )
    conn.commit()
    conn.close()

    summary, full = summarizer.make_summary(sid)
    assert summary == "ok"
    assert full == "[01-02-24 03-04] user: hi\n[01-02-24 03-05] assistant: hello"
