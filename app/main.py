"""Kivi web app. Start with:  uvicorn app.main:app --reload"""
import uuid

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app.answer import answer
from app.db import query
from app.embeddings import embed
from app.retrieve import retrieve
from app.understand import understand

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
    user = query("select id from users where display_name = 'demo'")[0]
    user_id = user["id"]
    query_id = str(uuid.uuid4())

    # 1. Understand — repair, slots, focus, time windows
    understanding = understand(user_id, body.text)

    # 2. Retrieve — structured prefilter, vector search, rerank, score floor
    semantic_embedding = embed(understanding["normalized"])
    retrieved_items = retrieve(
        user_id, query_id, understanding["normalized"], semantic_embedding
    )

    # 3. Answer — grounded in evidence, or abstain
    response = answer(query_id, understanding["normalized"], retrieved_items)

    # surface what the repair layer did, so a wrong repair is visible not silent
    response["repairs"] = understanding.get("substitutions", [])

    return response