from app.application.ports.repositories import ProductRepositoryPort
from app.application.ports.event_publisher import EventPublisherPort
from app.application.dtos.commands import PublishProductCommand

class PublishProductCase:
    def __init__(
            self,
            product_repo: ProductRepositoryPort,
            event_publisher: EventPublisherPort,
    ):
        self._product_repo = product_repo
        self._event_publisher = event_publisher

    async def execute(self, command: PublishProductCommand) -> None:
        product = await self._product_repo.get_by_id(command.product_id)
        if not product:
            raise ValueError(f"Product with id {command.product_id} not found")

        product.publish(correlation_id = command.correlation_id)

        await self._product_repo.save(product)

        events = product.pull_domain_events()
        for event in events:
            await self._event_publisher.publish(event)

