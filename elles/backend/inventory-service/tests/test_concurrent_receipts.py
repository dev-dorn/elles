import asyncio
import os
from uuid import uuid4

import httpx

BASE_URL = "http://localhost:8003/api/v1/stock"
SKU = f"RACE-{uuid4().hex[:12]}"
URL = f"{BASE_URL}/{SKU}/adjustment"

async def send_receipt(client: httpx.AsyncClient) -> tuple[int, dict]:
    response = await client.post(
        URL,
        json={"delta": 1, "reason": "received"},

    )
    return response.status_code, response.json()

async def main() -> None:
    token = os.environ["INVENTORY_TOKEN"]
    headers = {"Authorization": f"Bearer {token}"}
    limits = httpx.Limits(max_connections=30, max_keepalive_connections=30)

    async with httpx.AsyncClient(
        headers=headers,
        timeout=30,
        limits=limits,
    ) as client:
        results = await asyncio.gather(
            *(send_receipt(client) for _ in range(30)),
            return_exceptions=True,
        )

    failures = [result for result in results if isinstance(result, Exception)]
    responses = [result for result in results if not isinstance(result, Exception)]
    successful = [body for status, body in responses if status == 201]

    print(f"Test SKU: {SKU}")
    print(f"HTTP 201 responses: {len(successful)}/30")
    print(f"Request errors: {failures}")

    if successful:
        largest_on_hand = max(body["on_hand"] for body in successful)
        print(f"Largest returned on_hand: {largest_on_hand}")

    assert not failures
    assert len(successful) == 30
    assert largest_on_hand == 30


asyncio.run(main())