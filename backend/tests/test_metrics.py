import pytest
from backend.engine.metrics import calculate_metrics
from backend.regions.base import get_region
from backend.models import Agent

def test_calculate_metrics_protest_sigmoid():
    region = get_region("uz")
    region.protest_threshold = 0.5
    agents_all_support = [Agent(name="A", archetype="A", age_group="A", income="A", current_stance=1.0) for _ in range(10)]
    metrics_support = calculate_metrics(agents_all_support, region)
    assert metrics_support["protest_probability"] < 0.05
    
    agents_all_oppose = [Agent(name="A", archetype="A", age_group="A", income="A", current_stance=-1.0) for _ in range(10)]
    metrics_oppose = calculate_metrics(agents_all_oppose, region)
    assert metrics_oppose["protest_probability"] > 0.95


