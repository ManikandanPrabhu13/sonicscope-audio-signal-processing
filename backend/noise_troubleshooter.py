"""
noise_troubleshooter.py
Rule-based audio noise diagnostics for AudioSense AI.

Maps noise descriptions to structured diagnosis results.
No fabricated measurements or simulations — all advice is
based on well-established audio engineering practice.
"""

import re
from typing import Dict, Any, List

# ── Noise pattern database ────────────────────────────────────────────────────

NOISE_PATTERNS = [
    {
        "keywords": ["hum", "50hz", "60hz", "mains", "power supply", "power-supply", "ac hum"],
        "noise_type": "Mains Hum (50/60 Hz)",
        "possible_causes": [
            "Ground loop between audio equipment and power supply",
            "Inadequate shielding on audio cables",
            "Single-point grounding not implemented",
            "Switching power supply radiating interference into audio path",
            "Unbalanced connections picking up common-mode noise",
        ],
        "identification_steps": [
            "Disconnect one device at a time and listen — the hum disappears when the offending device is unplugged.",
            "Measure the signal with an oscilloscope; 50 Hz or 60 Hz hum shows a clean sine wave superimposed.",
            "Lift the ground on one device temporarily (use a ground-lift adapter) to confirm a ground loop.",
            "Check if the hum changes pitch between 50 Hz and 60 Hz depending on the power grid.",
        ],
        "solutions": [
            "Use a ground loop isolator on RCA/TRS connections.",
            "Run all equipment from the same power strip/outlet to create a single ground reference.",
            "Replace unbalanced (RCA) cables with balanced (XLR) connections where possible.",
            "Use a linear power supply instead of a switching power supply for sensitive preamp stages.",
            "Add a 100 Ω resistor in series with the shield at one end of the cable to break the ground loop.",
            "Implement a star-ground topology in the PCB layout.",
        ],
    },
    {
        "keywords": ["buzz", "buzzing", "rf", "radio", "interference", "emi", "rfi"],
        "noise_type": "Buzzing / RF/EMI Interference",
        "possible_causes": [
            "Radio-frequency interference (RFI) from nearby wireless devices or switching regulators",
            "Inadequate decoupling capacitors on op-amp power rails",
            "Long unshielded cable acting as an antenna",
            "High-impedance input node exposed to EMI",
            "Missing ferrite bead on power supply line",
        ],
        "identification_steps": [
            "Move the device away from Wi-Fi routers, mobile phones, and fluorescent lights.",
            "Probe the power rails with an oscilloscope — look for high-frequency spikes at the switching frequency.",
            "Wrap the signal cable in aluminium foil temporarily; if buzzing reduces, shielding is the issue.",
            "Check if the buzz correlates with mobile phone activity (GSM buzz is a distinctive pattern).",
        ],
        "solutions": [
            "Add 100 nF ceramic capacitors close to each op-amp's VCC and GND pins.",
            "Add a ferrite bead (e.g., BLM18) in series with the power supply line to the audio stage.",
            "Use shielded twisted-pair (STP) or coaxial cable for all signal paths.",
            "Keep signal cables away from power cables — cross them at 90° if they must cross.",
            "Add a low-pass RC filter (e.g., 10 Ω + 100 nF) on the power rail to the preamp.",
            "Use a metal enclosure and connect the chassis to the audio circuit ground at a single point.",
        ],
    },
    {
        "keywords": ["distortion", "clipping", "saturate", "saturation", "overdrive", "harmonic"],
        "noise_type": "Distortion / Clipping",
        "possible_causes": [
            "Input signal amplitude exceeds op-amp output swing (clipping)",
            "Insufficient supply voltage for the required output swing",
            "Op-amp slew rate too low for the signal frequency",
            "Incorrect gain setting causing the amplifier to clip",
            "Non-linearity in the feedback network components",
        ],
        "identification_steps": [
            "View the output on an oscilloscope — clipping appears as a flattened sine wave top/bottom.",
            "Reduce the input level; if distortion disappears the gain is too high or the supply too low.",
            "Check Total Harmonic Distortion (THD) with a spectrum analyser — clipping produces strong odd harmonics.",
            "Verify supply voltage reaches the op-amp pins with a multimeter.",
        ],
        "solutions": [
            "Reduce the input signal level or lower the amplifier gain.",
            "Increase the supply voltage to give more headroom (e.g., ±12 V instead of ±5 V).",
            "Choose an op-amp with a higher slew rate for high-frequency signals (e.g., NE5534, OPA2134).",
            "Add an input attenuator (voltage divider) before the amplifier stage.",
            "Use a rail-to-rail output op-amp if the supply cannot be increased.",
            "Check all resistors in the feedback network for correct values and tolerances.",
        ],
    },
    {
        "keywords": ["hiss", "white noise", "thermal noise", "shot noise", "high frequency noise", "sss"],
        "noise_type": "Broadband Hiss / Thermal Noise",
        "possible_causes": [
            "High-value resistors in the signal path generating thermal (Johnson) noise",
            "High-noise op-amp used in a low-noise application",
            "Insufficient gain early in the signal chain (poor noise figure)",
            "Long cable runs increasing resistance and noise pickup",
            "Input stage transistor/op-amp with high input noise voltage",
        ],
        "identification_steps": [
            "Short the input to ground — if hiss disappears the noise source is external; if it remains, it is internal.",
            "Calculate expected thermal noise: Vnoise = √(4kTRB), where k = 1.38×10⁻²³ J/K, T = temperature, R = resistance, B = bandwidth.",
            "Measure noise floor with a spectrum analyser — thermal noise appears as a flat baseline.",
            "Swap the op-amp for a known low-noise type and compare.",
        ],
        "solutions": [
            "Replace high-value resistors (> 10 kΩ) with lower values in the signal path where possible.",
            "Use a low-noise op-amp such as LT1028, AD797, or OPA1612.",
            "Apply a bandwidth-limiting low-pass filter after the gain stage to cut out-of-band noise.",
            "Place the highest-gain stage first in the signal chain to improve the noise figure.",
            "Cool resistors or use metal-film resistors which have lower excess noise than carbon-film types.",
        ],
    },
    {
        "keywords": ["pop", "click", "transient", "switch", "turn on", "turn-on", "relay"],
        "noise_type": "Pops and Clicks (Transient Noise)",
        "possible_causes": [
            "DC offset at power-on causing a loud thump through the speaker",
            "Capacitor charging transient when the circuit powers up",
            "Relay switching transient not suppressed",
            "Digital control signals coupling into the analog audio path",
            "Input not muted during power-on/off sequence",
        ],
        "identification_steps": [
            "Measure DC voltage at the amplifier output at power-on with a multimeter.",
            "Use an oscilloscope to capture the transient — check its amplitude and duration.",
            "Check if the pop occurs at power-on, power-off, or both.",
            "Identify if the pop is from the amplifier output or the power supply rail.",
        ],
        "solutions": [
            "Add a muting relay that shorts the speaker output for ~1–2 seconds after power-on.",
            "Use a DC-blocking capacitor (e.g., 100 µF–1000 µF) at the output to block DC offset.",
            "Slow down the power-on ramp with an RC time constant on the supply rail.",
            "Add a soft-start circuit or use an IC with built-in pop suppression.",
            "Ensure op-amp inputs have defined DC bias paths (pull-down resistors on unconnected inputs).",
        ],
    },
    {
        "keywords": ["oscillation", "oscillating", "squeal", "squealing", "feedback", "instability", "ringing"],
        "noise_type": "Oscillation / Instability",
        "possible_causes": [
            "Insufficient phase margin in the op-amp feedback network",
            "Capacitive load on the op-amp output (driving a cable or capacitor directly)",
            "Power supply decoupling capacitors missing or too far from the IC",
            "Feedback resistor values too high causing parasitic capacitance effects",
            "PCB layout with long feedback traces creating inductive loops",
        ],
        "identification_steps": [
            "View the output on an oscilloscope — oscillation appears as a sustained high-frequency waveform.",
            "Remove the load and check if oscillation stops (capacitive load issue).",
            "Measure the oscillation frequency — it typically matches the op-amp's gain-bandwidth product.",
            "Check if oscillation appears on the power supply rail (decoupling issue).",
        ],
        "solutions": [
            "Add a small series resistor (10–100 Ω) between the op-amp output and the load/cable.",
            "Place a small capacitor (10–100 pF) in the feedback path to add a compensation pole.",
            "Add 100 nF ceramic decoupling capacitors directly at each op-amp power pin.",
            "Reduce feedback resistor values to minimise the effect of parasitic capacitance.",
            "Improve PCB layout: keep feedback traces short and away from input traces.",
            "Choose an op-amp designed for capacitive load driving (e.g., OPA2134, LM833).",
        ],
    },
]

