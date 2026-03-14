import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy import text

from config.config import setup_logging
from v1.player import player_router
from v1.ws_router import ws_router


setup_logging()
logger = logging.getLogger(__name__)


app = FastAPI(
    title="Theatre Movies Together",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.mount("/static", StaticFiles(directory="static"), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(player_router)
app.include_router(ws_router)


@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse("static/favicon.ico")