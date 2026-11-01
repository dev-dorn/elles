"""List and get: filters, pagination and who can see unpublished products."""
from datetime import datetime, timedelta, timezone

import pytest

from tests.helpers import auth, make_product, make_token

URL = "/api/v1/products/"


def slugs(response):
    return [item["slug"] for item in response.json()["items"]]


@pytest.fixture
def catalog(repo):
    """Four published products, one draft and one archived, with distinct creation times."""
    now = datetime.now(timezone.utc)
    products = [
        make_product("velvet-matte-lipstick", category="makeup", amounts=(185000,),
                     created_at=now - timedelta(minutes=5)),
        make_product("golden-hour-eau-de-parfum", category="fragrance", amounts=(850000, 1350000),
                     attributes={"scent_family": ["floral", "warm"]},
                     created_at=now - timedelta(minutes=4)),
        make_product("glow-vitamin-c-serum", category="skincare", amounts=(240000,),
                     attributes={"skin_types": ["oily", "combination"]},
                     created_at=now - timedelta(minutes=3)),
        make_product("shea-body-lotion", category="bodycare", amounts=(120000,), brand="Naturals",
                     created_at=now - timedelta(minutes=2)),
        make_product("secret-draft", category="makeup", status="draft",
                     created_at=now - timedelta(minutes=1)),
        make_product("old-archived", category="makeup", status="archived", created_at=now),
    ]
    for product in products:
        repo.add(product)
    return products


class TestList:
    def test_is_public_and_shows_only_published_products_newest_first(self, client, catalog):
        response = client.get(URL)

        assert response.status_code == 200
        assert slugs(response) == [
            "shea-body-lotion",
            "glow-vitamin-c-serum",
            "golden-hour-eau-de-parfum",
            "velvet-matte-lipstick",
        ]
        assert response.json()["total"] == 4

    def test_an_empty_catalog_returns_an_empty_page(self, client):
        body = client.get(URL).json()
        assert body == {"items": [], "total": 0, "page": 1, "page_size": 20, "pages": 0}

    def test_filters_by_category(self, client, catalog):
        assert slugs(client.get(URL, params={"category": "fragrance"})) == ["golden-hour-eau-de-parfum"]

    def test_unknown_category_returns_422(self, client, catalog):
        assert client.get(URL, params={"category": "furniture"}).status_code == 422

    def test_filters_by_brand(self, client, catalog):
        assert slugs(client.get(URL, params={"brand": "Naturals"})) == ["shea-body-lotion"]

    @pytest.mark.parametrize("q", ["serum", "SERUM", "vitamin"])
    def test_searches_names_ignoring_case(self, client, catalog, q):
        assert slugs(client.get(URL, params={"q": q})) == ["glow-vitamin-c-serum"]

    def test_a_one_character_search_returns_422(self, client, catalog):
        assert client.get(URL, params={"q": "a"}).status_code == 422

    def test_filters_by_minimum_price(self, client, catalog):
        assert slugs(client.get(URL, params={"min_price": 500000})) == ["golden-hour-eau-de-parfum"]

    def test_filters_by_maximum_price(self, client, catalog):
        assert slugs(client.get(URL, params={"max_price": 130000})) == ["shea-body-lotion"]

    def test_filters_by_price_range(self, client, catalog):
        response = client.get(URL, params={"min_price": 100000, "max_price": 200000})
        assert slugs(response) == ["shea-body-lotion", "velvet-matte-lipstick"]

    def test_a_reversed_price_range_returns_422(self, client, catalog):
        assert client.get(URL, params={"min_price": 5000, "max_price": 100}).status_code == 422

    def test_filters_by_scent_family(self, client, catalog):
        assert slugs(client.get(URL, params={"scent_family": "floral"})) == ["golden-hour-eau-de-parfum"]

    def test_filters_by_skin_type(self, client, catalog):
        assert slugs(client.get(URL, params={"skin_type": "oily"})) == ["glow-vitamin-c-serum"]

    def test_filters_combine(self, client, catalog):
        assert slugs(client.get(URL, params={"category": "makeup", "brand": "Naturals"})) == []

    def test_paginates(self, client, catalog):
        first = client.get(URL, params={"page": 1, "page_size": 3}).json()
        second = client.get(URL, params={"page": 2, "page_size": 3}).json()

        assert [i["slug"] for i in first["items"]] == [
            "shea-body-lotion", "glow-vitamin-c-serum", "golden-hour-eau-de-parfum",
        ]
        assert [i["slug"] for i in second["items"]] == ["velvet-matte-lipstick"]
        assert first["total"] == second["total"] == 4
        assert first["pages"] == second["pages"] == 2

    def test_a_page_past_the_end_is_empty(self, client, catalog):
        body = client.get(URL, params={"page": 9, "page_size": 3}).json()
        assert body["items"] == []
        assert body["total"] == 4

    @pytest.mark.parametrize("params", [{"page": 0}, {"page_size": 0}, {"page_size": 101}])
    def test_invalid_paging_returns_422(self, client, catalog, params):
        assert client.get(URL, params=params).status_code == 422

    def test_a_card_shows_the_cheapest_price_and_variant_count(self, client, catalog):
        items = {i["slug"]: i for i in client.get(URL).json()["items"]}

        parfum = items["golden-hour-eau-de-parfum"]
        assert parfum["price_from"] == {"amount": 850000, "currency": "KES"}
        assert parfum["variant_count"] == 2

    def test_inactive_variants_do_not_count_toward_the_card(self, client, repo):
        repo.add(make_product("mixed", amounts=(50, 100), active=(False, True)))

        item = client.get(URL).json()["items"][0]

        assert item["price_from"]["amount"] == 100
        assert item["variant_count"] == 1


