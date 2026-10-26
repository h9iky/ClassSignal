"""FastAPI application entry point."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.routers import router

STATIC_DIR = Path(__file__).parent / "static"

app = FastAPI(
    title="ClassSignal API",
    description="Initial API foundation for the ClassSignal educational platform.",
    version="0.1.0",
)
app.include_router(router)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
def homepage() -> FileResponse:
    """Serve the browser interface; API routes remain under /api/v1."""
    return FileResponse(STATIC_DIR / "index.html")
