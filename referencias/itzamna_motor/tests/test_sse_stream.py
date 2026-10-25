import pytest
import json
from httpx import AsyncClient, ASGITransport
from main import app

@pytest.mark.anyio
async def test_evolution_stream_emits_events():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        params = {
            "water_total_liters": 1000.0,
            "energy_total_kwh": 100.0,
            "num_inhabitants": 10,
            "cultivable_area_m2": 20.0,
            "max_generations": 20,  # Smaller for fast test
            "emit_every_n": 5
        }
        
        # Test stream
        events_received = 0
        final_received = False
        
        async with client.stream("GET", "/api/evolution-stream", params=params) as response:
            assert response.status_code == 200
            
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = json.loads(line[6:])
                    events_received += 1
                    if data["is_final"]:
                        final_received = True
                        
        assert events_received > 0
        assert final_received
