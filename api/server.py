from doctest import debug_script

from dotenv import dotenv_values
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from search.tavily_search import TavilySearch

description = dotenv_values()["DESCRIPTION"]

app = FastAPI(
    title="Export Automation System API",
    description=f"REST API for {description}",
    version="1.0.0",
)


class SearchRequest(BaseModel):
    query: str


@app.get("/api/health")
def health_check():
    return {
        "status": "ok",
        "service": "export-automation-system",
    }


@app.post("/api/search")
def search_buyers(request: SearchRequest):
    query = request.query.strip()

    if not query:
        raise HTTPException(
            status_code=400,
            detail="Query cannot be empty",
        )

    try:
        search = TavilySearch()

        results = search.search(query)

        return {
            "query": query,
            "total": len(results),
            "results": results,
        }

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error),
        )