"""The functions that translate between domain objects and MongoDB documents.

The in-memory fake used elsewhere skips these, so they get their own round-trip tests.
"""
from datetime import datetime, timezone

from catalog_app.domain.models.product import Price, Product, Size, Variant
from catalog_app.infrastructure.persistence.mongodb.product_repository import _to_document, _to_domain
from tests.helpers import ADMIN_ID, make_product


def full_product() -> Product:
    product = make_product(
        "golden-hour",
        category="fragrance",
        status="published",
        amounts=(850000, 1350000),
        attributes={"concentration": "eau-de-parfum", "scent_family": ["floral"]},
    )
    product.benefits = ["Long-lasting"]
    product.how_to_use = ["Spray on pulse points."]
    product.images = ["https://cdn.example/hero.jpg"]
    product.variants[0].size = Size(value=50, unit="ml")
    product.variants[0].shade_name = "Amber"
    product.variants[0].images = ["https://cdn.example/50.jpg"]
    product.updated_at = datetime(2026, 10, 29, 9, 0, tzinfo=timezone.utc)
    return product


def test_a_product_survives_a_round_trip():
    original = full_product()

    assert _to_domain(_to_document(original)) == original


def test_the_document_id_is_stored_as_a_string_under_underscore_id():
    product = full_product()
    document = _to_document(product)

    assert document["_id"] == str(product.id)
    assert "id" not in document
    assert document["created_by"] == str(ADMIN_ID)


def test_prices_are_stored_as_integers():
    document = _to_document(full_product())

    assert document["variants"][0]["price"] == {"amount": 850000, "currency": "KES"}
    assert isinstance(document["variants"][0]["price"]["amount"], int)


def test_a_variant_without_a_size_stores_none_and_loads_back_without_one():
    product = make_product("tool", category="tools")

    document = _to_document(product)
    assert document["variants"][0]["size"] is None

    assert _to_domain(document).variants[0].size is None


def test_an_inactive_variant_stays_inactive():
    product = make_product("mixed", amounts=(100, 200), active=(False, True))

    loaded = _to_domain(_to_document(product))

    assert [v.is_active for v in loaded.variants] == [False, True]


def test_a_variant_with_no_images_is_still_active():
    document = _to_document(make_product("plain"))
    document["variants"][0]["images"] = []

    assert _to_domain(document).variants[0].is_active is True


def test_a_variant_missing_is_active_defaults_to_active():
    document = _to_document(make_product("legacy"))
    del document["variants"][0]["is_active"]

    assert _to_domain(document).variants[0].is_active is True


def test_older_documents_with_float_prices_load_as_integers():
    document = _to_document(make_product("legacy", amounts=(18500,)))
    document["variants"][0]["price"]["amount"] = 18500.0

    amount = _to_domain(document).variants[0].price.amount

    assert amount == 18500
    assert isinstance(amount, int)


def test_optional_fields_may_be_missing_from_a_document():
    document = _to_document(make_product("sparse"))
    for key in ("benefits", "how_to_use", "attributes", "images", "updated_at"):
        del document[key]

    loaded = _to_domain(document)

    assert loaded.benefits == [] and loaded.how_to_use == []
    assert loaded.attributes == {} and loaded.images == []
    assert loaded.updated_at is None


def test_variant_order_is_preserved():
    product = make_product("ordered", amounts=(300, 100, 200))

    loaded = _to_domain(_to_document(product))

    assert [v.price.amount for v in loaded.variants] == [300, 100, 200]
