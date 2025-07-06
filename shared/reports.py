from __future__ import annotations

from datetime import date

from .database import get_connection


def get_daily_stats(report_date: date) -> dict[str, float | int]:
    """Return daily statistics for the given date."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        date_str = report_date.isoformat()
        cursor.execute(
            "SELECT COUNT(*) FROM users WHERE date_joined = ?",
            (date_str,),
        )
        new_users = cursor.fetchone()[0] or 0

        cursor.execute(
            "SELECT COUNT(*), COALESCE(SUM(amount), 0) FROM recharge "
            "WHERE substr(timestamp, 1, 10) = ?",
            (date_str,),
        )
        row = cursor.fetchone()
        payments_count = row[0] or 0
        payments_sum = float(row[1] or 0.0)

        cursor.execute(
            """
            SELECT COALESCE(SUM(amount), 0)
            FROM recharge r
            WHERE substr(r.timestamp, 1, 10)=?
              AND r.user_id IN (
                    SELECT user_id
                    FROM recharge
                    GROUP BY user_id
                    HAVING substr(MIN(timestamp),1,10)=?
              )
            """,
            (date_str, date_str),
        )
        first_payments_sum = float(cursor.fetchone()[0] or 0.0)

        return {
            "new_users": new_users,
            "payments_count": payments_count,
            "payments_sum": payments_sum,
            "first_payments_sum": first_payments_sum,
        }
    finally:
        conn.close()


def format_daily_report(report_date: date) -> str:
    """Return formatted text report for the given date."""
    stats = get_daily_stats(report_date)
    report_lines = [
        f"ОТЧЕТ ЗА {report_date.strftime('%m-%d-%y')}",
        "",
        f"Новых пользователей: {stats['new_users']}",
        f"Совершено платежей: {stats['payments_count']}",
        f"На сумму: {stats['payments_sum']:.2f}",
        f"Из них первый платеж: {stats['first_payments_sum']:.2f}",
    ]
    return "\n".join(report_lines)
