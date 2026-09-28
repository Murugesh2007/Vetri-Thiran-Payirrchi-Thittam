"""
All FastAPI routes for ComicCraft.
"""

import traceback

from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from app.config import TEMPLATES_DIR, PANELS_DIR, to_web_path
from app.gemini_flash import generate_outline
from app.gemini_pro import generate_story
from app.image_generator import generate_image
from app.layout_builder import build_comic_layout
from app.exporters import save_pdf


router = APIRouter()

templates = Jinja2Templates(
    directory=str(TEMPLATES_DIR)
)


class PromptRequest(BaseModel):
    prompt: str
    character_name: str = ""
    setting: str = ""
    tone: str = ""
    style: str = ""


def _run_comic_pipeline(full_prompt: str) -> dict:
    # ---------------------------------------------
    # STEP 1: Generate panel outline
    # ---------------------------------------------

    outline = generate_outline(full_prompt)

    if not isinstance(outline, list):
        raise ValueError(
            "Gemini did not return a valid panel list."
        )

    if not outline:
        raise ValueError(
            "Gemini returned an empty panel list."
        )

    if (
        isinstance(outline[0], dict)
        and "error" in outline[0]
    ):
        raise ValueError(
            outline[0]["error"]
        )

    # ---------------------------------------------
    # STEP 2: Generate story
    # ---------------------------------------------

    full_story = generate_story(outline)

    # ---------------------------------------------
    # STEP 3: Generate images
    # ---------------------------------------------

    image_paths = []

    for index, panel in enumerate(
        outline,
        start=1
    ):

        if not isinstance(panel, dict):
            continue

        image_prompt = panel.get(
            "image_prompt",
            ""
        )

        if not image_prompt:
            image_prompt = panel.get(
                "prompt",
                ""
            )

        if not image_prompt:
            image_prompt = (
                f"Comic panel {index}, "
                f"based on the story: {full_prompt}"
            )

        image_path = generate_image(
            image_prompt,
            filename=f"panel_{index}.png"
        )

        image_paths.append(
            image_path
        )

    if not image_paths:
        raise ValueError(
            "No panel images were generated."
        )

    # ---------------------------------------------
    # STEP 4: Build comic page image
    # ---------------------------------------------

    comic_file = PANELS_DIR / "comic_page.png"

    build_comic_layout(
        image_paths,
        output_path=comic_file,
        title="ComicCraft"
    )

    # ---------------------------------------------
    # STEP 5: Create PDF layout list
    # ---------------------------------------------

    layout = []

    for index, panel in enumerate(
        outline
    ):

        if index >= len(image_paths):
            continue

        image_path = image_paths[index]

        title = panel.get(
            "title",
            f"Panel {index + 1}"
        )

        story_text = ""

        if isinstance(
            full_story,
            list
        ):

            if index < len(
                full_story
            ):

                story_item = full_story[
                    index
                ]

                if isinstance(
                    story_item,
                    dict
                ):

                    story_text = (
                        story_item.get(
                            "text"
                        )
                        or story_item.get(
                            "caption"
                        )
                        or story_item.get(
                            "dialogue"
                        )
                        or ""
                    )

                else:

                    story_text = str(
                        story_item
                    )

        elif isinstance(
            full_story,
            dict
        ):

            story_text = (
                full_story.get(
                    str(index + 1)
                )
                or full_story.get(
                    f"panel_{index + 1}"
                )
                or ""
            )

        else:

            story_text = str(
                full_story
            )

        layout.append(
            {
                "panel": index + 1,
                "title": title,
                "image_path": image_path,
                "image_url": to_web_path(
                    image_path
                ),
                "text": story_text,
            }
        )

    # ---------------------------------------------
    # STEP 6: Create PDF
    # ---------------------------------------------

    pdf_path = save_pdf(
        layout
    )

    # ---------------------------------------------
    # STEP 7: Return result
    # ---------------------------------------------

    return {
        "layout": layout,
        "comic_path": to_web_path(
            comic_file
        ),
        "pdf_path": to_web_path(
            pdf_path
        ),
        "story": full_story,
    }


# -------------------------------------------------
# HOME PAGE
# -------------------------------------------------

@router.get(
    "/",
    response_class=HTMLResponse
)
async def homepage(
    request: Request
):

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={}
    )


# -------------------------------------------------
# GENERATE COMIC
# -------------------------------------------------

@router.post(
    "/generate",
    response_class=HTMLResponse
)
async def generate_comic(
    request: Request,
    prompt: str = Form(...),
    character_name: str = Form(""),
    setting: str = Form(""),
    tone: str = Form(""),
    style: str = Form(""),
):

    try:

        full_prompt = (
            f"{prompt}\n"
            f"The main character is "
            f"{character_name}. "
            f"The setting is "
            f"a {setting}. "
            f"The tone is "
            f"{tone}. "
            f"The art style is "
            f"{style}."
        )

        result = _run_comic_pipeline(
            full_prompt
        )

        return templates.TemplateResponse(
            request=request,
            name="comic_preview.html",
            context={
                "layout": result["layout"],
                "comic_path": result["comic_path"],
                "pdf_path": result["pdf_path"],
                "story": result["story"],
            }
        )

    except Exception as e:

        traceback.print_exc()

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# -------------------------------------------------
# EXPORT SUCCESS
# -------------------------------------------------

@router.get(
    "/export-success",
    response_class=HTMLResponse
)
async def export_success(
    request: Request,
    pdf_path: str = ""
):

    return templates.TemplateResponse(
        request=request,
        name="export_success.html",
        context={
            "request": request,
            "pdf_path": pdf_path,
        }
    )


# -------------------------------------------------
# JSON API
# -------------------------------------------------

@router.post(
    "/generate-comic/json"
)
async def generate_comic_json(
    payload: PromptRequest
):

    try:

        full_prompt = (
            f"{payload.prompt}\n"
            f"The main character is "
            f"{payload.character_name}. "
            f"The setting is "
            f"a {payload.setting}. "
            f"The tone is "
            f"{payload.tone}. "
            f"The art style is "
            f"{payload.style}."
        )

        result = _run_comic_pipeline(
            full_prompt
        )

        return JSONResponse(
            {
                "layout": result["layout"],
                "comic_path": result["comic_path"],
                "pdf_path": result["pdf_path"],
                "story": result["story"],
            }
        )

    except Exception as e:

        traceback.print_exc()

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# -------------------------------------------------
# TEST IMAGE
# -------------------------------------------------

@router.get(
    "/test-image"
)
async def test_image(
    prompt: str = (
        "A futuristic city at sunset, "
        "sci-fi, cinematic"
    )
):

    try:

        image_path = generate_image(
            prompt
        )

        return {
            "message": (
                "Image generated successfully"
            ),
            "path": image_path,
            "url": to_web_path(
                image_path
            ),
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
