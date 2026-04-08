import asyncio
import json
from unittest.mock import MagicMock
from tqdm.asyncio import tqdm
from backend.llm.base import LLMProvider, LLMResponse, LLMMessage
from backend.engine.schemas import KeyFigureAction, MassAgentReaction, MassBatchResponse, RoundSynthesis
from backend.engine.runner import SimulationRunner
from backend.models import Simulation, Agent, SimulationStatus
import uuid

class DummyRunnerLLM(LLMProvider):
    async def chat(self, messages: list[LLMMessage], temperature, response_format=None, max_tokens=1000) -> LLMResponse:
        # Simulate local LLM delay
        await asyncio.sleep(0.5)
        
        user_msg = messages[-1].content
        sys_msg = messages[0].content
        
        mock_response = MagicMock()
        
        if "KeyFigureAction" in sys_msg:
            # Extract name from string hackily for mock
            lines = user_msg.split("\n")
            name = "Unknown"
            for line in lines:
                if "Name:" in line:
                    name = line.split("Name:")[1].strip()
                    break
            
            val = {
                "agent_name": name,
                "public_statement": f"I strongly disagree with this!",
                "new_stance": -0.5
            }
            mock_response.content = json.dumps(val)
            
        elif "MassBatchResponse" in sys_msg:
            # Extract IDs and mock shift them
            lines = user_msg.split("\n")
            reactions = []
            for line in lines:
                if "ID: " in line:
                    id_part = line.split("|")[0].split("ID:")[1].strip()
                    reactions.append({
                        "agent_id": id_part,
                        "new_stance": -0.2, # Shift everyone slightly negative
                        "emotional_reaction": "Concerned"
                    })
            mock_response.content = json.dumps({"reactions": reactions})
            
        elif "RoundSynthesis" in sys_msg:
            val = {
                "narrative_summary": "Tensions rose this round as key figures expressed dissent.",
                "key_events": ["A key figure spoke out", "Mass sentiment shifted notably negative"]
            }
            mock_response.content = json.dumps(val)
        else:
            mock_response.content = "{}"
            
        return mock_response

    def get_token_count(self, text: str) -> int:
        return len(text) // 4


async def run_test():
    print("--- Starting Simulation Runner Verification (MOCK) ---")
    provider = DummyRunnerLLM()
    runner = SimulationRunner(provider)
    
    # Setup mock initial state
    sim = Simulation(
        id=1,
        title="Test Sim",
        status=SimulationStatus.RUNNING,
        current_round=0,
        total_rounds=2
    )
    
    agents = []
    # 4 Key figures
    for i in range(4):
        agents.append(Agent(
            id=i,
            simulation_id=1,
            name=f"Key Figure {i}",
            archetype="politician",
            age_group="45-54",
            income="high",
            initial_stance=0.5,
            current_stance=0.5,
            is_key_figure=True
        ))
    
    # 36 Mass agents (Total 40)
    for i in range(4, 40):
        agents.append(Agent(
            id=i,
            simulation_id=1,
            name=f"Mass Agent {i}",
            archetype="citizen",
            age_group="25-34",
            income="middle",
            initial_stance=0.5,
            current_stance=0.5,
            is_key_figure=False
        ))

    print(f"Total Agents: {len(agents)}")
    print(f"Goal: Run 2 rounds with tqdm tracking.")
    
    # Let's wrap rounds in a tqdm to simulate the long-running simulation execution loop
    for round_num in tqdm(range(1, 3), desc="Simulation Rounds"):
        sim, agents, round_record, agent_results = await runner.run_round(
            sim, 
            agents, 
            injected_event="A controversial leak occurred." if round_num == 1 else None
        )
        
        synthesis = json.loads(round_record.synthesis_text)
        print(f"\n[Round {sim.current_round} Complete]")
        print(f"Narrative: {synthesis.get('narrative_summary')}")
        
        # Test Metrics Output
        stances = [a.current_stance for a in agents]
        avg = sum(stances) / len(agents)
        print(f"New Avg Stance: {avg:.2f}")

    print("\n--- Verification Complete ---")

if __name__ == "__main__":
    asyncio.run(run_test())
