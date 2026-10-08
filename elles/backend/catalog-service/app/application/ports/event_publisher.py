from typing import Protocol
from app.domain.events import DomainEvent

class EventPublisherPort(Protocol):
    """
    Port defining how Domain events are broadcasted to the message broker.
    The implementation (RabbitMq )
    """
    async def publish(self, event: DomainEvent) -> None: ...