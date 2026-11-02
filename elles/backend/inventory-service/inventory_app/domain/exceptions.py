from dataclasses import dataclass
from typing import List

class InventoryError(Exception):
    """Base class for exceptions in this module."""

class StockItemNotFoundError(InventoryError):
    """Exception raised for items not found in the database."""
class ReservationNotFoundError(InventoryError):
    """Exception raised for items not found in the database."""
class ReservationConflictError(InventoryError):
    """Exception raised for items conflicting with the database."""
class CannotReduceBelowReservedError(InventoryError):
    """Exception raised for items not found in the database."""
class InvalidAdjustmentError(InventoryError):
    """Exception raised for items not found in the database."""

@dataclass(frozen=True)
class Shortage:
    sku: str
    requested: int
    available: int

class InsufficientStockError(InventoryError):
    def __init__(self, shortages: List[Shortage]):
        self.shortages = shortages
        detail = ", ".join(f"{s.sku} (requested {s.requested}, available {s.available})" for s in shortages)
        super().__init__(f"Insufficient stock for {detail}")

