"""Kivi web app. Start with:  uvicorn app.main:app --reload

Right now this serves the shell and one stub endpoint. Every phase in the
build guide adds real behaviour behind these routes.
"""
import uuid
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app.db import query, log_decision
from app.understand import understand
from app.retrieve import retrieve
from app.answer import answer
from app.embeddings import embed

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
    # Assume 'demo' user
    user = query("select id from users where display_name = 'demo'")[0]
    user_id = user["id"]
    query_id = str(uuid.uuid4())
    
    # 1. Understand
    understanding = understand(user_id, body.text)
    
    # 2. Retrieve
    semantic_embedding = embed(understanding["normalized"])
    retrieved_items = retrieve(
        user_id, query_id, understanding["normalized"], semantic_embedding
    )
    
    # 3. Answer
    response = answer(query_id, retrieved_items)
    
    return response
