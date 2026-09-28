"""
Expands a panel outline into a full comic-style story with narration and
character dialogue, using Google's Gemini Pro model.
"""

import google.generativeai as genai

from app.config import GEMINI_API_KEY, GEMINI_PRO_MODEL

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)


def _fallback_story(outline: list) -> str:
    """Deterministic narration used when no GEMINI_API_KEY is configured."""
    parts = []
    for item in outline:
        if isinstance(item, dict):
            title = item.get("title", "Untitled panel")
            scene = item.get("scene_description", "")
        else:
            title = "Panel"
            scene = str(item)
        parts.append(
            f"**Panel: {title}**\n"
            f"CAPTION: {scene}\n"
            f"NARRATION: The story continues, panel by panel, building toward "
            f"its conclusion.\n"
        )
    return "\n".join(parts)


def generate_story(outline: list) -> str:
    """
    Generates a detailed comic story with narration and character dialogue
    from a list of comic panel outlines using Gemini Pro.

    Args:
        outline (list): A list of dicts/strings representing each comic
            panel's idea.

    Returns:
        str: The generated comic story text, or an error message.
    """
    if not GEMINI_API_KEY:
        return _fallback_story(outline)

    # Format the panel outline as a numbered list for clarity
    formatted_outline = "\n".join(
        [f"{i + 1}. {item}" for i, item in enumerate(outline)]
    )

    prompt = f"""
You're a comic book writer.

Given the following panel breakdown, write a comic-style story with engaging narration and character dialogues for each panel.

Panel Outline:
{formatted_outline}

Guidelines:
- Use a fun and engaging tone, like an actual comic book.
- Include narration and clearly marked character lines.
- Keep each panel self-contained but part of a cohesive story.
- Start each panel's block with the exact line "**Panel {{n}}: <title>**" so it can be parsed reliably.
"""

    try:
        model = genai.GenerativeModel(GEMINI_PRO_MODEL)
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error generating story: {str(e)}"