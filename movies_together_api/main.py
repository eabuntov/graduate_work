import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from db import engine
from routers.player import router as player_router
from ws_routes import router as ws_router


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


# -----------------------------------------------------------------------------
# Routers
# -----------------------------------------------------------------------------

app.include_router(player_router)
app.include_router(ws_router)


# -----------------------------------------------------------------------------
# Startup / Shutdown
# -----------------------------------------------------------------------------

@app.on_event("startup")
def startup_event():
    """
    Verify DB connectivity on startup.
    """
    logger.info("Starting application...")

    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        logger.info("Database connection established.")
    except Exception as e:
        logger.exception("Database connection failed.")
        raise e


@app.on_event("shutdown")
def shutdown_event():
    logger.info("Shutting down application...")


# -----------------------------------------------------------------------------
# Healthcheck
# -----------------------------------------------------------------------------

@app.get("/health")
def health():
    return {"status": "ok"}