import json
from typing import Optional, List
from backend.llm.base import LLMProvider, LLMMessage
from backend.engine.schemas import PolicySummary, AgentProfile, AgentPopulation, AgentRelationshipItem, AgentRelationshipGraph
from backend.regions.base import RegionProfile, get_default_region
from backend.models import Agent, Simulation, SimulationStatus
from datetime import datetime, timezone

class WorldBuilder:
    def __init__(self, llm_provider: LLMProvider):
        self.llm = llm_provider

    async def extract_policy(self, text: str) -> PolicySummary:
        sys_prompt = "You are an expert policy analyst. Read the text and extract the structured policy summary. Return ONLY valid JSON matching the schema."
        user_prompt = f"Policy Document:\n{text}\n\nExtract the summary parameters in JSON format. Do not use Markdown wrapping."

        messages = [
            LLMMessage("system", sys_prompt),
            LLMMessage("user", user_prompt)
        ]

        # Use native JSON mode if available/supported by the SDK wrapper
        res = await self.llm.chat(messages, temperature=0.2, response_format="json_object")
        
        try:
            # Parse response
            data = json.loads(res.content)
            return PolicySummary(**data)
        except Exception as e:
            raise ValueError(f"Failed to parse PolicySummary from LLM: {str(e)}\nRaw: {res.content}")

    async def generate_agents(self, policy: PolicySummary, region: RegionProfile, count: int = 40) -> List[AgentProfile]:
        # Synthesize prompt
        archetype_reqs = []
        for arch, pct in region.archetype_distribution.items():
            num = int(round(count * pct))
            if num > 0:
                archetype_reqs.append(f"- {num} x {arch}")
        
        sys_prompt = "You are an expert sociologist and world builder. Generate a diverse population array of strictly specified personas based on region context and the policy being implemented. Return ONLY valid JSON matching the schema ({ \"agents\": [ ... ] })."
        
        user_prompt = f"""
        Region: {region.name}
        Context: {region.economic_context} {region.cultural_notes}

        Policy Context:
        Title: {policy.title}
        Impact: {policy.economic_impact}

        Requirements:
        Generate exactly {count} agents.
        Ensure 3-5 of the total agents are marked as 'is_key_figure=true' (e.g., politicians, journalists, influencers). The rest should be false.
        
        Distribution required:
        {chr(10).join(archetype_reqs)}

        Output strictly as JSON containing an 'agents' list.
        """

        messages = [
            LLMMessage("system", sys_prompt),
            LLMMessage("user", user_prompt)
        ]

        # Use slightly higher temp for variety
        res = await self.llm.chat(messages, temperature=0.7, response_format="json_object", max_tokens=8000)
        
        try:
            data = json.loads(res.content)
            population = AgentPopulation(**data)
            return population.agents
        except Exception as e:
            raise ValueError(f"Failed to parse AgentPopulation from LLM: {str(e)}\nRaw: {res.content}")

    async def draft_simulation(self, title: str, document_text: str, region_preset: str) -> tuple[Simulation, List[Agent], List[AgentRelationshipItem]]:
        # 1. Load Region
        region = get_default_region() # Currently hardcoded to mock

        # 2. Extract Policy
        policy_summary = await self.extract_policy(document_text)

        # 3. Generate Agents Profiles
        agent_profiles = await self.generate_agents(policy_summary, region, count=40)

        # 4. Generate Social Relationships
        relationships = await self.generate_relationships(agent_profiles)

        # 4. Create Draft Entities
        
        sim = Simulation(
            title=title,
            policy_document_text=document_text,
            policy_summary=json.dumps(policy_summary.model_dump()),
            region_preset=region.code,
            status=SimulationStatus.DRAFT,
            current_round=0,
            total_rounds=25, # Default
            created_at=datetime.now(timezone.utc),
            agent_count=len(agent_profiles),
            scenario_description="Draft prediction run."
        )

        db_agents = []
        for ap in agent_profiles:
            db_agents.append(Agent(
                name=ap.name,
                archetype=ap.archetype,
                persona="",
                age_group=self._map_age_group(ap.age),
                income=ap.income_level,
                political_lean=ap.political_lean,
                policy_impact_score=ap.policy_impact_score,
                personality_traits=json.dumps(ap.personality_traits),
                initial_stance=ap.initial_stance,
                current_stance=ap.initial_stance,
                influence_score=ap.influence_score,
                is_key_figure=ap.is_key_figure,
                region_context=ap.region_context
            ))

        return sim, db_agents, relationships

    async def generate_relationships(self, agents: List[AgentProfile]) -> List[AgentRelationshipItem]:
        agent_list = "\n".join(
            f"- {a.name} ({a.archetype}, key_figure={a.is_key_figure})"
            for a in agents
        )
        sys_prompt = (
            "You are a social network analyst. Given a list of agents in a political simulation, "
            "generate a realistic directed social influence graph. Key figures (politicians, journalists) "
            "should have higher out-degree. Return ONLY valid JSON matching the schema "
            '({ "relationships": [ { "source_name": ..., "target_name": ..., "relationship_type": ..., "strength": ... } ] }).'
        )
        user_prompt = (
            f"Agents:\n{agent_list}\n\n"
            "Generate 20-30 directed relationships. "
            "Types: 'influences', 'opposes', 'supports', 'follows'. "
            "Strength: 0.1 (weak) to 1.0 (strong). "
            "Ensure diverse types — not all influences. Return JSON only."
        )
        res = await self.llm.chat(
            [LLMMessage("system", sys_prompt), LLMMessage("user", user_prompt)],
            temperature=0.5,
            response_format="json_object",
            max_tokens=4000
        )
        try:
            data = json.loads(res.content)
            graph = AgentRelationshipGraph(**data)
            return graph.relationships
        except Exception as e:
            # Non-fatal: return empty list if generation fails
            print(f"[WorldBuilder] Relationship generation failed: {e}")
            return []

    def _map_age_group(self, age: int) -> str:
        if age < 25: return "18-24"
        elif age <= 34: return "25-34"
        elif age <= 44: return "35-44"
        elif age <= 54: return "45-54"
        elif age <= 64: return "55-64"
        else: return "65+"
