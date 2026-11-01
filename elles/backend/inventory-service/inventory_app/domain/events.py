from dataclasses import dataclass
from datetime import datetime
from uuid import UUID, uuid4

@dataclass(frozen=True)
class DomainEvent:
    event_id: UUID
    occurred_on: datetime
    aggregate_id: UUID
    correlation_id: str

    @classmethod
    def create(cls, aggregate_id: UUID, correlation_id: str, **kwargs):
        return cls(
            event_id=uuid4(),
            occurred_on=datetime.utcnow(),
            aggregate_id=aggregate_id,
            correlation_id=correlation_id,
            **kwargs
        )
