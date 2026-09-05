"""Provider failure classification without provider-specific routing."""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum

class FailureType(str, Enum):
    RATE_LIMIT = "RATE_LIMIT"
    QUOTA_EXHAUSTED = "QUOTA_EXHAUSTED"
    OVERLOADED = "OVERLOADED"
    TIMEOUT = "TIMEOUT"
    CONNECTION = "CONNECTION"
    AUTH = "AUTH"
    CONFIGURATION = "CONFIGURATION"
    UNKNOWN = "UNKNOWN"

@dataclass(frozen=True)
class Failure:
    type: FailureType
    cooldown_seconds: int

def classify_failure(*, status_code: int | None, retry_after_seconds: int | None = None) -> Failure:
    if status_code == 429:
        return Failure(FailureType.RATE_LIMIT, retry_after_seconds or 60)
    if status_code == 503:
        return Failure(FailureType.OVERLOADED, 60)
    if status_code in {401, 403}:
        return Failure(FailureType.AUTH, 24 * 60 * 60)
    if status_code == 400:
        return Failure(FailureType.CONFIGURATION, 24 * 60 * 60)
    return Failure(FailureType.UNKNOWN, 30)
