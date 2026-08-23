"""P6 issue-list and actual-usage API contracts."""
from typing import Literal

from pydantic import BaseModel, Field


class ConsumableActualEventCreate(BaseModel):
    event_type: Literal["issue", "return", "consume"]
    quantity: float = Field(gt=0)
    unit: str = Field(min_length=1, max_length=20)
    client_idempotency_key: str = Field(min_length=8, max_length=200)
    batch_number: str | None = Field(None, max_length=100)
    notes: str | None = Field(None, max_length=2000)
    quota_operation_id: str | None = Field(None, max_length=36)
