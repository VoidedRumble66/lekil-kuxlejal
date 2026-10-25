import asyncio
import httpx
import pytest
from main import app

@pytest.mark.anyio
async def test_concurrent_sse_connections():
    """SC-005: El motor debe soportar 10 conexiones SSE simultáneas sin degrado perceptible"""
    num_clients = 10
    
    async def connect_client(client_id):
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            params = {
                "water_total_liters": 1000.0,
                "energy_total_kwh": 100.0,
                "num_inhabitants": 10,
                "cultivable_area_m2": 20.0,
                "max_generations": 20,
                "emit_every_n": 5
            }
            
            async with client.stream("GET", "/api/evolution-stream", params=params) as response:
                assert response.status_code == 200
                events = 0
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        events += 1
                return events

    # Run 10 clients concurrently
    tasks = [connect_client(i) for i in range(num_clients)]
    results = await asyncio.gather(*tasks)
    
    for count in results:
        assert count > 0, "Client did not receive any events"
