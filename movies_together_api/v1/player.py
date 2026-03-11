import logging
from uuid import UUID

from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from db import get_db
from models import WatchSession, FilmWork, FilmWorkStorage


player_router = APIRouter()
templates = Jinja2Templates(directory="templates")


@player_router.get("/watch/{session_id}", response_class=HTMLResponse)
async def watch_player(
    request: Request,
    session_id: str,
    db: AsyncSession = Depends(get_db),
):
    # Validate session
    result = await db.execute(
        select(WatchSession).where(WatchSession.id == UUID(session_id))
    )
    session = result.scalar_one_or_none()

    if not session or session.status != "active":
        raise HTTPException(status_code=404, detail="Session not found")

    # Load movie
    result = await db.execute(
        select(FilmWork.title, FilmWorkStorage.video_url)
        .join(FilmWorkStorage, FilmWork.id == FilmWorkStorage.film_work_id)
        .where(FilmWork.id == session.movie_id)
    )
    movie = result.one_or_none()

    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    return templates.TemplateResponse(
        "watch_player.html",
        {
            "request": request,
            "session_id": session_id,
            "movie_title": movie.title,
            "video_url": movie.video_url,
        },
    )