"""Kivi web app. Start with:  uvicorn app.main:app --reload

Right now this serves the shell and one stub endpoint. Every phase in the
build guide adds real behaviour behind these routes.
"""
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app.db import query

app = FastAPI(title="Kivi — semantic memory")
app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.get("/")
def home():
    return FileResponse("app/static/index.html")


@app.get("/api/health")
def health():
    row = query("select count(*) as n from episodes")[0]
    return {"ok": True, "episodes": row["n"]}


class Ask(BaseModel):
    text: str


@app.post("/api/ask")
def ask(body: Ask):
    """STUB. Phase 7 of the build guide replaces this with the real pipeline:
    query understanding (§7) → retrieval (§8) → answer contract (§8).
    """
    return {
        "answer": f"Not built yet. You said: {body.text}",
        "citations": [],
        "abstained": True,
        "repairs": [],
        "reason": "pipeline not implemented",
    }
