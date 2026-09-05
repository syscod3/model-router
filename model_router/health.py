"""SQLite WAL health state shared by Hermes processes."""
from __future__ import annotations
import sqlite3
from pathlib import Path
from .failures import Failure
from .types import CandidateHealth, HealthState

class HealthStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as db:
            db.execute("PRAGMA journal_mode=WAL")
            db.execute("CREATE TABLE IF NOT EXISTS candidate_health (key TEXT PRIMARY KEY, state TEXT NOT NULL, failure_type TEXT, cooldown_until REAL)")
            db.execute("CREATE TABLE IF NOT EXISTS payg_budget (day TEXT PRIMARY KEY, spent_usd REAL NOT NULL)")
    def _connect(self):
        return sqlite3.connect(self.path)
    def record_failure(self, key: str, failure: Failure, *, now: float) -> None:
        until = now + failure.cooldown_seconds
        with self._connect() as db:
            db.execute("INSERT INTO candidate_health VALUES (?, ?, ?, ?) ON CONFLICT(key) DO UPDATE SET state=excluded.state, failure_type=excluded.failure_type, cooldown_until=excluded.cooldown_until", (key, HealthState.COOLING_DOWN.value, failure.type.value, until))
    def get(self, key: str, *, now: float) -> CandidateHealth:
        with self._connect() as db:
            row = db.execute("SELECT state, failure_type, cooldown_until FROM candidate_health WHERE key = ?", (key,)).fetchone()
        if not row or row[2] <= now:
            return CandidateHealth()
        return CandidateHealth(state=HealthState(row[0]), failure_type=row[1], cooldown_until=row[2])

    def remaining_budget_usd(self, day: str, *, daily_limit_usd: float) -> float:
        with self._connect() as db:
            row = db.execute("SELECT spent_usd FROM payg_budget WHERE day = ?", (day,)).fetchone()
        return max(0.0, daily_limit_usd - (float(row[0]) if row else 0.0))

    def reserve_budget_usd(self, day: str, *, daily_limit_usd: float, amount_usd: float) -> bool:
        """Atomically reserve a fixed estimated cost without exceeding the daily cap."""
        if amount_usd < 0 or daily_limit_usd < 0:
            return False
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT spent_usd FROM payg_budget WHERE day = ?", (day,)).fetchone()
            spent = float(row[0]) if row else 0.0
            if spent + amount_usd > daily_limit_usd:
                return False
            db.execute(
                "INSERT INTO payg_budget(day, spent_usd) VALUES (?, ?) "
                "ON CONFLICT(day) DO UPDATE SET spent_usd = excluded.spent_usd",
                (day, spent + amount_usd),
            )
        return True
