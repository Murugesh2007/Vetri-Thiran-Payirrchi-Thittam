from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .config import ensure_directories
from .routes import router



@asynccontextmanager
async def lifespan(app: FastAPI):
    ensure_directories()
    yield


app = FastAPI(
    title="ComicCraft",
    description="AI Comic Story Creator using Gemini and Stable Diffusion",
    version="1.0.0",
    lifespan=lifespan,
)

app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(router)


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "application": "ComicCraft",
        "version": "1.0.0",
    }