from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Optional, Sequence, Tuple
from uuid import UUID

from inventory_app.domain.models.models import StockItem, StockMovement, MovementReason, ReservationLine, Reservation


class InventoryRepositoryPort(ABC):
    """Every method that changes stock is atomic: it either applies fully or not at all."""

    @abstractmethod
    async def get_stock(self, sku: str) -> Optional[StockItem]: ...

    @abstractmethod
    async def get_stock_many(self, skus: Sequence[str]) -> Dict[str, StockItem]: ...

    @abstractmethod
    async def list_stock(
        self, low_stock_at: Optional[int], page: int, page_size: int
    ) -> Tuple[List[StockItem], int]:
        """Stock ordered by SKU. low_stock_at keeps items whose available quantity is at or below it."""

    @abstractmethod
    async def list_movements(self, sku: str, limit: int) -> List[StockMovement]:
        """Newest first."""

    @abstractmethod
    async def adjust(
        self,
        sku: str,
        delta: int,
        reason: MovementReason,
        note: Optional[str],
        actor: Optional[UUID],
    ) -> StockItem:
        """Add or remove stock on hand, creating the record for a new SKU.

        Raises StockItemNotFoundError when removing stock from an unknown SKU, and
        CannotReduceBelowReservedError when the result would be below what is reserved.
        """

    @abstractmethod
    async def reserve(
        self, order_id: str, lines: Sequence[ReservationLine], expires_at: datetime
    ) -> Tuple[Reservation, bool]:
        """Hold stock for an order. Returns (reservation, created).

        Idempotent per order_id: repeating the same request returns the existing
        reservation with created=False. Raises InsufficientStockError (nothing is
        held) or ReservationConflictError (different items, or no longer active).
        """

    @abstractmethod
    async def get_reservation(self, order_id: str) -> Optional[Reservation]: ...

    @abstractmethod
    async def commit_reservation(self, order_id: str) -> Reservation:
        """The order is paid: reserved stock leaves the warehouse. Idempotent."""

    @abstractmethod
    async def release_reservation(self, order_id: str) -> Reservation:
        """The order is cancelled: reserved stock becomes available again. Idempotent."""

    @abstractmethod
    async def expire_due(self, now: datetime, limit: int) -> List[Reservation]:
        """Release active reservations whose expiry has passed. Returns those released."""