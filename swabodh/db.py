"""Local SQLite storage. The database is a single file on your own computer."""
import sqlite3
from contextlib import contextmanager

import pandas as pd

from .config import DATA_DIR, DB_PATH


@contextmanager
def connect():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS measurements (
                date TEXT NOT NULL,
                source TEXT NOT NULL,
                metric TEXT NOT NULL,
                value REAL NOT NULL,
                PRIMARY KEY (date, source, metric)
            );
            CREATE TABLE IF NOT EXISTS experiments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                metric TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS experiment_days (
                experiment_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                condition TEXT NOT NULL,
                PRIMARY KEY (experiment_id, date)
            );
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
            """
        )


def save_measurements(df: pd.DataFrame) -> int:
    rows = [
        (str(r.date), str(r.source), str(r.metric), float(r.value))
        for r in df[["date", "source", "metric", "value"]].itertuples(index=False)
    ]
    with connect() as conn:
        conn.executemany("INSERT OR REPLACE INTO measurements VALUES (?, ?, ?, ?)", rows)
    return len(rows)


def load_measurements() -> pd.DataFrame:
    with connect() as conn:
        df = pd.read_sql_query(
            "SELECT date, source, metric, value FROM measurements ORDER BY date", conn
        )
    df["date"] = pd.to_datetime(df["date"])
    return df


def create_experiment(name: str, metric: str, schedule) -> int:
    """schedule = list of (date, 'treatment' or 'control')."""
    with connect() as conn:
        cur = conn.execute("INSERT INTO experiments (name, metric) VALUES (?, ?)", (name, metric))
        exp_id = cur.lastrowid
        conn.executemany(
            "INSERT OR REPLACE INTO experiment_days VALUES (?, ?, ?)",
            [(exp_id, str(d), cond) for d, cond in schedule],
        )
    return exp_id


def list_experiments() -> pd.DataFrame:
    with connect() as conn:
        return pd.read_sql_query(
            """SELECT e.id, e.name, e.metric, e.created_at,
                      (SELECT COUNT(*) FROM experiment_days d WHERE d.experiment_id = e.id) AS n_days
               FROM experiments e ORDER BY e.id DESC""",
            conn,
        )


def get_experiment_days(exp_id: int) -> pd.DataFrame:
    with connect() as conn:
        return pd.read_sql_query(
            "SELECT date, condition FROM experiment_days WHERE experiment_id = ? ORDER BY date",
            conn,
            params=(int(exp_id),),
        )


def get_setting(key: str, default: str = "") -> str:
    with connect() as conn:
        row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
    return row[0] if row else default


def set_setting(key: str, value: str) -> None:
    with connect() as conn:
        conn.execute("INSERT OR REPLACE INTO settings VALUES (?, ?)", (key, value))


def table_counts() -> dict:
    with connect() as conn:
        return {
            "measurements": conn.execute("SELECT COUNT(*) FROM measurements").fetchone()[0],
            "experiments": conn.execute("SELECT COUNT(*) FROM experiments").fetchone()[0],
            "experiment_days": conn.execute("SELECT COUNT(*) FROM experiment_days").fetchone()[0],
        }


def delete_all_data(keep_settings: bool = False) -> None:
    with connect() as conn:
        conn.execute("DELETE FROM measurements")
        conn.execute("DELETE FROM experiments")
        conn.execute("DELETE FROM experiment_days")
        if not keep_settings:
            conn.execute("DELETE FROM settings")
