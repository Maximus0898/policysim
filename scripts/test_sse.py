import asyncio
import httpx
from uvicorn import Config, Server
from backend.main import app
from unittest.mock import patch, MagicMock
from backend.llm.base import LLMProvider, LLMResponse, LLMMessage
import json

# Setup mock LLM for testing
class ApiTestRunnerLLM(LLMProvider):
    async def chat(self, messages: list[LLMMessage], temperature, response_format=None, max_tokens=1000) -> LLMResponse:
        # 1-second delay for background realism
        await asyncio.sleep(1.0)
        sys_msg = messages[0].content
        mock_response = MagicMock()
        
        # Determine World Builder vs Runner
        if "policy analyst" in sys_msg.lower():
            val = {
                "title": "API Auth Act", "policy_type": "Social", "key_provisions": [],
                "affected_demographics": [], "economic_impact": "None", "implementation_timeline": "1 year",
                "government_rationale": "Test API"
            }
            mock_response.content = json.dumps(val)
        elif "sociologist" in sys_msg.lower():
            agents = []
            for i in range(15):
                agents.append({
                    "name": f"Agent {i}", "archetype": "citizen", "age": 30, "income_level": "middle",
                    "education_level": "-", "political_lean": 0.0, "policy_impact_score": 0.0,
                    "personality_traits": {}, "initial_stance": 0.5, "influence_score": 0.5,
                    "is_key_figure": (i == 0), "region_context": ""
                })
            mock_response.content = json.dumps({"agents": agents})
        elif "KeyFigureAction" in sys_msg:
            val = {"agent_name": "Agent 0", "public_statement": "API Streaming is working!", "new_stance": 0.8}
            mock_response.content = json.dumps(val)
        elif "MassBatchResponse" in sys_msg:
            mock_response.content = json.dumps({"reactions": []})
        elif "RoundSynthesis" in sys_msg:
            val = {"narrative_summary": "SSE event sent out.", "key_events": ["Test Event"]}
            mock_response.content = json.dumps(val)
        else:
            mock_response.content = "{}"
            
        return mock_response
        
    def get_token_count(self, text: str) -> int:
        return len(text) // 4

@patch('backend.api.routes.get_provider', return_value=ApiTestRunnerLLM())
@patch('backend.services.simulation_service.get_provider', return_value=ApiTestRunnerLLM())
async def run_client_test(mock_runner, mock_builder):
    # 1. Start Server
    config = Config(app=app, host="127.0.0.1", port=8000, log_level="error")
    server = Server(config)
    
    server_task = asyncio.create_task(server.serve())
    await asyncio.sleep(2) # wait for boot
    
    url = "http://127.0.0.1:8000/api/simulations"
    
    async with httpx.AsyncClient() as client:
        print("--- 1. Testing POST World Builder ---")
        payload = {
            "title": "API Test",
            "policy_document_text": "Random text.",
            "region_preset": "uz"
        }
        resp = await client.post(url + "/", json=payload)
        data = resp.json()
        sim_id = data["simulation_id"]
        print(f"Created Draft Simulation: ID {sim_id}")
        
        print("\n--- 2. Connecting to SSE Stream ---")
        stream_task = asyncio.create_task(listen_to_sse(client, url, sim_id))
        
        print("\n--- 3. Triggering Background Loop (2 Rounds) ---")
        await client.post(url + f"/{sim_id}/start", json={"rounds": 2})
        
        # Wait for SSE task to naturally exit when "completion" is yielded
        await stream_task
        
    print("\n--- Verification Complete ---")
    server.should_exit = True
    await server_task

async def listen_to_sse(client, base_url, sim_id):
    stream_url = base_url + f"/{sim_id}/stream"
    try:
        # Need to use standard httpx stream instead of sse client logic for a raw test script to avoid extra SSE deps here
        # httpx stream
        async with client.stream("GET", stream_url, timeout=10.0) as response:
            async for line in response.aiter_lines():
                if line.startswith("data:"):
                    # Process SSE payload
                    payload = json.loads(line[5:])
                    type_str = payload.get("type")
                    if type_str == "round_update":
                        print(f"-> [SSE] Round {payload.get('round_number')} Received. Raw Payload: {payload}")
                    elif type_str == "completion":
                        print("-> [SSE] Received Completion Signal! Exiting listener.")
                        break
    except Exception as e:
        print(f"SSE Listener error: {e}")

if __name__ == "__main__":
    asyncio.run(run_client_test())
