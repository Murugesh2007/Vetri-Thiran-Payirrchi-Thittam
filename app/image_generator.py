"""
ComicCraft image generator.

Uses Hugging Face Diffusers + Stable Diffusion to generate comic images.

If image generation fails, the error is printed clearly and the exception
is raised instead of silently creating a colored placeholder image.
"""

import os
import re

import torch
from diffusers import StableDiffusionPipeline

from app.config import (
    PANELS_DIR,
    STABLE_DIFFUSION_MODEL,
    HF_API_KEY,
    FORCE_PLACEHOLDER_IMAGES,
    settings,
)


# ---------------------------------------------------------
# Global Stable Diffusion pipeline
# ---------------------------------------------------------

_pipe = None


# ---------------------------------------------------------
# Filename helper
# ---------------------------------------------------------

def sanitize_filename(prompt: str) -> str:
    """
    Convert prompt text into a safe PNG filename.
    """

    base = re.sub(
        r"[^a-zA-Z0-9]+",
        "_",
        prompt.strip().lower(),
    )

    base = base.strip("_")[:60]

    if not base:
        base = "panel"

    return f"{base}.png"


# ---------------------------------------------------------
# Load Stable Diffusion
# ---------------------------------------------------------

def _load_pipeline():
    """
    Load Stable Diffusion only once.

    Uses GPU when CUDA is available.
    Otherwise uses CPU.
    """

    global _pipe

    if _pipe is not None:
        return _pipe

    if FORCE_PLACEHOLDER_IMAGES:
        raise RuntimeError(
            "FORCE_PLACEHOLDER_IMAGES is enabled. "
            "Set it to False in app/config.py."
        )

    print("")
    print("======================================")
    print("Loading Stable Diffusion...")
    print("======================================")

    try:

        device = (
            "cuda"
            if torch.cuda.is_available()
            else "cpu"
        )

        if device == "cuda":
            dtype = torch.float16
        else:
            dtype = torch.float32

        print(f"Device: {device}")
        print(f"Model: {STABLE_DIFFUSION_MODEL}")

        if HF_API_KEY:
            print("Hugging Face token: Found")
        else:
            print("Hugging Face token: Not found")

        kwargs = {
            "torch_dtype": dtype,
        }

        # Newer diffusers versions can use token=
        if HF_API_KEY:
            kwargs["token"] = HF_API_KEY

        print("Downloading/loading Stable Diffusion model...")
        print("This may take some time on the first run.")

        _pipe = StableDiffusionPipeline.from_pretrained(
            STABLE_DIFFUSION_MODEL,
            **kwargs,
        )

        _pipe = _pipe.to(device)

        # CPU memory optimization
        if device == "cpu":

            try:
                _pipe.enable_attention_slicing()
                print("Attention slicing enabled.")
            except Exception:
                pass

        # GPU memory optimization
        if device == "cuda":

            try:
                _pipe.enable_attention_slicing()
                print("GPU attention slicing enabled.")
            except Exception:
                pass

        print("======================================")
        print("Stable Diffusion loaded successfully.")
        print("======================================")
        print("")

        return _pipe

    except Exception as e:

        print("")
        print("======================================")
        print("STABLE DIFFUSION LOAD ERROR")
        print("======================================")
        print(str(e))
        print("======================================")
        print("")

        raise


# ---------------------------------------------------------
# Generate image
# ---------------------------------------------------------

def generate_image(prompt, filename=None):
    """
    Generate one comic panel image.

    Args:
        prompt: Image description.
        filename: Optional filename.

    Returns:
        Path to generated image.
    """

    if not prompt:
        raise ValueError(
            "Image prompt cannot be empty."
        )

    if filename is None:
        filename = sanitize_filename(prompt)

    os.makedirs(
        str(PANELS_DIR),
        exist_ok=True,
    )

    path = os.path.join(
        str(PANELS_DIR),
        filename,
    )

    print("")
    print("======================================")
    print("Generating Comic Panel")
    print("======================================")
    print(f"Prompt: {prompt}")
    print(f"Output: {path}")
    print("======================================")

    pipe = _load_pipeline()

    try:

        # Get settings safely
        steps = getattr(
            settings,
            "IMAGE_STEPS",
            25,
        )

        width = getattr(
            settings,
            "IMAGE_WIDTH",
            512,
        )

        height = getattr(
            settings,
            "IMAGE_HEIGHT",
            512,
        )

        guidance = getattr(
            settings,
            "IMAGE_GUIDANCE_SCALE",
            7.5,
        )

        print(
            f"Steps: {steps}"
        )

        print(
            f"Size: {width}x{height}"
        )

        print(
            f"Guidance: {guidance}"
        )

        # Generate image
        result = pipe(
            prompt=prompt,
            num_inference_steps=steps,
            width=width,
            height=height,
            guidance_scale=guidance,
        )

        image = result.images[0]

        image.save(path)

        print("")
        print("======================================")
        print("IMAGE GENERATED SUCCESSFULLY")
        print("======================================")
        print(path)
        print("======================================")
        print("")

        # Release temporary GPU memory
        if torch.cuda.is_available():

            try:
                torch.cuda.empty_cache()
            except Exception:
                pass

        return path

    except Exception as e:

        print("")
        print("======================================")
        print("STABLE DIFFUSION GENERATION ERROR")
        print("======================================")
        print(f"Prompt: {prompt}")
        print(f"Error: {e}")
        print("======================================")
        print("")

        # Release GPU memory after an error
        if torch.cuda.is_available():

            try:
                torch.cuda.empty_cache()
            except Exception:
                pass

        # IMPORTANT:
        # Do not create a fake colored image.
        # Show the real error instead.
        raise