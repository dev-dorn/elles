from abc import ABC, abstractmethod
from typing import Dict, Iterable, Sequence

from inventory_app.domain.models.models import Availability


class AvailabilityCachePort(ABC):
    """A cache for public availability. It must never decide whether a reservation succeeds,
    and it must never raise: a broken cache has to behave like an empty one."""

    @abstractmethod
    async def get_many(self, skus: Sequence[str]) -> Dict[str, Availability]: ...

    @abstractmethod
    async def set_many(self, items: Iterable[Availability]) -> None: ...

    @abstractmethod
    async def invalidate(self, skus: Iterable[str]) -> None: ...