# Default fallback when no pattern matches
DEFAULT_DIAGNOSIS = {
    "noise_type": "Unidentified Audio Problem",
    "possible_causes": [
        "Grounding issue or ground loop in the audio chain",
        "Poor quality or damaged cables",
        "Component failure (capacitor, resistor, or active device)",
        "Power supply noise coupling into the signal path",
        "Impedance mismatch between source and load",
    ],
    "identification_steps": [
        "Isolate the signal chain: disconnect sections one at a time until the problem disappears.",
        "Use an oscilloscope to examine the signal at each stage.",
        "Check all supply voltages and ground connections.",
        "Inspect components for visible damage, cold solder joints, or oxidation.",
        "Try known-good cables to rule out cable issues.",
    ],
    "solutions": [
        "Add proper decoupling capacitors (100 nF ceramic + 10 µF electrolytic) on all power rails.",
        "Check and tighten all ground connections.",
        "Replace suspect capacitors (electrolytic caps degrade over time).",
        "Review the circuit against the original schematic.",
        "Consult the component datasheets for recommended application circuits.",
    ],
    "summary": (
        "Could not identify a specific noise type from the description. "
        "General audio troubleshooting steps are provided above. "
        "For more targeted help, describe the noise more specifically "
        "(e.g., hum, hiss, buzz, distortion, pop) and when it occurs."
    ),
}


def diagnose_noise(description: str) -> Dict[str, Any]:
    """
    Analyse a noise description and return a structured diagnosis.

    Uses keyword matching against known noise patterns.
    Falls back to general guidance if no pattern matches.
    """
    desc_lower = description.lower()
    # Normalise common punctuation
    desc_lower = re.sub(r"[^\w\s]", " ", desc_lower)

    best_match = None
    best_score = 0

    for pattern in NOISE_PATTERNS:
        score = sum(1 for kw in pattern["keywords"] if kw in desc_lower)
        if score > best_score:
            best_score = score
            best_match = pattern

    if best_match and best_score > 0:
        result = {
            "noise_type": best_match["noise_type"],
            "possible_causes": best_match["possible_causes"],
            "identification_steps": best_match["identification_steps"],
            "solutions": best_match["solutions"],
            "summary": (
                f"Based on your description, this appears to be "
                f"'{best_match['noise_type']}'. "
                f"Review the {len(best_match['possible_causes'])} possible causes and "
                f"{len(best_match['solutions'])} solutions listed above. "
                f"Start with identification steps to confirm the root cause before applying fixes."
            ),
        }
    else:
        result = DEFAULT_DIAGNOSIS.copy()

    return result
