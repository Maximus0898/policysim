from pydantic import BaseModel, Field
from typing import List, Dict, Optional

class PolicySummary(BaseModel):
    title: str = Field(description="A short, descriptive title for the policy.")
    policy_type: str = Field(description="The general category of the policy (e.g., Economic, Social, Infrastructure).")
    key_provisions: List[str] = Field(description="Bullet points of the main actions the policy takes.")
    affected_demographics: List[str] = Field(description="Which demographic groups are most affected.")
    economic_impact: str = Field(description="A short sentence on the expected economic impact.")
    implementation_timeline: str = Field(description="When the policy takes effect.")
    government_rationale: str = Field(description="The stated reason the government is enacting this policy.")

class AgentProfile(BaseModel):
    name: str = Field(description="A realistic name for the agent matching the region's culture.")
    archetype: str = Field(description="The demographic category (e.g., urban_professional, rural_farmer).")
    age: int = Field(description="Age in years.")
    income_level: str = Field(description="Must be exactly: 'low', 'middle', or 'high'.")
    education_level: str = Field(description="Short description of education (e.g., 'High School', 'University').")
    political_lean: float = Field(description="Float from -1.0 (opposition) to 1.0 (pro-government).")
    policy_impact_score: float = Field(description="How directly this policy affects them. -1.0 (very negative) to 1.0 (very positive).")
    personality_traits: Dict[str, float] = Field(description="Key-value pairs of Big Five traits (0.0 to 1.0), e.g., {'openness': 0.7}.")
    initial_stance: float = Field(description="Float from -1.0 (strongly oppose) to 1.0 (strongly support).")
    influence_score: float = Field(description="Social reach. 0.0 to 1.0.")
    is_key_figure: bool = Field(description="True if they are a politician, influencer, or journalist.")
    region_context: str = Field(description="1-sentence backstory about where they live and work.")

class AgentPopulation(BaseModel):
    agents: List[AgentProfile] = Field(description="The generated list of agents.")

# --- Phase 5: Simulation Core Schemas ---

class KeyFigureAction(BaseModel):
    agent_name: str = Field(description="Name of the key figure.")
    public_statement: str = Field(description="A short, in-character public quote or statement made by the figure.")
    new_stance: float = Field(description="Float from -1.0 to 1.0 representing their updated stance.")

class MassAgentReaction(BaseModel):
    agent_id: str = Field(description="The UUID of the agent this reaction belongs to.")
    new_stance: float = Field(description="Float from -1.0 to 1.0 representing their updated stance.")
    emotional_reaction: str = Field(description="A short phrase describing their internal feeling.")

class MassBatchResponse(BaseModel):
    reactions: List[MassAgentReaction] = Field(description="List of reactions for all agents requested.")

class RoundSynthesis(BaseModel):
    narrative_summary: str = Field(description="A 2-3 paragraph news-style summary of the round's events.")
    key_events: List[str] = Field(description="3-5 bullet points of the most critical shifts or actions.")


# --- Phase 9: Network Graph Schemas ---

class AgentRelationshipItem(BaseModel):
    source_name: str = Field(description="The name of the influencing agent.")
    target_name: str = Field(description="The name of the agent being influenced.")
    relationship_type: str = Field(description="Type: 'influences', 'opposes', 'supports', or 'follows'.")
    strength: float = Field(description="Relationship strength from 0.1 (weak) to 1.0 (strong).")

class AgentRelationshipGraph(BaseModel):
    relationships: List[AgentRelationshipItem] = Field(description="The full social graph as directed relationships.")


