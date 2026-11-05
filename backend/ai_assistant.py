"""
ai_assistant.py – SonicScope
Handles communication with IBM Granite model via IBM watsonx.ai API.
Credentials are loaded from environment variables — never hardcoded.
"""

import os
import httpx
from typing import Tuple

# IBM watsonx.ai endpoints
IAM_TOKEN_URL = "https://iam.cloud.ibm.com/identity/token"
# granite-4-h-small exposes the chat completions endpoint
WATSONX_CHAT_URL = "https://us-south.ml.cloud.ibm.com/ml/v1/text/chat?version=2024-05-01"

# IBM Granite model identifier — verified via live API 2026-11-05
# ibm/granite-4-h-small: status=available, functions=[text_chat, text_generation, autoai_rag]
GRANITE_MODEL_ID = "ibm/granite-4-h-small"

# System prompt — keeps the model focused on audio engineering
SYSTEM_PROMPT = (
    "You are SonicScope AI, an expert audio electronics engineer and educator. "
    "You specialise in audio circuit design, signal processing, op-amp circuits, "
    "amplifiers, filters (low-pass, high-pass, band-pass, notch), preamplifiers, "
    "grounding techniques, noise elimination, and audio DSP concepts. "
    "When answering, provide clear explanations, relevant equations where helpful, "
    "and practical, actionable advice. "
    "If a question is unrelated to audio electronics or signal processing, "
    "politely decline and redirect the user to audio-related topics. "
    "Use technical terminology accurately but explain it accessibly."
)


async def _get_iam_token(api_key: str) -> str:
    """Exchange an IBM Cloud API key for a short-lived IAM bearer token."""
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            IAM_TOKEN_URL,
            data={
                "grant_type": "urn:ibm:params:oauth:grant-type:apikey",
                "apikey": api_key,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
    if response.status_code != 200:
        raise ValueError(
            f"IBM IAM token request failed (HTTP {response.status_code}): {response.text}"
        )
    token_data = response.json()
    return token_data["access_token"]


async def get_ai_response(question: str) -> Tuple[str, str]:
    """
    Send a question to IBM Granite via watsonx.ai and return (answer, model_id).

    Raises:
        ValueError: If credentials are missing or the API call fails.
    """
    api_key = os.getenv("IBM_API_KEY")
    project_id = os.getenv("IBM_PROJECT_ID")

    if not api_key:
        raise ValueError(
            "IBM_API_KEY environment variable is not set. "
            "Please configure your IBM Cloud API key in the .env file."
        )
    if not project_id:
        raise ValueError(
            "IBM_PROJECT_ID environment variable is not set. "
            "Please configure your IBM watsonx.ai project ID in the .env file."
        )

    # Get IAM token
    iam_token = await _get_iam_token(api_key)

    # granite-4-h-small uses the OpenAI-compatible chat completions format
    payload = {
        "model_id": GRANITE_MODEL_ID,
        "project_id": project_id,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": question},
        ],
        "parameters": {
            "decoding_method": "greedy",
            "max_new_tokens": 800,
            "min_new_tokens": 30,
            "repetition_penalty": 1.1,
        },
    }

    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(
            WATSONX_CHAT_URL,
            json=payload,
            headers={
                "Authorization": f"Bearer {iam_token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
        )

    if response.status_code != 200:
        raise ValueError(
            f"IBM watsonx.ai API error (HTTP {response.status_code}): {response.text}"
        )

    data = response.json()

    # Extract assistant reply from chat completions response
    try:
        generated_text = data["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError) as exc:
        raise ValueError(
            f"Unexpected response format from watsonx.ai: {data}"
        ) from exc

    if not generated_text:
        raise ValueError("IBM Granite returned an empty response.")

    return generated_text, GRANITE_MODEL_ID
