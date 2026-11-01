import pytest
from pydantic import TypeAdapter

from catalog_app.application.dtos.product_dtos import CreateProductRequest
from catalog_app.application.use_cases.create_product import CreateProductUseCase
from catalog_app.domain.exceptions import DuplicateProductError
from tests.helpers import ADMIN_ID, fragrance_payload, makeup_payload

adapter = TypeAdapter(CreateProductRequest)


def parse(payload):
    return adapter.validate_python(payload)


async def test_saves_a_draft_owned_by_the_creator(repo):
    await CreateProductUseCase(repo).execute(parse(makeup_payload()), created_by=ADMIN_ID)

    saved = await repo.get_by_slug("velvet-matte-lipstick")
    assert saved is not None
    assert saved.created_by == ADMIN_ID
    assert saved.status == "draft"
    assert saved.variants[0].price.amount == 185000


async def test_a_variant_without_a_size_is_stored_without_one(repo):
    await CreateProductUseCase(repo).execute(parse(makeup_payload()), created_by=ADMIN_ID)

    saved = await repo.get_by_slug("velvet-matte-lipstick")
    assert saved.variants[0].size is None


async def test_sizes_are_carried_over(repo):
    await CreateProductUseCase(repo).execute(parse(fragrance_payload()), created_by=ADMIN_ID)

    saved = await repo.get_by_slug("golden-hour-eau-de-parfum")
    assert [(v.size.value, v.size.unit) for v in saved.variants] == [(50, "ml"), (100, "ml")]


async def test_attributes_are_stored_without_empty_values(repo):
    await CreateProductUseCase(repo).execute(parse(makeup_payload()), created_by=ADMIN_ID)

    attributes = (await repo.get_by_slug("velvet-matte-lipstick")).attributes
    assert attributes["finish"] == "matte"
    assert "coverage" not in attributes  # None values are dropped


async def test_the_product_does_not_share_lists_with_the_request(repo):
    request = parse(makeup_payload())
    product = await CreateProductUseCase(repo).execute(request, created_by=ADMIN_ID)

    assert product.benefits is not request.benefits
    assert product.variants[0].images is not request.variants[0].images


async def test_duplicate_slug_is_rejected(repo):
    use_case = CreateProductUseCase(repo)
    await use_case.execute(parse(makeup_payload()), created_by=ADMIN_ID)

    with pytest.raises(DuplicateProductError):
        await use_case.execute(parse(makeup_payload()), created_by=ADMIN_ID)
    assert len(repo.items) == 1
