import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles
from sqlalchemy import text

from db import engine
from v1.player import player_router
from v1.ws_router import ws_router


# -----------------------------------------------------------------------------
# Logging
# -----------------------------------------------------------------------------

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# -----------------------------------------------------------------------------
# Application
# -----------------------------------------------------------------------------

app = FastAPI(
    title="Theatre Movies Together",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)


# -----------------------------------------------------------------------------
# CORS (adjust origins in production)
# -----------------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # replace with frontend domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

# -----------------------------------------------------------------------------
# Routers
# -----------------------------------------------------------------------------

app.include_router(player_router)
app.include_router(ws_router)


# -----------------------------------------------------------------------------
# Healthcheck
# -----------------------------------------------------------------------------

@app.get("/health")
def health():
    return {"status": "ok"}