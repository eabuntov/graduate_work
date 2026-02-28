import json

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

from config.settings import settings
from services.tracing import setup_tracing
from api.v1.api_router import api_router


setup_tracing()

app = FastAPI(title=settings.SERVICE_NAME)

FastAPIInstrumentor.instrument_app(app)

with open("api/v1/openapi_ru.json", "r", encoding="utf-8") as f:
    custom_openapi_schema = json.load(f)


def custom_openapi():
    return custom_openapi_schema


app.openapi = custom_openapi

app.include_router(api_router)


@app.get("/health", response_class=JSONResponse)
async def healthcheck():
    """
    Простой healthcheck.
    Returns 200 OK если приложение живо.
    """
    return {"status": "ok"}
