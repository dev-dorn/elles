import pytest

from catalog_app.domain.exceptions import DomainException, InvalidPriceError
from catalog_app.domain.models.product import Price, Product, Variant
from tests.helpers import ADMIN_ID, make_product


class TestPrice:
    @pytest.mark.parametrize("amount", [0, -1, -18500])
    def test_must_be_greater_than_zero(self, amount):
        with pytest.raises(InvalidPriceError):
            Price(amount=amount)

    def test_defaults_to_kes(self):
        assert Price(amount=100).currency == "KES"


class TestPublish:
    def test_moves_a_draft_to_published(self):
        product = make_product("golden-hour", status="draft")
        product.publish()
        assert product.status == "published"
        assert product.updated_at is not None

    def test_needs_a_name_and_a_slug(self):
        product = Product(created_by=ADMIN_ID, variants=[Variant(sku="S1", price=Price(100))])
        with pytest.raises(DomainException):
            product.publish()
        assert product.status == "draft"

    def test_needs_an_active_variant(self):
        product = make_product("golden-hour", status="draft", amounts=(100, 200), active=(False, False))
        with pytest.raises(DomainException, match="active variant"):
            product.publish()
        assert product.status == "draft"

    def test_needs_at_least_one_variant(self):
        product = make_product("golden-hour", status="draft", amounts=())
        with pytest.raises(DomainException):
            product.publish()

    def test_one_active_variant_is_enough(self):
        product = make_product("golden-hour", status="draft", amounts=(100, 200), active=(False, True))
        product.publish()
        assert product.status == "published"


class TestArchive:
    def test_moves_to_archived(self):
        product = make_product("golden-hour", status="published")
        product.archive()
        assert product.status == "archived"
        assert product.updated_at is not None

    def test_an_archived_product_can_be_published_again(self):
        product = make_product("golden-hour", status="archived")
        product.publish()
        assert product.status == "published"


class TestVariants:
    def test_add_variant_appends_and_touches_updated_at(self):
        product = make_product("golden-hour", amounts=(100,))
        product.add_variant(Variant(sku="NEW-SKU", price=Price(500)))
        assert [v.sku for v in product.variants][-1] == "NEW-SKU"
        assert product.updated_at is not None

    def test_duplicate_sku_is_rejected(self):
        product = make_product("golden-hour", amounts=(100,))
        existing = product.variants[0].sku
        with pytest.raises(DomainException, match="Duplicate SKU"):
            product.add_variant(Variant(sku=existing, price=Price(500)))
        assert len(product.variants) == 1


def test_created_by_is_required():
    with pytest.raises(TypeError):
        Product()  # type: ignore[call-arg]
