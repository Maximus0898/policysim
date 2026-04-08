from pydantic import BaseModel
from typing import Dict

class RegionProfile(BaseModel):
    name: str
    code: str
    language_context: str
    trust_in_government_baseline: float
    protest_threshold: float
    media_landscape: str
    economic_context: str
    archetype_distribution: Dict[str, float]
    cultural_notes: str

def get_region(code: str) -> RegionProfile:
    """Factory to retrieve a region profile by code."""
    presets = {
        "uz": RegionProfile(
            name="Uzbekistan (Preset)",
            code="uz",
            language_context="Post-Soviet Central Asian society, collectivist culture.",
            trust_in_government_baseline=0.55,
            protest_threshold=0.72,
            media_landscape="State-dominant media, growing independent online press.",
            economic_context="Lower-middle income, significant informal economy.",
            archetype_distribution={
                "urban_professional": 0.15, "rural_household": 0.30, 
                "small_business_owner": 0.12, "transport_worker": 0.10,
                "government_employee": 0.13, "student_youth": 0.10,
                "opposition_figure": 0.02, "journalist_state": 0.02,
                "journalist_independent": 0.02, "religious_community_leader": 0.04
            },
            cultural_notes="Family and mahalla networks are primary information channels."
        ),
        "kz": RegionProfile(
            name="Kazakhstan (Standard)",
            code="kz",
            language_context="Bilingual Russian/Kazakh society. Urbanized and resource-rich.",
            trust_in_government_baseline=0.48,
            protest_threshold=0.65,
            media_landscape="Digital-native news ecosystem with strong social media influence.",
            economic_context="High reliance on energy exports; significant wealth inequality.",
            archetype_distribution={
                "urban_professional": 0.20, "rural_household": 0.20,
                "small_business_owner": 0.15, "energy_sector_worker": 0.15,
                "government_employee": 0.10, "student_youth": 0.12,
                "opposition_figure": 0.03, "journalist_state": 0.02,
                "journalist_independent": 0.03
            },
            cultural_notes="Strong regional identifies; legacy of 'Great Steppe' nomads."
        )
    }
    return presets.get(code, presets["uz"])

def get_default_region() -> RegionProfile:
    return get_region("uz")

