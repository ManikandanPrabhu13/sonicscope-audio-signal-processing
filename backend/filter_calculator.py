"""
filter_calculator.py
RC filter calculations for AudioSense AI.
Supports low-pass and high-pass RC filters.

Formula:  fc = 1 / (2 * pi * R * C)
"""

import math
from typing import Optional, Dict, Any

# Standard E12 capacitor series values in µF
E12_CAPACITORS_UF = [
    0.001, 0.0012, 0.0015, 0.0018, 0.0022, 0.0027, 0.0033, 0.0039, 0.0047, 0.0056, 0.0068, 0.0082,
    0.01, 0.012, 0.015, 0.018, 0.022, 0.027, 0.033, 0.039, 0.047, 0.056, 0.068, 0.082,
    0.1, 0.12, 0.15, 0.18, 0.22, 0.27, 0.33, 0.39, 0.47, 0.56, 0.68, 0.82,
    1.0, 1.2, 1.5, 1.8, 2.2, 2.7, 3.3, 3.9, 4.7, 5.6, 6.8, 8.2,
    10.0, 12.0, 15.0, 18.0, 22.0, 27.0, 33.0, 47.0, 100.0, 220.0, 470.0, 1000.0,
]


def _nearest_standard_capacitor(capacitance_uf: float) -> float:
    """Return the nearest E12 series capacitor value in µF."""
    return min(E12_CAPACITORS_UF, key=lambda c: abs(c - capacitance_uf))


def calculate_rc_filter(
    filter_type: str,
    cutoff_frequency: float,
    resistance: Optional[float] = None,
    capacitance: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Calculate the missing RC filter component.

    Exactly one of resistance or capacitance must be provided.
    Returns a dict with all component values and explanatory text.

    Raises:
        ValueError: on invalid inputs.
    """
    if filter_type not in ("low_pass", "high_pass"):
        raise ValueError("filter_type must be 'low_pass' or 'high_pass'.")
    if cutoff_frequency <= 0:
        raise ValueError("cutoff_frequency must be a positive number in Hz.")

    if resistance is not None and capacitance is not None:
        # Both provided — calculate actual cutoff frequency from them
        R = resistance
        C = capacitance
        actual_fc = 1.0 / (2.0 * math.pi * R * C)
    elif resistance is not None:
        R = resistance
        if R <= 0:
            raise ValueError("Resistance must be positive.")
        # C = 1 / (2π * fc * R)
        C = 1.0 / (2.0 * math.pi * cutoff_frequency * R)
        actual_fc = cutoff_frequency
    elif capacitance is not None:
        C = capacitance
        if C <= 0:
            raise ValueError("Capacitance must be positive.")
        # R = 1 / (2π * fc * C)
        R = 1.0 / (2.0 * math.pi * cutoff_frequency * C)
        actual_fc = cutoff_frequency
    else:
        raise ValueError("Provide at least one of 'resistance' or 'capacitance'.")

    capacitance_uf = C * 1e6
    standard_cap_uf = _nearest_standard_capacitor(capacitance_uf)

    # Recalculate fc using standard capacitor
    actual_fc_with_standard = 1.0 / (2.0 * math.pi * R * (standard_cap_uf * 1e-6))

    filter_label = "Low-Pass" if filter_type == "low_pass" else "High-Pass"
    formula = "fc = 1 / (2π × R × C)"

    explanation = (
        f"This {filter_label} RC filter has a −3 dB cutoff frequency of "
        f"{actual_fc:.2f} Hz. "
        f"With R = {_format_resistance(R)} and C = {capacitance_uf:.4g} µF "
        f"({_format_resistance(R)} × {capacitance_uf:.4g} µF), "
        f"signals {'below' if filter_type == 'low_pass' else 'above'} {actual_fc:.2f} Hz "
        f"pass through with minimal attenuation. "
        f"The nearest standard E12 capacitor is {standard_cap_uf} µF, which gives "
        f"an actual cutoff of {actual_fc_with_standard:.2f} Hz."
    )

    return {
        "filter_type": filter_label,
        "cutoff_frequency_hz": round(cutoff_frequency, 4),
        "actual_cutoff_frequency_hz": round(actual_fc, 4),
        "resistance_ohms": round(R, 6),
        "capacitance_farads": round(C, 12),
        "capacitance_uf": round(capacitance_uf, 6),
        "standard_capacitance_uf": standard_cap_uf,
        "formula": formula,
        "explanation": explanation,
    }


def _format_resistance(ohms: float) -> str:
    """Format resistance with k/M suffix for readability."""
    if ohms >= 1_000_000:
        return f"{ohms / 1_000_000:.4g} MΩ"
    if ohms >= 1_000:
        return f"{ohms / 1_000:.4g} kΩ"
    return f"{ohms:.4g} Ω"
