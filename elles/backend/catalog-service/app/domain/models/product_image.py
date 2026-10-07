from dataclasses import dataclass, field
from uuid import UUID , uuid4

@dataclass
class ProductImage:
    id: UUID = field(default_factory=uuid4)
    image_url: str = "" 
    alt_text: str = ""
    is_primary: bool = False

    def mark_as_primary(self):
        self.is_primary = True

    def update_url(self, new_url: str):
        if not new_url.startswith("http"):
            raise ValueError("Image URL must be a valid HTTP address.")
        self.image_url = new_url