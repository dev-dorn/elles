from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Sequence
from uuid import UUID

from inventory_app.domain.exceptions import InvalidAdjustmentError


class MovementReason(str, Enum):
    RECEIVED = "received"
    CORRECTION = "correction"
    DAMAGED = "damaged"
    RETURNED = "returned"
    RESERVED = "reserved"
    RELEASED = "released"
    EXPIRED = "expired"
    SOLD = "SOLD"


MANUAL_REASONS = (
    MovementReason.RECEIVED,
    MovementReason.CORRECTION,
    MovementReason.DAMAGED,
    MovementReason.RETURNED,
)


def validate_adjustment(delta: int, reason: MovementReason) -> None:
    if reason not in MANUAL_REASONS:
        raise InvalidAdjustmentError(f"`{reason.value}` cannot be entered manually.")
    if delta == 0:
        raise InvalidAdjustmentError("An adjustment must change the stock")
    if reason in (MovementReason.RECEIVED, MovementReason.RETURNED) and delta < 0:
        raise InvalidAdjustmentError(f"`{reason.value}` must add stock (a positive delta).")
    if reason is MovementReason.DAMAGED and delta > 0:
        raise InvalidAdjustmentError("'damaged' adjustment cannot be added to the stock( a negative delta).")


class ReservationStatus(str, Enum):
    ACTIVE = "active"
    COMMITTED = "committed"
    RELEASED = "released"
    EXPIRED = "expired"


@dataclass(frozen=True)
class StockItem:
    sku: str
    on_hand: int
    reserved: int
    updated_at: datetime

    @property
    def available(self) -> int:
        return self.on_hand - self.reserved


@dataclass(frozen=True)
class Availability:
    sku: str
    in_stock: bool
    low_stock: bool

    @classmethod
    def from_stock(cls, sku: str, item: Optional[StockItem], low_stock_threshold: int) -> "Availability":
        available = max(item.available, 0) if item else 0
        return cls(sku=sku, in_stock=available > 0, low_stock=0 < available <= low_stock_threshold)



@dataclass(frozen=True)
class ReservationLine:
    sku: str
    quantity: int


@dataclass
class Reservation:
    id: UUID
    order_id: str
    status: ReservationStatus
    lines: List[ReservationLine]
    expires_at: datetime
    created_at: datetime
    updated_at: datetime

    def has_same_lines(self, lines: Sequence[ReservationLine]) -> bool:
        return self._as_map(self.lines) == self._as_map(lines)

    @staticmethod
    def _as_map(lines: Sequence[ReservationLine]) -> Dict[str, int]:
        return {line.sku: line.quantity for line in lines}

@dataclass(frozen=True)
class StockMovement:
    id: UUID
    sku: str
    delta_on_hand: int
    delta_reserved: int
    reason: MovementReason
    created_at: datetime
    reference: Optional[str] = None
    note: Optional[str] = None
    actor: Optional[UUID] = None

