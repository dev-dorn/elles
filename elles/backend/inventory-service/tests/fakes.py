from typing import Dict, Optional, Sequence

from inventory_app.domain.models.models import StockItem


class InMemoryStockRepository:
    """Small repository fake implementing the stock read contract."""

    def __init__(self) -> None:
        self.items: Dict[str, StockItem] = {}

    async def get_stock(self, sku: str) -> Optional[StockItem]:
        return self.items.get(sku)

    async def get_stock_many(self, skus: Sequence[str]) -> Dict[str, StockItem]:
        return {sku: self.items[sku] for sku in dict.fromkeys(skus) if sku in self.items}

    async def save(self, item: StockItem) -> None:
        self.items[item.sku] = item
