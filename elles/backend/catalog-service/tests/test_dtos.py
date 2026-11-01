import pytest
from pydantic import TypeAdapter, ValidationError

from catalog_app.application.dtos.product_dtos import CreateProductRequest
from tests.helpers import fragrance_payload, makeup_payload

adapter = TypeAdapter(CreateProductRequest)

# One valid attributes example per category.
CATEGORY_ATTRIBUTES = {
    "makeup": {"finish": "matte", "coverage": "full"},
    "fragrance": {"concentration": "eau-de-parfum"},
    "skincare": {"skin_types": ["dry"], "spf": 30},
    "haircare": {"hair_types": ["curly"]},
    "bodycare": {"scent": "vanilla"},
    "nails": {"finish": "glossy"},
    "tools": {"material": "foam", "reusable": True},
}

SIZED_VARIANT = [{"sku": "SKU-1", "size": {"value": 50, "unit": "ml"}, "price": {"amount": 1000}}]


def build(**overrides):
    return makeup_payload(**overrides)


class TestCategories:
    @pytest.mark.parametrize("category,attributes", CATEGORY_ATTRIBUTES.items())
    def test_each_category_accepts_its_own_attributes(self, category, attributes):
        model = adapter.validate_python(
            build(category=category, attributes=attributes, variants=SIZED_VARIANT)
        )
        assert model.category == category

    def test_unknown_category_is_rejected(self):
        with pytest.raises(ValidationError):
            adapter.validate_python(build(category="furniture"))

    def test_missing_category_is_rejected(self):
        payload = build()
        del payload["category"]
        with pytest.raises(ValidationError):
            adapter.validate_python(payload)

    def test_attributes_from_another_category_are_rejected(self):
        with pytest.raises(ValidationError):
            adapter.validate_python(build(attributes={"concentration": "eau-de-parfum"}))

    def test_invalid_attribute_value_is_rejected(self):
        with pytest.raises(ValidationError):
            adapter.validate_python(build(attributes={"finish": "sparkly"}))


class TestFragrance:
    def test_requires_a_concentration(self):
        with pytest.raises(ValidationError) as exc:
            adapter.validate_python(fragrance_payload(attributes={"scent_family": ["floral"]}))
        assert "concentration" in str(exc.value)

    def test_every_variant_needs_a_size(self):
        payload = fragrance_payload(variants=[{"sku": "NO-SIZE", "price": {"amount": 1000}}])
        with pytest.raises(ValidationError) as exc:
            adapter.validate_python(payload)
        assert "size" in str(exc.value)


class TestCommonRules:
    @pytest.mark.parametrize("slug", ["ok-slug-1", "abc", "a1-b2-c3"])
    def test_valid_slugs(self, slug):
        assert adapter.validate_python(build(slug=slug)).slug == slug

    @pytest.mark.parametrize(
        "slug", ["Has-Caps", "under_score", "-leading", "trailing-", "double--hyphen", "has space", "ab"]
    )
    def test_invalid_slugs(self, slug):
        with pytest.raises(ValidationError):
            adapter.validate_python(build(slug=slug))

    def test_unknown_top_level_field_is_rejected(self):
        with pytest.raises(ValidationError):
            adapter.validate_python(build(how_too_use=["typo"]))

    def test_client_cannot_set_created_by(self):
        with pytest.raises(ValidationError):
            adapter.validate_python(build(created_by="c86af85a-f58d-4235-b4ad-f2153eb15e69"))

    def test_only_draft_status_is_accepted_on_create(self):
        with pytest.raises(ValidationError):
            adapter.validate_python(build(status="published"))

    def test_at_least_one_variant_is_required(self):
        with pytest.raises(ValidationError):
            adapter.validate_python(build(variants=[]))

    def test_duplicate_skus_in_one_request_are_rejected(self):
        variants = [
            {"sku": "SAME", "price": {"amount": 100}},
            {"sku": "SAME", "price": {"amount": 200}},
        ]
        with pytest.raises(ValidationError) as exc:
            adapter.validate_python(build(variants=variants))
        assert "Duplicate SKUs" in str(exc.value)

    def test_description_has_a_minimum_length(self):
        with pytest.raises(ValidationError):
            adapter.validate_python(build(description="short"))

    def test_text_is_stripped_of_surrounding_whitespace(self):
        assert adapter.validate_python(build(name="  Padded Name  ")).name == "Padded Name"


class TestPrice:
    @pytest.mark.parametrize("amount", [0, -100, 12.5])
    def test_amount_must_be_a_positive_whole_number(self, amount):
        variants = [{"sku": "S1", "price": {"amount": amount}}]
        with pytest.raises(ValidationError):
            adapter.validate_python(build(variants=variants))

    def test_currency_is_uppercased(self):
        variants = [{"sku": "S1", "price": {"amount": 100, "currency": "kes"}}]
        assert adapter.validate_python(build(variants=variants)).variants[0].price.currency == "KES"

    def test_currency_defaults_to_kes(self):
        variants = [{"sku": "S1", "price": {"amount": 100}}]
        assert adapter.validate_python(build(variants=variants)).variants[0].price.currency == "KES"

    @pytest.mark.parametrize("currency", ["KE", "KESS", "K3S", "123"])
    def test_currency_must_be_three_letters(self, currency):
        variants = [{"sku": "S1", "price": {"amount": 100, "currency": currency}}]
        with pytest.raises(ValidationError):
            adapter.validate_python(build(variants=variants))
