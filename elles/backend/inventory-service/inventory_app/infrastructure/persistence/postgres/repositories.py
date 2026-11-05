from unittest import result

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from inventory_app.domain.models.entities import StockItem, StockMovement
from inventory_app.infrastructure.persistence.postgres.models import StockItemModel, StockMovementModel


class PostgresStockRepository:
    def __init__(self, session: AsyncSession):
        self.session = session
    async def get_by_sku(self, sku: str) -> StockItem | None:
        """Retrieves a stock item by its SKU"""
        result = await self.session.execute(
            select(StockItemModel).where(StockItemModel.sku == sku)

        )
        model = result.scalar_one_or_none()
        if not model:
            return None
        return StockItem(
            sku= model.sku,
            on_hand=model.on_hand,
            reserved=model.reserved,
            updated_at=model.updated_at,
        )
    async def save(self, stock_item: StockItem) -> None:
        result = await self.session.execute(
            select(StockItemModel).where(StockItemModel.sku == stock_item.sku)

        )
        model = result.scalar_one_or_none()

        if model:
            model.on_hand = stock_item.on_hand
            model.reserved = stock_item.reserved
            model.updated_at = stock_item.updated_at

        else:
            model = StockItemModel(
                sku=stock_item.sku,
                on_hand=stock_item.on_hand,
                reserved=stock_item.reserved,
                updated_at=stock_item.updated_at,
            )
            self.session.add(model)
        await self.session.flush()

    async def atomic_reserve(self, sku:str, quantity:int) -> bool:

        stmt = (
            update(StockItemModel)
            .where(
                StockItemModel.sku == sku,
                (StockItemModel.on_hand - StockItemModel.reserved) >= quantity,

            )
            .values(reserved=StockItemModel.reserved + quantity)
        )
        result = await self.session.execute(stmt)
        await self.session.flush()

        return result.rowcount > 0
    async def record_movement(self, movement: StockMovement) -> None:
        model = StockMovementModel(
            sku=movement.sku,
            delta_on_hand=movement.delta_on_hand,
            delta_reserved=movement.delta_reserved,
            reason=movement.reason,

        )
        self.session.add(model)
        await self.session.flush()


