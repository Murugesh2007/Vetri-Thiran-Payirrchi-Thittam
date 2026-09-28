"""
Generates a structured 5-panel comic outline from a user's story prompt,
using Google's Gemini Flash model.
"""

import json
import re
from typing import List, Dict

import google.generativeai as genai

from app.config import GEMINI_API_KEY, GEMINI_FLASH_MODEL

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)


def _extract_json_array(text: str) -> str:
    """Strip markdown code fences and pull out the JSON array if the model
    wrapped it in extra prose."""
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(json)?", "", text).strip()
        text = re.sub(r"```$", "", text).strip()

    start = text.find("[")
    end = text.rfind("]")
    if start != -1 and end != -1 and end > start:
        return text[start : end + 1]
    return text


def _fallback_outline(user_prompt: str) -> List[Dict]:
    """A deterministic 5-panel outline used when no GEMINI_API_KEY is
    configured, so the rest of the pipeline can still be exercised."""
    beats = [
        ("The Setup", "We meet our hero and the world they live in."),
        ("The Call", "Something disrupts the ordinary and sets the story moving."),
        ("Rising Action", "Our hero faces the first real obstacle."),
        ("The Turn", "A twist changes everything."),
        ("Resolution", "The story reaches its conclusion."),
    ]
    panels = []
    for i, (title, desc) in enumerate(beats, start=1):
        panels.append(
            {
                "panel": i,
                "title": title,
                "scene_description": f"{desc} Based on the idea: {user_prompt}",
                "image_prompt": f"Comic book panel illustration, {desc.lower()} "
                f"related to: {user_prompt}, dynamic composition, detailed",
            }
        )
    return panels


def generate_outline(user_prompt: str) -> list:
    """
    Generates a 5-panel comic layout based on the user's story idea using
    Gemini.

    Args:
        user_prompt (str): The user's comic idea prompt.

    Returns:
        list: A list of dictionaries, one for each panel. On any failure,
        returns a list containing a single {"error": ...} dict, EXCEPT
        when no API key is configured at all, in which case a deterministic
        local fallback outline is returned so the pipeline keeps working.
    """
    if not GEMINI_API_KEY:
        return _fallback_outline(user_prompt)

    prompt = f"""
You are a professional AI comic planner.

Your task is to generate a *strictly formatted* JSON array containing 5 panel descriptions for a comic based on the story idea below:

STORY: "{user_prompt}"

Each JSON object must include:
- "panel" (integer)
- "title" (string)
- "scene_description" (string)
- "image_prompt" (string)

Respond ONLY in this valid JSON format, without any explanations or markdown:
[
  {{
    "panel": 1,
    "title": "Title here",
    "scene_description": "Scene description here",
    "image_prompt": "Image prompt for Stable Diffusion"
  }},
  ...
]
"""

    try:
        model = genai.GenerativeModel(GEMINI_FLASH_MODEL)
        response = model.generate_content(prompt)
        output_text = response.text.strip()

        print("\n🔹 RAW GEMINI RESPONSE 🔹\n", output_text)

        output_text = _extract_json_array(output_text)
        panel_data = json.loads(output_text)

        if not isinstance(panel_data, list):
            raise ValueError("Gemini response is not a list.")

        for panel in panel_data:
            if not isinstance(panel, dict) or not all(
                key in panel for key in ("panel", "title", "scene_description", "image_prompt")
            ):
                raise ValueError(f"Invalid panel format or missing keys: {panel}")

        return panel_data

    except json.JSONDecodeError as e:
        print("❌ JSON Decode Error:", e)
        return [{"error": f"JSON parsing failed: {str(e)}"}]

    except Exception as e:
        print("❌ Unexpected Error:", e)
        return [{"error": f"Generation failed: {str(e)}"}]