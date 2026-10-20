import re
from typing import List, Dict, Any, Optional, Literal, Annotated, Union
from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict


class _Base(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")


class PriceDTO(_Base):
    amount: int = Field(..., gt=0, description="Smallest currency unit (18500 = KES 185.00)")
    currency: str = Field(default="KES", min_length=3, max_length=3)

    @field_validator("currency")
    @classmethod
    def currency_upper(cls, v: str) -> str:
        v = v.upper()
        if not v.isalpha():
            raise ValueError("Currency must be a 3-letter ISO code, e.g. 'KES'")
        return v


class SizeDTO(_Base):
    value: float = Field(..., gt=0)
    unit: str = Field(default="ml", min_length=1)


class VariantDTO(_Base):
    sku: str = Field(..., min_length=1, max_length=64)
    price: PriceDTO
    shade_name: Optional[str] = None
    size: Optional[SizeDTO] = None
    images: List[str] = Field(default_factory=list)
    is_active: bool = True


class MakeupAttributes(_Base):
    finish: Optional[Literal["matte", "satin", "dewy", "glossy", "natural"]] = None
    coverage: Optional[Literal["sheer", "light", "medium", "full"]] = None
    skin_types: List[str] = Field(default_factory=list)
    claims: list[str] = Field(default_factory=list)

class FragranceAttributes(_Base):
    concentration: Literal["eau-de-parfum", "eau-de-toilette", "body-mist", "parfum"]
    gender_target: Optional[Literal["women", "men", "unisex"]] = None
    scent_family: List[str] = Field(default_factory=list)
    notes: Dict[str, List[str]] = Field(default_factory=dict)
    longevity: Optional[str] = None

class SkincareAttributes(_Base):
    skin_types: List[str] = Field(default_factory=list)
    key_ingredients: List[str] = Field(default_factory=list)
    spf: Optional[float]= None

class HaircareAttributes(_Base):
    hair_types: List[str] = Field(default_factory=list)
    key_ingredients: List[str] = Field(default_factory=list)

class BodycareAttributes(_Base):
    skin_types: List[str]= Field(default_factory=list)
    key_ingredients: List[str] = Field(default_factory=list)
    scent: Optional[str] = None

class NailAttributes(_Base):
    finish: Optional[str] = None
    claims: List[str] = Field(default_factory=list)

class ToolAttributes(_Base):
    material: Optional[str] = None
    reusable: Optional[bool] = None

class ProductBase(_Base):
    slug: str = Field(..., min_length=3, max_length=200)
    name: str = Field(..., min_length=3, max_length=200)
    brand: str = Field(..., min_length=3, max_length=200)
    description: str = Field(..., min_length=10, max_length=5000)
    benefits: List[str] = Field(default_factory=list)
    how_to_use: List[str] = Field(default_factory=list)
    variants: List[VariantDTO] = Field(..., min_length=1)
    images: List[str] = Field(default_factory=list)
    status: Literal["draft"] = "draft"

    @field_validator("slug")
    @classmethod
    def slug_must_be_url_safe(cls, v: str) -> str:
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", v):
            raise ValueError("Slug must be lowercase, alphanumeric, hyphen-separated (e.g. 'my-product')")
        return v

    @model_validator(mode="after")
    def unique_skus(self):
        skus = [v.sku for v in self.variants]
        dupes = {s for s in skus if skus.count(s) > 1}
        if dupes:
            raise ValueError(f"Duplicate SKUs in request: {sorted(dupes)}")
        return self
class CreateMakeupProduct(ProductBase):
    category: Literal["makeup"]
    attributes: MakeupAttributes = Field(default_factory=MakeupAttributes)

class CreateFragranceProduct(ProductBase):
    category: Literal["fragrance"]
    attributes: FragranceAttributes

    @model_validator(mode="after")
    def variants_need_size(self):
        if any(v.size is None for v in self.variants):
            raise  ValueError("Variants must not be empty")
        return self

class CreateSkincareProduct(ProductBase):
    category: Literal["skincare"]
    attributes: SkincareAttributes = Field(default_factory=SkincareAttributes)

class CreateHaircareProduct(ProductBase):
    category: Literal["haircare"]
    attributes: HaircareAttributes = Field(default_factory=HaircareAttributes)

class CreateBodycareProduct(ProductBase):
    category: Literal["bodycare"]
    attributes: BodycareAttributes = Field(default_factory=BodycareAttributes)

class CreateNailsProduct(ProductBase):
    category: Literal["nails"]
    attributes: NailAttributes = Field(default_factory=NailAttributes)

class CreateToolsProduct(ProductBase):
    category: Literal["tools"]
    attributes: ToolAttributes = Field(default_factory=ToolAttributes)



CreateProductRequest = Annotated[
    Union[
        CreateMakeupProduct,
        CreateFragranceProduct,
        CreateSkincareProduct,
        CreateHaircareProduct,
        CreateBodycareProduct,
        CreateNailsProduct,
        CreateToolsProduct,
    ],
    Field(discriminator="category"),
]



