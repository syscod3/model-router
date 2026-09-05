"""SQLite WAL health state shared by Hermes processes."""
from __future__ import annotations
import sqlite3
from pathlib import Path
from .failures import Failure
from .types import CandidateHealth, HealthState

class HealthStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        with self._connect() as db:
            db.execute("PRAGMA journal_mode=WAL")
            db.execute("CREATE TABLE IF NOT EXISTS candidate_health (key TEXT PRIMARY KEY, state TEXT NOT NULL, failure_type TEXT, cooldown_until REAL)")
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
