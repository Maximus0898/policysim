import json
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.models import Simulation, Round, AgentRoundResult
from backend.llm.factory import get_provider
from backend.llm.base import LLMMessage
import os
import pathlib

logger = logging.getLogger(__name__)

class Backtester:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.provider = get_provider()

    async def assess_historical_fit(self, simulation_id: int, scenario_id: str) -> Dict[str, Any]:
        """
        Calculates the Backtest Accuracy Score (Outcome 70% + Trajectory 30%).
        """
        # 1. Load Scenario Ground Truth
        scenario = self._load_scenario(scenario_id)
        if not scenario:
            return {"error": f"Scenario {scenario_id} not found."}

        # 2. Fetch Simulation Rounds
        rounds_res = await self.session.execute(
            select(Round).where(Round.simulation_id == simulation_id).order_by(Round.round_number)
        )
        sim_rounds = list(rounds_res.scalars().all())
        
        # 3. Calculate Trajectory Score (30%)
        traj_score, traj_details = self._calculate_trajectory_score(sim_rounds, scenario["historical_markers"])
        
        # 4. Calculate Outcome Score (70%)
        outcome_score, outcome_details = await self._calculate_outcome_score(sim_rounds, scenario["historical_markers"])
        
        # Final weighted score
        total_score = (outcome_score * 0.7) + (traj_score * 0.3)
        
        # Generate Divergence Log
        divergence_log = self._generate_divergence_log(sim_rounds, scenario["historical_markers"])

        return {
            "total_score": round(total_score, 1),
            "outcome_score": round(outcome_score, 1),
            "trajectory_score": round(traj_score, 1),
            "outcome_details": outcome_details,
            "trajectory_details": traj_details,
            "divergence_log": divergence_log,
            "historical_data": scenario["historical_markers"]
        }

    def _load_scenario(self, scenario_id: str) -> Optional[Dict[str, Any]]:
        path = pathlib.Path(__file__).parent.parent / "data" / "scenarios" / f"{scenario_id}.json"
        if not os.path.exists(path):
            return None
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _calculate_trajectory_score(self, rounds: List[Round], markers: List[Dict[str, Any]]) -> tuple[float, List[Dict]]:
        """
        MAE calculation with non-uniform bi-round weighting.
        Weights ramp from 0.5 (early) to 1.5 (late).
        """
        weights = [0.5, 1.0, 1.5] # For 3 checkpoints (R1, R3, R5)
        total_weighted_error = 0.0
        total_weight = 0.0
        details = []

        marker_map = {m["round"]: m for m in markers}
        sim_map = {r.round_number: r for r in rounds}

        for i, (r_num, marker) in enumerate(marker_map.items()):
            sim_r = sim_map.get(r_num)
            if not sim_r: continue

            # Get average sentiment from AgentRoundResult (cached/calculated)
            # In MVP we can pull this from the Round.synthesis_text if we stored it there, 
            # or calculate fresh. Let's assume we can get it.
            try:
                synth = json.loads(sim_r.synthesis_text)
                sim_sentiment = synth.get("avg_sentiment", 0.0) # We need to ensure runner stores this
            except:
                sim_sentiment = 0.0

            hist_sentiment = marker["sentiment"]
            error = abs(sim_sentiment - hist_sentiment)
            
            weight = weights[i] if i < len(weights) else 1.0
            total_weighted_error += error * weight
            total_weight += weight
            
            details.append({
                "round": r_num,
                "sim": sim_sentiment,
                "hist": hist_sentiment,
                "error": error,
                "weight": weight
            })

        if total_weight == 0: return 0.0, []
        
        # Accuracy = 100 * (1 - Weighted MAE / 2.0) -- normalizing stance range is 2.0 (-1 to 1)
        # Simplified: 100 * (1 - avg_error) handles typical drift
        avg_error = total_weighted_error / total_weight
        score = max(0, 100 * (1 - (avg_error / 0.5))) # 0.5 error is a "fail"
        return score, details

    async def _calculate_outcome_score(self, rounds: List[Round], markers: List[Dict[str, Any]]) -> tuple[float, List[Dict]]:
        """
        Binary outcome check with LLM-generated reasoning.
        """
        sim_summary = "\n".join([f"Round {r.round_number}: {r.synthesis_text}" for r in rounds])
        marker_summary = json.dumps(markers, indent=2)

        sys_prompt = """
        You are an institutional auditor. Compare the simulation outcome against historical markers.
        Criteria:
        1. Protests happened? (Matching history)
        2. Government responded? (Matching history)
        3. Policy status reversed/maintained? (Matching history)

        For each criterion, assign a score (0-100) and provide a concise 'audit_reasoning'.
        Output ONLY valid JSON:
        {
          "criteria": [
            {"label": "Public Outcry", "score": 80, "reasoning": "..."},
            {"label": "State Response", "score": 50, "reasoning": "..."},
            {"label": "Policy Outcome", "score": 100, "reasoning": "..."}
          ]
        }
        """
        user_prompt = f"SIMULATION HISTORY:\n{sim_summary}\n\nHISTORICAL TRUTH:\n{marker_summary}"
        
        res = await self.provider.chat([
            LLMMessage(role="system", content=sys_prompt),
            LLMMessage(role="user", content=user_prompt)
        ], temperature=0.1, response_format="json_object")
        
        try:
            data = json.loads(res.content)
            scores = [c["score"] for c in data["criteria"]]
            avg_score = sum(scores) / len(scores)
            return avg_score, data["criteria"]
        except:
            return 0.0, []

    def _generate_divergence_log(self, sim_rounds: List[Round], markers: List[Dict]) -> List[str]:
        log = []
        marker_map = {m["round"]: m for m in markers}
        sim_map = {r.round_number: r for r in sim_rounds}
        
        for r_num in sorted(marker_map.keys()):
            sim_r = sim_map.get(r_num)
            hist_m = marker_map[r_num]
            if not sim_r: continue
            
            # Simple heuristic for divergence: Sentiment delta > 0.4
            try:
                sim_s = json.loads(sim_r.synthesis_text).get("avg_sentiment", 0.0)
            except: sim_s = 0.0
            
            hist_s = hist_m["sentiment"]
            if abs(sim_s - hist_s) > 0.4:
                log.append(f"Round {r_num}: Simulation predicted {self._get_stance_label(sim_s)}, but history recorded {self._get_stance_label(hist_s)}.")
        
        return log

    def _get_stance_label(self, val: float) -> str:
        if val > 0.3: return "Support/Stability"
        if val < -0.3: return "Opposition/Unrest"
        return "Neutrality/Stalemate"
