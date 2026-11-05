# SonicScope
### Intelligent Audio Signal Analysis & Processing Platform

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111%2B-009688?logo=fastapi)](https://fastapi.tiangolo.com)
[![IBM watsonx.ai](https://img.shields.io/badge/IBM-watsonx.ai-054ADA?logo=ibm)](https://dataplatform.cloud.ibm.com)
[![IBM Granite](https://img.shields.io/badge/IBM%20Granite-4.0--H--Small-054ADA?logo=ibm)](https://www.ibm.com/granite)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## Introduction

**SonicScope** is a web-based platform built to help electronics students, audio engineers, and hobbyists design, analyse, and troubleshoot audio circuits. It combines core digital signal processing (DSP) theory, practical RC filter mathematics, and AI-powered engineering guidance delivered through IBM Granite — IBM's flagship open-source foundation model — running on IBM watsonx.ai.

The project was developed as part of **IBM SkillsBuild Hackathon — Problem Statement #32: Audio Signal Processing Assistant Agent**, with the goal of providing an accessible, technically accurate tool that bridges academic DSP concepts and real-world circuit engineering.

---

## Problem Statement

Audio engineers and students frequently encounter challenges such as:

- Selecting the correct filter topology and component values for a given cutoff frequency.
- Diagnosing the root cause of noise artefacts (hum, buzz, hiss, distortion, pops) in audio circuits.
- Understanding the theoretical foundations of operational amplifier circuits, preamplifiers, and signal chains.

Existing resources are scattered across datasheets, textbooks, and forums. SonicScope consolidates these into a single interactive assistant backed by an AI model that has been guided to stay within the audio electronics domain.

---

## Objectives

1. Provide an AI assistant capable of answering questions about audio electronics, signal processing, amplifiers, op-amps, and filters — powered by IBM Granite via IBM watsonx.ai.
2. Implement an accurate RC filter calculator that computes missing component values from a desired cutoff frequency and suggests standard E12 series components.
3. Deliver a structured noise troubleshooter that maps symptom descriptions to probable causes, identification steps, and practical solutions.
4. Enforce responsible AI usage: no fabricated measurements, no hardcoded secrets, clear errors when the API is unavailable.

---

## Key Features

### 1. AI Audio Engineering Assistant
- Integrates **IBM Granite 4.0-H-Small** via the IBM watsonx.ai text/chat API.
- Answers questions about amplifiers, op-amps, RC/LC/active filters, grounding, shielding, DSP algorithms, and audio signal chains.
- Explains equations and concepts accessibly while maintaining technical accuracy.
- Out-of-domain questions are politely declined with a redirect to audio topics.
- Credentials loaded exclusively from environment variables — never hardcoded.

### 2. RC Filter Calculator
- Supports **low-pass** and **high-pass** RC filter design.
- User provides a desired −3 dB cutoff frequency and either R or C; the missing component is computed.
- Returns the exact calculated value, the actual cutoff frequency, and the nearest **E12 standard capacitor** value.
- Formula: **f_c = 1 / (2π × R × C)**

### 3. Audio Noise Troubleshooter
- Accepts a free-text description of the audio problem.
- Classifies into six noise categories: Mains Hum, RF/EMI Buzz, Distortion/Clipping, Broadband Hiss, Pops/Clicks, and Oscillation/Instability.
- Returns structured output: probable causes, identification steps, and ranked solutions — all grounded in established audio engineering practice.
- Falls back to general audio troubleshooting guidance when the description does not match a known pattern.

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     SonicScope Web UI                       │
│   frontend/index.html · style.css · app.js (Vanilla JS)     │
│   ┌────────────┐  ┌──────────────────┐  ┌───────────────┐  │
│   │ AI Chat Tab│  │ RC Filter Calc   │  │ Noise Diag.   │  │
│   └─────┬──────┘  └────────┬─────────┘  └──────┬────────┘  │
└─────────┼───────────────────┼────────────────────┼──────────┘
          │  HTTP/JSON        │                    │
          ▼                   ▼                    ▼
┌─────────────────────────────────────────────────────────────┐
│              FastAPI Backend  (backend/main.py)             │
│  POST /api/ask    POST /api/filter    POST /api/noise       │
│  GET  /health     GET  /              (serves frontend)     │
│                                                             │
│  ┌─────────────────┐  ┌───────────────┐  ┌──────────────┐  │
│  │ ai_assistant.py │  │filter_calc.py │  │noise_TS.py   │  │
│  │ IBM Granite 4.0 │  │ RC math (pure │  │ Rule-based   │  │
│  │ via watsonx.ai  │  │ Python/math)  │  │ pattern match│  │
│  └────────┬────────┘  └───────────────┘  └──────────────┘  │
└───────────┼─────────────────────────────────────────────────┘
            │  HTTPS
            ▼
┌───────────────────────────────────┐
│  IBM Cloud Services               │
│  ┌──────────────────────────────┐ │
│  │ IBM IAM  (token exchange)    │ │
│  └──────────────────────────────┘ │
│  ┌──────────────────────────────┐ │
│  │ IBM watsonx.ai               │ │
│  │ Model: ibm/granite-4-h-small │ │
│  │ Endpoint: /ml/v1/text/chat   │ │
│  └──────────────────────────────┘ │
└───────────────────────────────────┘
```

---

## Technology Stack

| Layer | Technology | Purpose |
|---|---|---|
| **AI Model** | IBM Granite 4.0-H-Small (`ibm/granite-4-h-small`) | Audio Q&A via chat completions |
| **AI Platform** | IBM watsonx.ai (IBM Cloud Lite) | Model hosting and inference API |
| **IAM Auth** | IBM Cloud IAM | Short-lived bearer token exchange |
| **Backend** | Python 3.10+, FastAPI, Uvicorn | REST API, request validation, static serving |
| **HTTP Client** | httpx (async) | Async calls to IBM watsonx.ai |
| **Frontend** | HTML5, CSS3, Vanilla JavaScript | Single-page UI, no build step required |
| **Config** | python-dotenv | Credential management from `.env` |
| **Validation** | Pydantic v2 | Request/response schema enforcement |

---

## Audio Signal Processing Concepts

SonicScope incorporates the following DSP and analog electronics concepts:

### RC Filter Design
- **Transfer function:** For a first-order RC low-pass filter, `H(jω) = 1 / (1 + jωRC)`
- **Cutoff frequency (−3 dB point):** `f_c = 1 / (2π × R × C)`
- **Attenuation:** −20 dB/decade above (low-pass) or below (high-pass) the cutoff frequency
- **Phase shift:** −45° at `f_c`, approaching −90° well above cutoff (low-pass)

### Noise Analysis
- **Thermal (Johnson–Nyquist) noise:** `V_n = √(4kTRB)` — proportional to resistance, temperature, and bandwidth
- **Ground loops:** Common-mode interference from differential ground potential between equipment
- **RF/EMI pickup:** High-impedance nodes act as antennas; decoupling and shielding techniques counteract this
- **Op-amp stability:** Phase margin and gain-bandwidth product determine oscillation risk; compensation capacitors restore stability

### Signal Chain Design Principles
- Star-ground topology for minimising ground impedance
- Decoupling capacitors (100 nF ceramic + 10 µF electrolytic) at every active device power pin
- Balanced (XLR/differential) signal transmission to reject common-mode noise
- Input noise figure: placing the highest-gain stage first minimises the overall noise figure

---

## AI / ML Components

| Component | Details |
|---|---|
| **Model** | `ibm/granite-4-h-small` (Granite 4.0, 32B parameters) |
| **Model source** | IBM Research — verified available via watsonx.ai foundation model specs API |
| **Endpoint** | `https://us-south.ml.cloud.ibm.com/ml/v1/text/chat?version=2024-05-01` |
| **Auth** | IBM Cloud IAM bearer token (exchanged per request from `IBM_API_KEY`) |
| **Prompt strategy** | System prompt constrains the model to audio electronics domain; user turn passes the question verbatim |
| **Decoding** | Greedy decoding, max 800 new tokens, repetition penalty 1.1 |
| **Guardrails** | Off-domain questions are rejected in the system prompt; API errors surface as HTTP 503 with a human-readable message |

---

## Prerequisites

- **Python 3.10 or newer** — [python.org](https://python.org)
- **IBM Cloud Lite account** — [register free](https://cloud.ibm.com/registration)
- **IBM watsonx.ai project** — [create at dataplatform.cloud.ibm.com](https://dataplatform.cloud.ibm.com/)

---

## Installation

```powershell
# Clone the repository
git clone https://github.com/ManikandanPrabhu13/sonicscope-audio-signal-processing.git
cd sonicscope-audio-signal-processing

# Create and activate a virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

---

## IBM Credentials Setup

### Step 1 — IBM Cloud API Key
1. Log in to [IBM Cloud](https://cloud.ibm.com).
2. Go to **Manage → Access (IAM) → API keys**.
3. Click **Create an IBM Cloud API key** — copy the key immediately (shown only once).

### Step 2 — watsonx.ai Project ID
1. Open [IBM watsonx.ai](https://dataplatform.cloud.ibm.com/).
2. Open your project → **Manage** tab → copy the **Project ID** (UUID).

### Step 3 — Configure `.env`
Edit the `.env` file in the project root:

```env
IBM_API_KEY=your_ibm_cloud_api_key_here
IBM_PROJECT_ID=your_watsonx_project_id_here
```

> ⚠️ `.env` is listed in `.gitignore` and must **never** be committed to version control.

---

## Running the Application

```powershell
# Activate the virtual environment first
.\venv\Scripts\Activate.ps1

# Start the backend (from project root)
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Open your browser at **[http://localhost:8000](http://localhost:8000)**

Interactive API documentation: **[http://localhost:8000/docs](http://localhost:8000/docs)**

---

## Example Usage

### AI Assistant — via browser
Navigate to the **AI Assistant** tab and ask:
> *"Why is my audio amplifier producing a 50 Hz hum?"*

The assistant will explain ground loop mechanisms, common-mode interference, and provide grounding and isolation solutions, drawing on IBM Granite's knowledge.

### RC Filter Calculator — API
```bash
curl -X POST http://localhost:8000/api/filter \
  -H "Content-Type: application/json" \
  -d '{"filter_type":"low_pass","cutoff_frequency":1000,"resistance":10000}'
```
```json
{
  "filter_type": "Low-Pass",
  "cutoff_frequency_hz": 1000.0,
  "actual_cutoff_frequency_hz": 1000.0,
  "resistance_ohms": 10000.0,
  "capacitance_uf": 0.015915,
  "standard_capacitance_uf": 0.015,
  "formula": "fc = 1 / (2π × R × C)",
  "explanation": "This Low-Pass RC filter has a −3 dB cutoff of 1000 Hz..."
}
```

### Noise Troubleshooter — API
```bash
curl -X POST http://localhost:8000/api/noise \
  -H "Content-Type: application/json" \
  -d '{"description":"constant 50Hz hum that gets louder when I plug in a second device"}'
```
Returns: noise type (`Mains Hum`), 5 possible causes, 4 identification steps, 6 solutions.

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Serves the SonicScope web UI |
| `GET` | `/health` | Health check — reports credential config status |
| `POST` | `/api/ask` | AI Q&A — body: `{"question": "..."}` |
| `POST` | `/api/filter` | RC filter calc — body: `{"filter_type","cutoff_frequency","resistance"/"capacitance"}` |
| `POST` | `/api/noise` | Noise diagnosis — body: `{"description": "..."}` |

---

## Project Structure

```
sonicscope-audio-signal-processing/
├── backend/
│   ├── main.py                  # FastAPI application, routes, CORS, static serving
│   ├── ai_assistant.py          # IBM Granite via watsonx.ai (IAM + chat completions)
│   ├── filter_calculator.py     # RC filter mathematics, E12 component lookup
│   └── noise_troubleshooter.py  # Rule-based noise diagnosis (6 categories)
├── frontend/
│   ├── index.html               # Single-page UI — 3 tabs
│   ├── style.css                # IBM Carbon-inspired design system
│   └── app.js                   # Fetch API calls, chat renderer, form handling
├── .env                         # ← Credentials (never committed)
├── .gitignore
├── requirements.txt
└── README.md
```

---

## Future Improvements

The following enhancements would extend SonicScope's capabilities meaningfully:

1. **Multi-order filter design** — Butterworth, Chebyshev, Bessel filter topologies with Sallen-Key op-amp implementations.
2. **Bode plot visualisation** — render gain and phase vs. frequency curves for designed filters using an SVG/Canvas chart.
3. **Conversation history** — maintain multi-turn chat context across the session for follow-up questions.
4. **Op-amp selection tool** — given signal bandwidth, supply voltage, and noise requirements, suggest matching op-amp ICs.
5. **Audio FFT demo** — allow users to upload a WAV file and visualise its frequency spectrum (browser-side Web Audio API).
6. **Expanded noise database** — add impedance mismatch, digital clock interference, and thermocouple noise patterns to the troubleshooter.
7. **IBM watsonx.ai fine-tuning** — fine-tune Granite on audio engineering literature for deeper domain accuracy.

---

## Guardrails & Security

- IBM credentials are **never hardcoded** — loaded exclusively from `.env` via `python-dotenv`.
- IBM Granite responses are **never fabricated** — if the API is unavailable a clear HTTP 503 error is returned.
- No circuit measurements are invented or claimed to be simulated.
- All inputs are validated by Pydantic v2 before processing.
- `.env` is listed in `.gitignore` — will never be committed.

---

## Acknowledgements

- **IBM Research** — for the IBM Granite open-source foundation model series.
- **IBM SkillsBuild** — for Problem Statement #32 defining the audio assistant challenge.
- **IBM watsonx.ai** — cloud infrastructure for model inference.

---

*SonicScope — IBM SkillsBuild Hackathon, Problem Statement #32.*
