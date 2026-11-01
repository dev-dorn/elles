"""Create, publish and archive: authentication, authorization and behaviour."""
import time
from uuid import UUID, uuid4

import jwt
import pytest

from catalog_app.infrastructure.config import settings
from tests.helpers import ADMIN_ID, auth, fragrance_payload, make_product, make_token, makeup_payload

URL = "/api/v1/products/"

PROTECTED = [
    pytest.param("post", URL, makeup_payload(), id="create"),
    pytest.param("post", f"{URL}some-slug/publish", None, id="publish"),
    pytest.param("post", f"{URL}some-slug/archive", None, id="archive"),
]

BAD_TOKENS = [
    pytest.param(lambda: make_token(secret="a-different-secret-that-is-long-enough-1234"), 401, "Invalid token", id="wrong-secret"),
    pytest.param(lambda: make_token(expires_in=-60), 401, "Token has expired", id="expired"),
    pytest.param(lambda: make_token(include_exp=False), 401, "Invalid token", id="no-expiry"),
    pytest.param(lambda: make_token(sub="not-a-uuid"), 401, "Invalid token subject", id="subject-not-a-uuid"),
    pytest.param(lambda: make_token(role="CUSTOMER"), 403, "Admin access required", id="customer-role"),
    pytest.param(lambda: make_token(role=None), 403, "Admin access required", id="no-role"),
]


class TestAuthentication:
    @pytest.mark.parametrize("method,url,body", PROTECTED)
    def test_a_token_is_required(self, client, method, url, body):
        response = getattr(client, method)(url, json=body)
        assert response.status_code == 401
        assert response.json() == {"detail": "Not authenticated"}

    @pytest.mark.parametrize("method,url,body", PROTECTED)
    @pytest.mark.parametrize("make,status,detail", BAD_TOKENS)
    def test_bad_tokens_are_refused(self, client, method, url, body, make, status, detail):
        response = getattr(client, method)(url, json=body, headers=auth(make()))
        assert response.status_code == status
        assert response.json()["detail"] == detail

    def test_unsigned_tokens_are_refused(self, client):
        payload = {"sub": str(ADMIN_ID), "role": "admin", "exp": int(time.time()) + 3600}
        unsigned = jwt.encode(payload, None, algorithm="none")
        response = client.post(URL, json=makeup_payload(), headers=auth(unsigned))
        assert response.status_code == 401

    def test_the_role_is_matched_case_insensitively(self, client):
        for role in ("admin", "ADMIN", "Admin"):
            response = client.post(
                URL, json=makeup_payload(slug=f"slug-{role.lower()}-{uuid4().hex[:6]}",
                                          variants=[{"sku": uuid4().hex, "price": {"amount": 100}}]),
                headers=auth(make_token(role=role)),
            )
            assert response.status_code == 201

    def test_the_secret_comes_from_settings(self):
        assert len(settings.JWT_SECRET_KEY) >= 32


class TestCreate:
    def test_creates_a_draft(self, client, repo):
        response = client.post(URL, json=makeup_payload(), headers=auth())

        assert response.status_code == 201
        body = response.json()
        assert body["status"] == "draft"
        assert body["name"] == "Velvet Matte Lipstick"
        assert UUID(body["product_id"]) in repo.items

    def test_the_creator_is_the_token_subject(self, client, repo):
        other_admin = uuid4()
        response = client.post(
            URL, json=makeup_payload(), headers=auth(make_token(sub=str(other_admin)))
        )

        saved = repo.items[UUID(response.json()["product_id"])]
        assert saved.created_by == other_admin

    def test_an_admin_id_header_is_ignored(self, client, repo):
        spoofed = uuid4()
        response = client.post(
            URL, json=makeup_payload(), headers={**auth(), "X-Admin-Id": str(spoofed)}
        )

        saved = repo.items[UUID(response.json()["product_id"])]
        assert saved.created_by == ADMIN_ID

    def test_a_fragrance_keeps_its_sizes(self, client, repo):
        response = client.post(URL, json=fragrance_payload(), headers=auth())

        assert response.status_code == 201
        saved = repo.items[UUID(response.json()["product_id"])]
        assert [v.size.value for v in saved.variants] == [50, 100]

    def test_duplicate_slug_returns_409(self, client):
        assert client.post(URL, json=makeup_payload(), headers=auth()).status_code == 201

        response = client.post(URL, json=makeup_payload(), headers=auth())

        assert response.status_code == 409
        assert "already exists" in response.json()["detail"]

    def test_duplicate_sku_on_another_product_returns_409(self, client, repo):
        client.post(URL, json=makeup_payload(), headers=auth())

        response = client.post(URL, json=makeup_payload(slug="another-lipstick"), headers=auth())

        assert response.status_code == 409
        assert "SKU" in response.json()["detail"]
        assert len(repo.items) == 1

    INVALID = {
        "missing-concentration": fragrance_payload(attributes={"scent_family": ["floral"]}),
        "unknown-category": makeup_payload(category="furniture"),
        "unknown-field": makeup_payload(how_too_use=["typo"]),
        "published-on-create": makeup_payload(status="published"),
        "zero-price": makeup_payload(variants=[{"sku": "S1", "price": {"amount": 0}}]),
        "duplicate-skus": makeup_payload(
            variants=[{"sku": "S1", "price": {"amount": 1}}, {"sku": "S1", "price": {"amount": 2}}]
        ),
        "bad-slug": makeup_payload(slug="Not A Slug"),
        "client-sets-creator": makeup_payload(created_by=str(uuid4())),
    }

    @pytest.mark.parametrize("payload", INVALID.values(), ids=INVALID.keys())
    def test_invalid_payloads_return_422_and_save_nothing(self, client, repo, payload):
        response = client.post(URL, json=payload, headers=auth())

        assert response.status_code == 422
        assert repo.items == {}


