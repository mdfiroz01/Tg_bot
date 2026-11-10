
import json
import os
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "data" / "videos.json"
INDEX_FILE = BASE_DIR / "index.html"

app = FastAPI(title="NightStream API")

app.mount(
    "/static",
    StaticFiles(directory=str(BASE_DIR / "static")),
    name="static"
)


def load_videos():
    if not DATA_FILE.exists():
        return []

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        return []


@app.get("/")
def home():
    if not INDEX_FILE.exists():
        raise HTTPException(404, "index.html not found")
    return FileResponse(INDEX_FILE)


@app.get("/api/trending")
def trending():
    videos = load_videos()

    videos.sort(
        key=lambda video: int(video.get("views", 0) or 0),
        reverse=True
    )

    return {"items": videos[:30]}


@app.get("/api/search")
def search(q: str = Query(default="")):
    videos = load_videos()
    keyword = q.strip().lower()

    if not keyword:
        return {"items": videos}

    results = []

    for video in videos:
        searchable = " ".join([
            str(video.get("title", "")),
            str(video.get("author", "")),
            " ".join(video.get("tags", []))
                if isinstance(video.get("tags"), list)
                else str(video.get("tags", ""))
        ]).lower()

        if keyword in searchable:
            results.append(video)

    return {"items": results}


@app.get("/api/stream")
def stream(video_id: str = Query(default="", alias="id")):
    videos = load_videos()

    video = next(
        (item for item in videos if str(item.get("id")) == video_id),
        None
    )

    if not video:
        raise HTTPException(404, "Video not found")

    if not video.get("m3u8"):
        raise HTTPException(404, "Stream URL not configured")

    return {
        "id": video.get("id"),
        "title": video.get("title", ""),
        "m3u8": video.get("m3u8"),
        "thumb": video.get("thumb", "")
    }


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "NightStream API"}
