import os
from datetime import datetime, timezone

import pytest
import pytest_asyncio
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from inventory_app.domain.models.models import StockItem
from inventory_app.infrastructure.persistence.postgres.models import StockItemModel
from inventory_app.infrastructure.persistence.postgres.repositories import PostgresStockRepository
from tests.fakes import InMemoryStockRepository


@pytest_asyncio.fixture(params=("memory", "postgres"))
async def stock_repository(request):
    if request.param == "memory":
        yield InMemoryStockRepository()
        return

    postgres_url = os.getenv("INVENTORY_TEST_POSTGRES_URL")
    if not postgres_url:
        pytest.skip("Set INVENTORY_TEST_POSTGRES_URL to a dedicated test database.")

    engine = create_async_engine(postgres_url, pool_pre_ping=True)
    table = StockItemModel.__table__
    async with engine.begin() as connection:
        await connection.run_sync(table.drop, checkfirst=True)
        await connection.run_sync(table.create)

    session = async_sessionmaker(engine, expire_on_commit=False)()
    try:
        yield PostgresStockRepository(session)
    finally:
        await session.rollback()
        await session.close()
        async with engine.begin() as connection:
            await connection.run_sync(table.drop, checkfirst=True)
        await engine.dispose()


@pytest.mark.asyncio
async def test_get_stock_returns_stock_item_and_available_quantity(stock_repository):
    expected = StockItem(
        sku="SKU-001",
        on_hand=10,
        reserved=3,
        updated_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )
    await stock_repository.save(expected)

    actual = await stock_repository.get_stock("SKU-001")

    assert actual == expected
    assert actual.available == 7


@pytest.mark.asyncio
async def test_get_stock_returns_none_for_unknown_sku(stock_repository):
    assert await stock_repository.get_stock("missing") is None


@pytest.mark.asyncio
async def test_get_stock_many_returns_only_matching_unique_skus(stock_repository):
    item_a = StockItem(sku="SKU-A", on_hand=5, reserved=1)
    item_b = StockItem(sku="SKU-B", on_hand=8, reserved=0)
    await stock_repository.save(item_a)
    await stock_repository.save(item_b)

    actual = await stock_repository.get_stock_many(
        ["SKU-B", "missing", "SKU-A", "SKU-B"]
    )

    assert actual == {"SKU-A": item_a, "SKU-B": item_b}
    assert await stock_repository.get_stock_many([]) == {}


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("on_hand", "reserved"),
    [(-1, 0), (2, 3), (0, -1)],
)
async def test_postgres_rejects_invalid_stock_quantities(
    stock_repository,
    on_hand: int,
    reserved: int,
):
    if not isinstance(stock_repository, PostgresStockRepository):
        pytest.skip("Database constraints are verified against PostgreSQL only.")

    stock_repository.session.add(
        StockItemModel(
            sku=f"BAD-{on_hand}-{reserved}",
            on_hand=on_hand,
            reserved=reserved,
        )
    )
    with pytest.raises(IntegrityError):
        await stock_repository.session.flush()
    await stock_repository.session.rollback()
