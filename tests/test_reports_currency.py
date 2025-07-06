import os
import sys
import tempfile
import importlib
from pathlib import Path
from datetime import date

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


def test_report_contains_ruble_sign():
    from shared.database import get_connection
    from shared.reports import format_daily_report

    today = date.today().isoformat()
    conn = get_connection()
    conn.execute(
        "INSERT INTO users (telegram_id, username, first_name, date_joined) VALUES (?, ?, ?, ?)",
        (1, 'u', 'U', today),
    )
    conn.execute(
        "INSERT INTO recharge (user_id, amount, source, timestamp) VALUES (?, ?, ?, ?)",
        (1, 100.0, 't', f"{today}T10:00"),
    )
    conn.commit()
    conn.close()

    report = format_daily_report(date.today())
    assert "На сумму: 100.00 ₽" in report
