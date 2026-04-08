import json
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.models import Simulation, Round, AgentRoundResult, Agent
from backend.llm.factory import get_provider
from backend.llm.base import LLMMessage
import pandas as pd
from jinja2 import Environment, FileSystemLoader
import os

logger = logging.getLogger(__name__)

class ReportingService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.provider = get_provider()

    async def get_heatmap_data(self, simulation_id: int) -> List[Dict[str, Any]]:
        """
        Fetches pivot data: Round -> Archetype -> Avg Sentiment.
        Used for the frontend heatmap visualization.
        """
        result = await self.session.execute(
            select(
                Round.round_number,
                Agent.archetype,
                AgentRoundResult.sentiment
            )
            .join(AgentRoundResult, Round.id == AgentRoundResult.round_id)
            .join(Agent, AgentRoundResult.agent_id == Agent.id)
            .where(Round.simulation_id == simulation_id)
            .order_by(Round.round_number, Agent.archetype)
        )
        
        rows = result.all()
        if not rows:
            return []
            
        df = pd.DataFrame(rows, columns=['round', 'archetype', 'sentiment'])
        
        # Pivot and calculate mean
        pivot = df.pivot_table(
            index='archetype', 
            columns='round', 
            values='sentiment', 
            aggfunc='mean'
        ).fillna(0)
        
        # Convert to a list of dicts for frontend: [{archetype: '...', rounds: [val, val, ...]}]
        formatted = []
        for arch, row in pivot.iterrows():
            formatted.append({
                "archetype": arch,
                "values": row.tolist()
            })
            
        return formatted

    async def synthesize_executive_brief(self, simulation_id: int) -> str:
        """
        Generates a 3-paragraph executive summary of the simulation rounds.
        """
        # Fetch simulation and all rounds
        sim_res = await self.session.execute(select(Simulation).where(Simulation.id == simulation_id))
        simulation = sim_res.scalar_one()
        
        rounds_res = await self.session.execute(
            select(Round).where(Round.simulation_id == simulation_id).order_by(Round.round_number)
        )
        rounds = list(rounds_res.scalars().all())
        
        if not rounds:
            return "No simulation data available for synthesis."

        # Compile round narratives
        narratives = []
        for r in rounds:
            try:
                synth = json.loads(r.synthesis_text)
                narratives.append(f"Round {r.round_number}: {synth.get('narrative_summary', '')}")
            except:
                narratives.append(f"Round {r.round_number}: [Data missing]")

        sys_msg = """
        You are a senior policy analyst. Summarize the simulation results into a clear, 3-paragraph executive brief.
        Focus on:
        1. The initial reaction to the policy.
        2. The key turning points or escalations during the simulation.
        3. The final predicted outcome and any critical demographic risk groups.
        Return ONLY the plain text synthesis. No markdown headers.
        """
        
        user_msg = f"""
        Simulation: {simulation.title}
        Policy Document: {simulation.policy_document_text[:1000]}...
        
        Round History:
        {chr(10).join(narratives)}
        """
        
        response = await self.provider.chat([
            LLMMessage(role="system", content=sys_msg),
            LLMMessage(role="user", content=user_msg)
        ], temperature=0.3)
        
        return response.content

    async def generate_pdf(self, simulation_id: int) -> bytes:
        """
        Generates a professional PDF report using fpdf2 (Pure Python).
        """
        from fpdf import FPDF
        
        # 1. Fetch Data
        sim_res = await self.session.execute(select(Simulation).where(Simulation.id == simulation_id))
        simulation = sim_res.scalar_one()
        
        agents_res = await self.session.execute(select(Agent).where(Agent.simulation_id == simulation_id))
        agents = list(agents_res.scalars().all())
        
        rounds_res = await self.session.execute(
            select(Round).where(Round.simulation_id == simulation_id).order_by(Round.round_number)
        )
        rounds = list(rounds_res.scalars().all())
        
        # Get brief
        summary = await self.synthesize_executive_brief(simulation_id)
        
        key_figures = [a for a in agents if a.is_key_figure]
        date_str = simulation.created_at.strftime("%Y-%m-%d")

        # 2. PDF Constructor
        class PDF(FPDF):
            def header(self):
                self.set_font("helvetica", "B", 8)
                self.set_text_color(150)
                self.cell(0, 10, f"INSTITUTIONAL PREDICTION BRIEF • {date_str}", border=0, align="L")
                self.ln(10)
                self.set_draw_color(0)
                self.line(10, 20, 200, 20)
                self.ln(5)

            def footer(self):
                self.set_y(-15)
                self.set_font("helvetica", "I", 8)
                self.set_text_color(150)
                self.cell(0, 10, f"Confidential Internal Briefing • PolicySim Engine • Page {self.page_no()}", 0, 0, "C")

        pdf = PDF()
        pdf.add_page()
        
        # Title
        pdf.set_font("helvetica", "B", 24)
        pdf.set_text_color(0)
        pdf.multi_cell(0, 15, simulation.title)
        pdf.ln(5)

        # Executive Summary
        pdf.set_font("helvetica", "B", 14)
        pdf.set_text_color(0, 86, 179) # Blue header
        pdf.cell(0, 10, "EXECUTIVE SUMMARY", ln=True)
        pdf.ln(2)
        
        pdf.set_font("helvetica", "I", 11)
        pdf.set_text_color(50)
        pdf.multi_cell(0, 7, summary)
        pdf.ln(10)

        # Key Figures Table
        pdf.set_font("helvetica", "B", 14)
        pdf.set_text_color(0, 86, 179)
        pdf.cell(0, 10, "KEY STAKEHOLDER STATUS", ln=True)
        pdf.ln(2)

        # Table Header
        pdf.set_font("helvetica", "B", 10)
        pdf.set_fill_color(240)
        pdf.set_text_color(0)
        pdf.cell(70, 10, "Figure Name", 1, 0, "L", True)
        pdf.cell(70, 10, "Archetype", 1, 0, "L", True)
        pdf.cell(50, 10, "Final Stance", 1, 1, "R", True)

        # Table rows
        pdf.set_font("helvetica", "", 10)
        for kf in key_figures:
            stance_pct = f"{(kf.current_stance * 100):.0f}%"
            pdf.cell(70, 10, kf.name, 1)
            pdf.cell(70, 10, kf.archetype, 1)
            pdf.cell(50, 10, stance_pct, 1, 1, "R")
        
        pdf.ln(10)

        # Timeline
        pdf.set_font("helvetica", "B", 14)
        pdf.set_text_color(0, 86, 179)
        pdf.cell(0, 10, "SIMULATION TIMELINE", ln=True)
        pdf.ln(2)

        for r in rounds:
            pdf.set_font("helvetica", "B", 10)
            pdf.set_text_color(0, 86, 179)
            pdf.cell(0, 7, f"ROUND {r.round_number}", ln=True)
            
            pdf.set_font("helvetica", "", 10)
            pdf.set_text_color(30)
            narrative = ""
            if r.synthesis_text:
                try:
                    narrative = json.loads(r.synthesis_text).get("narrative_summary", "")
                except:
                    narrative = "[Narrative parsing error]"
            
            pdf.multi_cell(0, 6, narrative)
            pdf.ln(5)

        return pdf.output()