class TestListVisibility:
    def test_drafts_need_an_admin(self, client, catalog):
        response = client.get(URL, params={"status": "draft"})
        assert response.status_code == 403

    @pytest.mark.parametrize("token", [
        pytest.param(lambda: make_token(role="CUSTOMER"), id="customer"),
        pytest.param(lambda: make_token(expires_in=-60), id="expired"),
        pytest.param(lambda: make_token(secret="a-different-secret-that-is-long-enough-1234"), id="forged"),
        pytest.param(lambda: "not-a-token", id="garbage"),
    ])
    def test_a_non_admin_token_counts_as_public(self, client, catalog, token):
        response = client.get(URL, params={"status": "draft"}, headers=auth(token()))
        assert response.status_code == 403

    def test_an_admin_sees_drafts(self, client, catalog):
        response = client.get(URL, params={"status": "draft"}, headers=auth())
        assert response.status_code == 200
        assert slugs(response) == ["secret-draft"]

    def test_an_admin_sees_archived_products(self, client, catalog):
        response = client.get(URL, params={"status": "archived"}, headers=auth())
        assert slugs(response) == ["old-archived"]

    def test_an_invalid_status_returns_422(self, client, catalog):
        assert client.get(URL, params={"status": "deleted"}, headers=auth()).status_code == 422

    def test_a_bad_token_does_not_block_the_public_list(self, client, catalog):
        response = client.get(URL, headers=auth("not-a-token"))
        assert response.status_code == 200
        assert response.json()["total"] == 4


class TestGet:
    def test_a_published_product_is_public(self, client, catalog):
        response = client.get(f"{URL}golden-hour-eau-de-parfum")

        assert response.status_code == 200
        body = response.json()
        assert body["slug"] == "golden-hour-eau-de-parfum"
        assert body["attributes"] == {"scent_family": ["floral", "warm"]}
        assert [v["price"]["amount"] for v in body["variants"]] == [850000, 1350000]

    def test_the_full_shape_is_returned(self, client, catalog):
        body = client.get(f"{URL}velvet-matte-lipstick").json()

        assert set(body) >= {
            "id", "slug", "name", "brand", "category", "description", "benefits", "how_to_use",
            "attributes", "variants", "images", "status", "created_at", "updated_at",
        }
        assert set(body["variants"][0]) >= {"sku", "shade_name", "size", "price", "images", "is_active"}

    def test_a_draft_is_hidden_from_the_public(self, client, catalog):
        assert client.get(f"{URL}secret-draft").status_code == 404

    def test_a_draft_is_hidden_from_a_customer(self, client, catalog):
        response = client.get(f"{URL}secret-draft", headers=auth(make_token(role="CUSTOMER")))
        assert response.status_code == 404

    def test_an_archived_product_is_hidden_from_the_public(self, client, catalog):
        assert client.get(f"{URL}old-archived").status_code == 404

    def test_an_admin_can_read_a_draft(self, client, catalog):
        response = client.get(f"{URL}secret-draft", headers=auth())
        assert response.status_code == 200
        assert response.json()["status"] == "draft"

    def test_an_unknown_slug_returns_404(self, client, catalog):
        assert client.get(f"{URL}no-such-product").status_code == 404
        assert client.get(f"{URL}no-such-product", headers=auth()).status_code == 404
