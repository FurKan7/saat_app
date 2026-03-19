"""Spec key normalization utilities."""
from typing import Dict

# Spec key normalization map (Turkish -> English, variations -> canonical)
SPEC_KEY_NORMALIZATION: Dict[str, str] = {
    # Turkish variations
    "kasa çapı": "case_diameter_mm",
    "kasa çap": "case_diameter_mm",
    "çap": "case_diameter_mm",
    "kasa kalınlığı": "case_thickness_mm",
    "kalınlık": "case_thickness_mm",
    "ağırlık": "weight_g",
    "gram": "weight_g",
    "su geçirmezlik": "water_resistance_atm",
    "su geçirmez": "water_resistance_atm",
    "cam tipi": "glass_type",
    "cam": "glass_type",
    "hareket tipi": "movement_type",
    "mekanizma": "movement_type",
    "cinsiyet": "gender",
    "lug genişliği": "lug_width_mm",
    "lug to lug": "lug_to_lug_mm",
    "lug-to-lug": "lug_to_lug_mm",
    "kronometre": "chronometer",
    "kasa rengi": "case_color",
    "kadran tipi": "dial_type",
    "arka kapak": "case_back",
    # English variations (normalize to canonical)
    "case_diameter": "case_diameter_mm",
    "diameter": "case_diameter_mm",
    "case_thickness": "case_thickness_mm",
    "thickness": "case_thickness_mm",
    "weight": "weight_g",
    "water_resistance": "water_resistance_atm",
    "wr": "water_resistance_atm",
    "glass": "glass_type",
    "crystal": "glass_type",
    "movement": "movement_type",
    "caliber": "movement_type",
    "lug_width": "lug_width_mm",
    "lug_to_lug": "lug_to_lug_mm",
}


def normalize_spec_key(key: str) -> str:
    """Normalize spec key to canonical form."""
    normalized = key.lower().strip()
    return SPEC_KEY_NORMALIZATION.get(normalized, normalized)

