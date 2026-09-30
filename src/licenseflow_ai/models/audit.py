from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


class AuditEvent(BaseModel):
    workflow_id: str
    event_type: str
    actor: str

    details: dict[str, Any] = Field(
        default_factory=dict
    )

    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )