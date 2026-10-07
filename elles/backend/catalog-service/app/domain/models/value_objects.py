from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from typing import List, Optional

class ProductCategory(str, Enum):
    PERFUME = "PERFUME"
    SKINCARE = "SKINCARE"
    MAKEUP = "MAKEUP"
    HAIRCARE = "HAIRCARE"
    BODY = "BODY"

class Concentration(str, Enum):
    PARFUM = "PARFUM"
    EAU_DE_PARFUM = "EAU_DE_PARFUM"
    EAU_DE_TOILETTE = "EAU_DE_TOILETTE"
    # Note: Skincare/Makeup won't use this, and that's okay. It's optional.

class SkinType(str, Enum):
    DRY = "DRY"
    OILY = "OILY"
    COMBINATION = "COMBINATION"
    SENSITIVE = "SENSITIVE"
    ALL = "ALL"

@dataclass(frozen=True)
class Price:
    amount: Decimal
    currency: str = "USD"

    def __post_init__(self):
        if self.amount < 0:
            raise ValueError("Price amount cannot be negative.")
        if not self.currency.isalpha() or len(self.currency) != 3:
            raise ValueError("Currency must be a 3-letter ISO code (e.g., USD).")

@dataclass(frozen=True)
class ScentProfile:
    """Specific to Perfumes and Body Mists"""
    top_notes: List[str]
    heart_notes: List[str]
    base_notes: List[str]
    family: str # e.g., "FLORAL", "WOODY"

    def __post_init__(self):
        if not self.top_notes or not self.heart_notes or not self.base_notes:
            raise ValueError("A valid scent profile must contain at least one note in top, heart, and base.")

@dataclass(frozen=True)
class SkincareProfile:
    """Specific to Skincare products"""
    volume_ml: int
    target_skin_types: List[SkinType]
    key_ingredients: List[str]

    def __post_init__(self):
        if self.volume_ml <= 0:
            raise ValueError("Volume must be greater than 0.")
        if not self.key_ingredients:
            raise ValueError("Skincare products must list at least one key ingredient.")