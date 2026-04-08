import asyncio
import json
from unittest.mock import AsyncMock, patch, MagicMock
from backend.engine.builder import WorldBuilder

class DummyLLM:
    async def chat(self, messages, temperature, response_format=None, max_tokens=1000):
        # determine which call it is based on messages
        user_msg = messages[-1].content
        mock_response = MagicMock()
        
        if "Policy Document:" in user_msg:
            # return PolicySummary
            val = {
                "title": "Mock Identity Act",
                "policy_type": "Social",
                "key_provisions": ["Provision 1"],
                "affected_demographics": ["All"],
                "economic_impact": "Cash injection",
                "implementation_timeline": "1 year",
                "government_rationale": "Boost tracking"
            }
            mock_response.content = json.dumps(val)
        else:
            # return AgentPopulation
            agents = []
            for i in range(40):
                is_key = i < 4
                agents.append({
                    "name": f"Agent {i}",
                    "archetype": "urban_professional",
                    "age": 30,
                    "income_level": "middle",
                    "education_level": "High School",
                    "political_lean": 0.5,
                    "policy_impact_score": 0.5,
                    "personality_traits": {"openness": 0.5},
                    "initial_stance": 0.5,
                    "influence_score": 0.9 if is_key else 0.1,
                    "is_key_figure": is_key,
                    "region_context": "City center"
                })
            mock_response.content = json.dumps({"agents": agents})
            
        return mock_response

async def main():
    print("--- Starting World Builder Verification (MOCK) ---")
    provider = DummyLLM()
    builder = WorldBuilder(provider)

    sample_policy = "Sample Policy Text"

    print("1. Extracting Policy Summary...")
    sim, agents = await builder.draft_simulation(
        title="Mock Act Sim",
        document_text=sample_policy,
        region_preset="uz"
    )

    summary = json.loads(sim.policy_summary)
    print("\n[Parsed Policy Data]")
    print(f"Title: {summary.get('title')}")
    print(f"Impact: {summary.get('economic_impact')}")

    print(f"\n2. Generating Agent Population (Target: 40)...")
    print(f"Total Agents Generated: {len(agents)}")
    
    key_figures = [a for a in agents if a.is_key_figure]
    print(f"Key Figures Generated: {len(key_figures)}")

    print("\n[Sample Agents (First 3)]")
    for a in agents[:3]:
        print(f"- {a.name} ({a.archetype}, {a.age_group}, {a.income}) | Stance: {a.initial_stance} | Key: {a.is_key_figure}")

    print("\n--- Verification Complete ---")

if __name__ == "__main__":
    asyncio.run(main())
