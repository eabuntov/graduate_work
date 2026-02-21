from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from uuid import UUID

from fastapi.templating import Jinja2Templates

from db import get_db
from models import WatchSession, WatchSessionParticipant, Movie

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/watch/{session_id}", response_class=HTMLResponse)
def watch_player(
    request: Request,
    session_id: str,
    db: Session = Depends(get_db),
):
    # Validate session
    session = (
        db.query(WatchSession)
        .filter(WatchSession.id == UUID(session_id))
        .first()
    )

    if not session or session.status != "active":
        raise HTTPException(status_code=404, detail="Session not found")

    movie = (
        db.query(Movie)
        .filter(Movie.id == session.movie_id)
        .first()
    )

    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    return templates.TemplateResponse(
        "watch_player.html",
        {
            "request": request,
            "session_id": session_id,
            "movie_title": movie.title,
            "video_url": movie.video_url,
            "poster_url": movie.poster_url,
        },
    )