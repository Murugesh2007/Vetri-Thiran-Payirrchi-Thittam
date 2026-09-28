from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parent.parent

STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"
PANELS_DIR = STATIC_DIR / "panels"
EXPORTS_DIR = STATIC_DIR / "exports"
EXPORT_FOLDER = EXPORTS_DIR


class Settings(BaseSettings):
    GEMINI_API_KEY: str = ""
    HF_API_KEY: str = ""

    GEMINI_FLASH_MODEL: str = "gemini-3.8-flash"
    GEMINI_STORY_MODEL: str = "gemini-3.1-pro-preview"

    IMAGE_MODEL: str = "stable-diffusion-v1-5/stable-diffusion-v1-5"
    IMAGE_DEVICE: str = "auto"

    IMAGE_STEPS: int = 25
    IMAGE_WIDTH: int = 512
    IMAGE_HEIGHT: int = 512
    IMAGE_GUIDANCE_SCALE: float = 7.5

    MAX_PANELS: int = 5
    USE_AI: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()


GEMINI_API_KEY = settings.GEMINI_API_KEY
HF_API_KEY = settings.HF_API_KEY

GEMINI_FLASH_MODEL = settings.GEMINI_FLASH_MODEL
GEMINI_PRO_MODEL = settings.GEMINI_STORY_MODEL
STABLE_DIFFUSION_MODEL = settings.IMAGE_MODEL

STABLE_DIFFUSION_MODEL = settings.IMAGE_MODEL
FORCE_PLACEHOLDER_IMAGES = False


def ensure_directories():
    STATIC_DIR.mkdir(parents=True, exist_ok=True)
    TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
    PANELS_DIR.mkdir(parents=True, exist_ok=True)
    EXPORTS_DIR.mkdir(parents=True, exist_ok=True)


def to_web_path(path):
    path = Path(path)

    try:
        relative_path = path.resolve().relative_to(STATIC_DIR.resolve())
    except ValueError:
        relative_path = path

    return "/static/" + relative_path.as_posix().lstrip("/")

EXPORT_FOLDER = EXPORTS_DIR
FONT_PATH = BASE_DIR / "arial.ttf"