class TestPublish:
    def test_moves_a_draft_to_published(self, client, repo):
        product = make_product("golden-hour", status="draft")
        repo.add(product)

        response = client.post(f"{URL}golden-hour/publish", headers=auth())

        assert response.status_code == 200
        assert response.json()["status"] == "published"
        assert repo.items[product.id].status == "published"

    def test_the_response_includes_the_variants(self, client, repo):
        repo.add(make_product("golden-hour", status="draft", amounts=(850000, 1350000)))

        body = client.post(f"{URL}golden-hour/publish", headers=auth()).json()

        assert [v["price"]["amount"] for v in body["variants"]] == [850000, 1350000]
        assert body["variants"][0]["price"]["currency"] == "KES"

    def test_a_published_product_appears_in_the_public_list(self, client, repo):
        repo.add(make_product("golden-hour", status="draft"))
        assert client.get(URL).json()["total"] == 0

        client.post(f"{URL}golden-hour/publish", headers=auth())

        assert [i["slug"] for i in client.get(URL).json()["items"]] == ["golden-hour"]

    def test_without_an_active_variant_returns_409_and_stays_a_draft(self, client, repo):
        product = make_product("golden-hour", status="draft", amounts=(100,), active=(False,))
        repo.add(product)

        response = client.post(f"{URL}golden-hour/publish", headers=auth())

        assert response.status_code == 409
        assert "active variant" in response.json()["detail"]
        assert repo.items[product.id].status == "draft"

    def test_unknown_slug_returns_404(self, client):
        assert client.post(f"{URL}no-such-product/publish", headers=auth()).status_code == 404

    def test_publishing_twice_is_harmless(self, client, repo):
        repo.add(make_product("golden-hour", status="draft"))
        client.post(f"{URL}golden-hour/publish", headers=auth())

        assert client.post(f"{URL}golden-hour/publish", headers=auth()).status_code == 200


class TestArchive:
    def test_moves_a_product_to_archived(self, client, repo):
        product = make_product("golden-hour", status="published")
        repo.add(product)

        response = client.post(f"{URL}golden-hour/archive", headers=auth())

        assert response.status_code == 200
        assert response.json()["status"] == "archived"
        assert repo.items[product.id].status == "archived"

    def test_an_archived_product_leaves_the_public_list(self, client, repo):
        repo.add(make_product("golden-hour", status="published"))
        assert client.get(URL).json()["total"] == 1

        client.post(f"{URL}golden-hour/archive", headers=auth())

        assert client.get(URL).json()["total"] == 0

    def test_an_archived_product_can_be_published_again(self, client, repo):
        repo.add(make_product("golden-hour", status="archived"))

        response = client.post(f"{URL}golden-hour/publish", headers=auth())

        assert response.status_code == 200
        assert response.json()["status"] == "published"

    def test_unknown_slug_returns_404(self, client):
        assert client.post(f"{URL}no-such-product/archive", headers=auth()).status_code == 404
