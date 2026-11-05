"""
SonicScope – Intelligent Audio Signal Analysis & Processing Platform
FastAPI Backend Entry Point
IBM SkillsBuild Problem Statement #32
"""

import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from typing import Optional
from dotenv import load_dotenv

from ai_assistant import get_ai_response
from filter_calculator import calculate_rc_filter
from noise_troubleshooter import diagnose_noise

load_dotenv()

app = FastAPI(
    title="SonicScope",
    description="Intelligent Audio Signal Analysis & Processing Platform powered by IBM Granite",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Request / Response Models ────────────────────────────────────────────────

class AIQueryRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=2000,
                          description="Audio engineering question")

class AIQueryResponse(BaseModel):
    answer: str
    model_used: str

class FilterRequest(BaseModel):
    filter_type: str = Field(..., description="'low_pass' or 'high_pass'")
    cutoff_frequency: float = Field(..., gt=0, description="Desired cutoff frequency in Hz")
    resistance: Optional[float] = Field(None, gt=0, description="Resistance in Ohms (omit to calculate)")
    capacitance: Optional[float] = Field(None, gt=0, description="Capacitance in Farads (omit to calculate)")

class FilterResponse(BaseModel):
    filter_type: str
    cutoff_frequency_hz: float
    actual_cutoff_frequency_hz: float
    resistance_ohms: float
    capacitance_farads: float
    capacitance_uf: float
    standard_capacitance_uf: float
    formula: str
    explanation: str

class NoiseRequest(BaseModel):
    description: str = Field(..., min_length=5, max_length=1000,
                             description="Describe the audio noise problem")

class NoiseResponse(BaseModel):
    noise_type: str
    possible_causes: list[str]
    identification_steps: list[str]
    solutions: list[str]
    summary: str


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/", include_in_schema=False)
async def root():
    """Serve the frontend index page."""
    frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend", "index.html")
    if os.path.exists(frontend_path):
        return FileResponse(frontend_path)
    return {"message": "AudioSense AI backend is running. Frontend not found."}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "ok",
        "service": "AudioSense AI",
        "ibm_project_id_configured": bool(os.getenv("IBM_PROJECT_ID")),
        "ibm_api_key_configured": bool(os.getenv("IBM_API_KEY")),
    }


@app.post("/api/ask", response_model=AIQueryResponse)
async def ask_ai(request: AIQueryRequest):
    """
    Send an audio engineering question to IBM Granite via watsonx.ai.
    """
    try:
        answer, model_used = await get_ai_response(request.question)
        return AIQueryResponse(answer=answer, model_used=model_used)
    except ValueError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"AI service error: {str(exc)}") from exc


@app.post("/api/filter", response_model=FilterResponse)
async def filter_calc(request: FilterRequest):
    """
    Calculate RC filter component values.
    Provide cutoff_frequency and exactly ONE of resistance or capacitance.
    """
    if request.resistance is None and request.capacitance is None:
        raise HTTPException(
            status_code=422,
            detail="Provide at least one of 'resistance' or 'capacitance'."
        )
    if request.filter_type not in ("low_pass", "high_pass"):
        raise HTTPException(
            status_code=422,
            detail="filter_type must be 'low_pass' or 'high_pass'."
        )
    try:
        result = calculate_rc_filter(
            filter_type=request.filter_type,
            cutoff_frequency=request.cutoff_frequency,
            resistance=request.resistance,
            capacitance=request.capacitance,
        )
        return FilterResponse(**result)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post("/api/noise", response_model=NoiseResponse)
async def noise_diagnosis(request: NoiseRequest):
    """
    Diagnose audio noise problems based on a user's description.
    """
    try:
        result = diagnose_noise(request.description)
        return NoiseResponse(**result)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Diagnosis error: {str(exc)}") from exc


# ── Static files (frontend) ──────────────────────────────────────────────────
frontend_dir = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.isdir(frontend_dir):
    app.mount("/static", StaticFiles(directory=frontend_dir), name="static")
