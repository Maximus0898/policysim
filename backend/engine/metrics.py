import math
import statistics
from typing import List, Dict
from collections import defaultdict
from backend.models import Agent
from backend.regions.base import RegionProfile


def calculate_metrics(agents: List[Agent], region: RegionProfile) -> dict:
    """
    Computes system-wide metrics for the current round based on agent states.
    """
    if not agents:
        return {
            "avg_sentiment": 0.0,
            "sentiment_variance": 0.0,
            "protest_probability": 0.0
        }

    stances = [a.current_stance for a in agents]
    
    # 1. Average Sentiment
    avg_sentiment = sum(stances) / len(stances)
    
    # 2. Variance (Polarization)
    sentiment_variance = statistics.variance(stances) if len(stances) > 1 else 0.0
    
    # 3. Protest Probability (Sigmoid curve)
    # Count negative segment (stance < -0.2)
    negative_agents = [s for s in stances if s < -0.2]
    negative_ratio = len(negative_agents) / len(stances)
    
    # Sigmoid function: P = 1 / (1 + e^(-k * (x - x0)))
    # Where x = negative_ratio, x0 = region.protest_threshold
    # k determines the steepness of the curve
    k = 12.0
    x0 = region.protest_threshold
    
    # Cap exponential to prevent overflow
    exponent = -k * (negative_ratio - x0)
    exponent = max(min(exponent, 50), -50) 
    
    protest_prob = 1.0 / (1.0 + math.exp(exponent))
    
    return {
        "avg_sentiment": round(avg_sentiment, 4),
        "sentiment_variance": round(sentiment_variance, 4),
        "protest_probability": round(protest_prob, 4)
    }

def calculate_archetype_metrics(agents: List[Agent]) -> Dict[str, dict]:
    """
    Groups agents by archetype and returns average sentiment for each demographic slice.
    """
    if not agents:
        return {}
    
    import pandas as pd
    df = pd.DataFrame([
        {"archetype": a.archetype, "stance": a.current_stance} 
        for a in agents
    ])
    
    summary = df.groupby("archetype")["stance"].mean().to_dict()
    
    return {
        arch: {"avg_sentiment": round(val, 4)} 
        for arch, val in summary.items()
    }

