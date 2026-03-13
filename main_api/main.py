import json
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
import sys

from starlette.staticfiles import StaticFiles

sys.path.append("/opt")
from api.v1.home_router import home_router
from api.v1.films_router import films_router
from api.v1.persons_router import persons_router
from api.v1.genres_router import genres_router
from api.v1.search_router import films_search_router


app = FastAPI(title="films API with Elasticsearch")

app.include_router(home_router)
app.include_router(films_router)
app.include_router(genres_router)
app.include_router(persons_router)
app.include_router(films_search_router)

templates = Jinja2Templates(directory="templates")

with open("api/v1/openapi.json", "r", encoding="utf-8") as f:
    custom_openapi_schema = json.load(f)

app.mount("/static", StaticFiles(directory="static"), name="static")


# Override FastAPI's openapi generation function
def custom_openapi():
    custom_openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT"
        }
    }
    custom_openapi_schema["security"] = [{"BearerAuth": []}]
    return custom_openapi_schema


# Assign it to the app
app.openapi = custom_openapi


@app.get("/health", response_class=JSONResponse)
async def healthcheck():
    """
    Простой healthcheck.
    Returns 200 OK если приложение живо.
    """
    return {"status": "ok"}
