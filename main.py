# main.py
import uvicorn
import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from typing import List, Optional

from contextlib import asynccontextmanager
from fastapi.responses import FileResponse, Response
from langchain_core.runnables import Runnable

from models import UserQuery, RecommendationResponse, JobListing, JobQueryStructured
from llm_parser import get_llm_chain
from api_client import scrape_all_platforms

# Load environment variables (like GROQ_API_KEY)
load_dotenv()

# --- LIFESPAN CONTEXT MANAGER ---

llm_chain: Optional[Runnable] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handles application startup and shutdown events.
    """
    global llm_chain
    print("FastAPI server starting up...")
    if not os.getenv("GROQ_API_KEY"):
        raise RuntimeError("GROQ_API_KEY not set in .env file")
    
    try:
        llm_chain = get_llm_chain()
        print("LLM chain is loaded.")
    except Exception as e:
        print(f"Error: {e}. LLM chain could not be initialized.")
        llm_chain = None
    
    yield
    
    print("FastAPI server shutting down...")

# --- END LIFESPAN ---

app = FastAPI(
    title="Smart Job Recommendation System",
    description="Uses Groq, LangChain, and FastAPI to recommend jobs based on natural language queries.",
    lifespan=lifespan
)

@app.get('/favicon.ico', include_in_schema=False)
async def favicon():
    return Response(content=None, status_code=204)

@app.get("/", summary="Serve the main UI")
async def read_root():
    return FileResponse('index.html')

@app.post("/recommend", response_model=RecommendationResponse, summary="Get Job Recommendations")
async def get_recommendations(user_query: UserQuery):
    global llm_chain
    if llm_chain is None:
        raise HTTPException(status_code=500, detail="LLM chain is not available. Check server startup logs.")

    print(f"Received query: {user_query.query}")
    
    try:
        structured_query: JobQueryStructured = llm_chain.invoke({"query": user_query.query})
        print(f"Structured query: {structured_query.model_dump_json(indent=2)}")
    except Exception as e:
        print(f"LLM Parsing Error: {e}")
        raise HTTPException(status_code=500, detail=f"Error parsing query with LLM: {e}")

    try:
        # This function now calls the API clients
        all_jobs: List[JobListing] = await scrape_all_platforms(structured_query)
        print(f"Total jobs found: {len(all_jobs)}")
    except Exception as e:
        print(f"API Client Error: {e}")
        raise HTTPException(status_code=500, detail=f"Error during job API fetching: {e}")

    best_matches = []
    other_jobs = []
    extracted_skills = set(s.lower() for s in structured_query.skills)

    if not extracted_skills:
        other_jobs = all_jobs
    else:
        for job in all_jobs:
            job_title_lower = job.title.lower()
            if any(skill in job_title_lower for skill in extracted_skills):
                best_matches.append(job)
            else:
                other_jobs.append(job)

    return RecommendationResponse(
        structured_query=structured_query,
        total_jobs_found=len(all_jobs),
        best_matches=best_matches,
        other_jobs=other_jobs
    )

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)