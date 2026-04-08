from sqlmodel import SQLModel, Field, Relationship, JSON
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class SimulationStatus(str, Enum):
    DRAFT = "draft"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"

class SimulationBase(SQLModel):
    title: str
    description: Optional[str] = None
    system_prompt: Optional[str] = None
    policy_document_text: str = ""
    policy_summary: str = ""
    region_preset: str = ""
    status: SimulationStatus = SimulationStatus.DRAFT
    current_round: int = 0
    total_rounds: int = 25
    agent_count: int = 40
    scenario_description: str = ""
    pending_event: Optional[str] = None



class Simulation(SimulationBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    agents: List["Agent"] = Relationship(back_populates="simulation")
    rounds: List["Round"] = Relationship(back_populates="simulation")

class AgentBase(SQLModel):
    name: str
    archetype: str
    persona: str = ""
    age_group: str # 18-24, 25-34, etc.
    income: str    # Low, Middle, High, etc.
    initial_stance: float = 0.5 # 0.0 to 1.0
    current_stance: float = 0.5
    influence_score: float = 1.0 # renamed from influence for consistency
    political_lean: float = 0.0
    policy_impact_score: float = 0.0
    personality_traits: str = "" 
    is_key_figure: bool = False
    region_context: str = ""
    regional_data: Dict[str, Any] = Field(default={}, sa_type=JSON)



class Agent(AgentBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    simulation_id: int = Field(foreign_key="simulation.id")
    
    simulation: Simulation = Relationship(back_populates="agents")
    round_results: List["AgentRoundResult"] = Relationship(back_populates="agent")

class RoundBase(SQLModel):
    round_number: int
    event_text: str
    synthesis_text: Optional[str] = None

class Round(RoundBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    simulation_id: int = Field(foreign_key="simulation.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    simulation: Simulation = Relationship(back_populates="rounds")
    agent_results: List["AgentRoundResult"] = Relationship(back_populates="round")

class AgentRoundResult(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    stance_value: float
    sentiment: float # -1.0 to 1.0
    
    agent_id: int = Field(foreign_key="agent.id")
    round_id: int = Field(foreign_key="round.id")
    
    agent: Agent = Relationship(back_populates="round_results")
    round: Round = Relationship(back_populates="agent_results")


class AgentRelationship(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    simulation_id: int = Field(foreign_key="simulation.id")
    source_agent_id: int = Field(foreign_key="agent.id")
    target_agent_id: int = Field(foreign_key="agent.id")
    relationship_type: str = "influences"  # influences, opposes, supports, follows
    strength: float = 0.5  # 0.0 to 1.0

