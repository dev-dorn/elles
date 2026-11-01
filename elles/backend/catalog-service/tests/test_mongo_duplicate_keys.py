"""MongoProductRepository.save must turn MongoDB's duplicate-key errors into DuplicateProductError.

The in-memory fake already raises that type, so only the real repository can get this wrong.
A stub collection stands in for MongoDB: no server is needed.
"""
import pytest
from pymongo.errors import DuplicateKeyError

from catalog_app.domain.exceptions import DuplicateProductError
from catalog_app.infrastructure.persistence.mongodb.product_repository import MongoProductRepository
from tests.helpers import make_product


class StubCollection:
    def __init__(self, error: Exception):
        self._error = error

    async def replace_one(self, *args, **kwargs):
        raise self._error


def repository_failing_with(error: Exception) -> MongoProductRepository:
    return MongoProductRepository({"products": StubCollection(error)})  # type: ignore[arg-type]


def duplicate_key(pattern: dict) -> DuplicateKeyError:
    return DuplicateKeyError("E11000 duplicate key error", 11000, {"keyPattern": pattern})


async def test_a_duplicate_slug_becomes_a_duplicate_product_error():
    repo = repository_failing_with(duplicate_key({"slug": 1}))

    with pytest.raises(DuplicateProductError, match="already exists"):
        await repo.save(make_product("golden-hour"))


async def test_the_error_names_the_slug():
    repo = repository_failing_with(duplicate_key({"slug": 1}))

    with pytest.raises(DuplicateProductError, match="golden-hour"):
        await repo.save(make_product("golden-hour"))


async def test_a_duplicate_sku_becomes_a_duplicate_product_error():
    repo = repository_failing_with(duplicate_key({"variants.sku": 1}))

    with pytest.raises(DuplicateProductError, match="SKU"):
        await repo.save(make_product("golden-hour"))


async def test_any_other_duplicate_key_still_becomes_a_duplicate_product_error():
    repo = repository_failing_with(duplicate_key({"something_else": 1}))

    with pytest.raises(DuplicateProductError):
        await repo.save(make_product("golden-hour"))


async def test_a_duplicate_key_error_without_details_is_still_translated():
    repo = repository_failing_with(DuplicateKeyError("E11000 duplicate key error", 11000, None))

    with pytest.raises(DuplicateProductError):
        await repo.save(make_product("golden-hour"))
