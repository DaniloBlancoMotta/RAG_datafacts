import os

from dotenv import load_dotenv
from fastapi import FastAPI

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

from app.core import engine
from app.models import QueryRequest, QueryResponse

app = FastAPI(title="Red Hat RAG API", version="1.0.0")


@app.post("/query", response_model=QueryResponse)
async def query(req: QueryRequest):
    return engine.process(req.query)
