import re

from catalog_app.application.ports.repositories import ProductFilters
from catalog_app.infrastructure.persistence.mongodb.product_repository import _build_query


def test_defaults_to_published_only():
    assert _build_query(ProductFilters()) == {"status": "published"}


def test_no_status_filter_when_status_is_none():
    assert _build_query(ProductFilters(status=None)) == {}


def test_simple_equality_filters():
    query = _build_query(ProductFilters(category="fragrance", brand="Elles", status="draft"))
    assert query == {"category": "fragrance", "brand": "Elles", "status": "draft"}


def test_price_bounds_share_one_condition():
    query = _build_query(ProductFilters(min_price=1000, max_price=5000))
    assert query["variants.price.amount"] == {"$gte": 1000, "$lte": 5000}


def test_zero_is_a_valid_price_bound():
    assert _build_query(ProductFilters(min_price=0))["variants.price.amount"] == {"$gte": 0}


def test_attribute_filters_use_the_attributes_paths():
    query = _build_query(ProductFilters(scent_family="floral", skin_type="oily"))
    assert query["attributes.scent_family"] == "floral"
    assert query["attributes.skin_types"] == "oily"


def test_name_search_is_case_insensitive():
    assert _build_query(ProductFilters(q="serum"))["name"]["$options"] == "i"


def test_name_search_escapes_regex_characters():
    query = _build_query(ProductFilters(q="a.b(c)"))
    assert query["name"]["$regex"] == re.escape("a.b(c)")
