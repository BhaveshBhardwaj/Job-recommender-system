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
from api_client import scrape_all_platforms # Make sure this points to your file

load_dotenv()

# --- LIFESPAN CONTEXT MANAGER ---
llm_chain: Optional[Runnable] = None
@asynccontextmanager
async def lifespan(app: FastAPI):
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

app = FastAPI(
    title="Smart Job Recommendation System",
    description="Uses Groq, LangChain, and FastAPI to recommend jobs based on natural language queries.",
    lifespan=lifespan
)

# --- REFACTORED LOGIC WITH SMART SORTING ---
async def get_recommendation_logic(user_query: UserQuery, chain: Runnable) -> RecommendationResponse:
    try:
        structured_query: JobQueryStructured = chain.invoke({"query": user_query.query})
        print(f"Structured query: {structured_query.model_dump_json(indent=2)}")
    except Exception as e:
        print(f"LLM Parsing Error: {e}")
        raise HTTPException(status_code=500, detail=f"Error parsing query with LLM: {e}")

    try:
        all_jobs: List[JobListing] = await scrape_all_platforms(structured_query)
        print(f"Total jobs found: {len(all_jobs)}")
    except Exception as e:
        print(f"API Client Error: {e}")
        raise HTTPException(status_code=500, detail=f"Error during job API fetching: {e}")

    # --- RURAL-OPTIMIZED SORTING LOGIC ---
    best_matches = []
    other_jobs = []
    extracted_skills = set(s.lower() for s in structured_query.skills)
    priority_sources = {'data.gov.in', 'api.setu.in', 'ncs.gov.in'} # Indian Govt/Rural Sources
    is_entry_level = structured_query.experience_level == 'entry-level'

    # Check if LLM identified government schemes as skills
    has_scheme_keywords = any(skill.lower() in ['mgnrega', 'pmkvy', 'ncs'] for skill in structured_query.skills)

    if (not extracted_skills or has_scheme_keywords) and is_entry_level:
        # Prioritize government schemes if user is entry-level OR explicitly mentioned/implied schemes
        for job in all_jobs:
            if job.source in priority_sources:
                best_matches.append(job)
            else:
                # Check for basic skill match even for other jobs
                job_title_lower = job.title.lower()
                job_desc_lower = (job.description_snippet or "").lower()
                if any(skill in job_title_lower or skill in job_desc_lower for skill in extracted_skills if skill not in ['mgnrega', 'pmkvy', 'ncs']):
                     best_matches.append(job)
                else:
                    other_jobs.append(job)
    else:
        # Standard sorting for users with specific skills
        for job in all_jobs:
            job_title_lower = job.title.lower()
            job_desc_lower = (job.description_snippet or "").lower()
            title_match = any(skill in job_title_lower for skill in extracted_skills)
            desc_match = any(skill in job_desc_lower for skill in extracted_skills)
            source_match = job.source in priority_sources

            # Prioritize matches OR relevant govt schemes for entry level
            if (title_match or desc_match) or (is_entry_level and source_match):
                best_matches.append(job)
            else:
                other_jobs.append(job)

    # --- NEW: Ensure best_matches isn't overly long, move less relevant ones ---
    MAX_BEST_MATCHES = 10
    if len(best_matches) > MAX_BEST_MATCHES:
        # Simple heuristic: move non-priority sources out if list is too long
        new_best = []
        moved_to_other = []
        for job in best_matches:
            if job.source in priority_sources or len(new_best) < MAX_BEST_MATCHES:
                 new_best.append(job)
            else:
                 moved_to_other.append(job)
        best_matches = new_best
        other_jobs.extend(moved_to_other)


    return RecommendationResponse(
        structured_query=structured_query,
        total_jobs_found=len(all_jobs),
        best_matches=best_matches,
        other_jobs=other_jobs
    )

# --- Text Formatting Helper ---
def format_response_as_text(data: RecommendationResponse) -> str:
    # (Same as before)
    lines = []
    lines.append("--- Your Job Recommendation Summary ---")
    lines.append(f"\nQuery Analysis:")
    lines.append(f"  Skills: {', '.join(data.structured_query.skills)}")
    lines.append(f"  Locations: {', '.join(data.structured_query.locations)}")
    if data.structured_query.experience_level:
        lines.append(f"  Level: {data.structured_query.experience_level}")
    lines.append(f"\nTotal Results Found: {data.total_jobs_found}\n")

    if data.best_matches:
        lines.append("--- Best Matches & Opportunities ---")
        for i, job in enumerate(data.best_matches, 1):
            lines.append(f"\n{i}. {job.title} @ {job.company}")
            lines.append(f"   Location: {job.location}")
            if job.description_snippet: lines.append(f"   Details: {job.description_snippet}")
            lines.append(f"   URL: {job.url}")
            lines.append(f"   (Source: {job.source})")

    if data.other_jobs:
        lines.append("\n--- Other Relevant Jobs ---")
        for i, job in enumerate(data.other_jobs, 1):
             lines.append(f"\n{i}. {job.title} @ {job.company}")
             lines.append(f"   Location: {job.location}")
             lines.append(f"   URL: {job.url}")
             lines.append(f"   (Source: {job.source})")

    if not data.best_matches and not data.other_jobs:
        lines.append("\nNo specific jobs found. Consider checking government portals or training centers listed, or try refining your query.")

    return "\n".join(lines)

# --- FastAPI Endpoints ---
@app.get('/favicon.ico', include_in_schema=False)
async def favicon(): return Response(content=None, status_code=204)

@app.get("/", summary="Serve the main UI")
async def read_root(): return FileResponse('index.html')

@app.post("/recommend", response_model=RecommendationResponse, summary="Get Job Recommendations (JSON)")
async def get_recommendations_json(user_query: UserQuery):
    global llm_chain
    if llm_chain is None: raise HTTPException(status_code=500, detail="LLM not ready.")
    try:
        return await get_recommendation_logic(user_query, llm_chain)
    except HTTPException as he: raise he
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

@app.post("/recommend-text", response_class=Response, summary="Get Job Recommendations (Plain Text)")
async def get_recommendations_text(user_query: UserQuery):
    global llm_chain
    if llm_chain is None: raise HTTPException(status_code=500, detail="LLM not ready.")
    try:
        response_data = await get_recommendation_logic(user_query, llm_chain)
        text_output = format_response_as_text(response_data)
        return Response(content=text_output, media_type="text/plain")
    except HTTPException as he: raise he
    except Exception as e: raise HTTPException(status_code=500, detail=f"Error: {e}")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)