from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional
from app.utils.skill_extractor import extract_skills
from app.scrapers.linkedin_scraper import LinkedInScraper
from app.scrapers.naukri_scraper import NaukriScraper
import os

app = FastAPI(title="Job Recommendation System")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

class UserQuery(BaseModel):
    query: str
    location: Optional[str] = None
    age: Optional[int] = None
    experience: Optional[int] = None

class JobResponse(BaseModel):
    title: str
    company: str
    location: str
    description: str
    skills_required: List[str]
    source: str
    apply_link: str

@app.post("/recommend-jobs", response_model=List[JobResponse])
async def recommend_jobs(user_query: UserQuery):
    try:
        # Extract skills from user query
        extracted_skills = extract_skills(user_query.query)
        
        if not extracted_skills:
            raise HTTPException(status_code=400, detail="No skills could be extracted from the query")
        
        # Initialize scrapers
        linkedin_scraper = LinkedInScraper()
        naukri_scraper = NaukriScraper()
        
        # Get jobs from multiple sources
        linkedin_jobs = await linkedin_scraper.search_jobs(
            skills=extracted_skills,
            location=user_query.location,
            experience=user_query.experience
        )
        
        naukri_jobs = await naukri_scraper.search_jobs(
            skills=extracted_skills,
            location=user_query.location,
            experience=user_query.experience
        )
        
        # Combine results
        all_jobs = linkedin_jobs + naukri_jobs
        
        return all_jobs
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    return FileResponse('app/static/index.html')