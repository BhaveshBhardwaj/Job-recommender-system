# models.py
from pydantic import BaseModel, Field
from typing import List, Optional

class UserQuery(BaseModel):
    """The input query from the user."""
    query: str = Field(..., example="I am a 12th pass from a village near Agra, I know some data entry. Find me a job.")

class JobQueryStructured(BaseModel):
    """The structured data extracted by the LLM."""
    skills: List[str] = Field(..., description="List of skills extracted from the query (e.g., 'python', 'data entry', 'driving').")
    locations: List[str] = Field(..., description="List of locations (cities, districts, or states) mentioned. e.g., 'Agra', 'Delhi', 'Rural Karnataka'.")
    experience_level: Optional[str] = Field(None, description="Inferred experience level like 'entry-level', 'mid-level', or 'experienced'.")
    job_titles: List[str] = Field(..., description="List of potential job titles to search for. e.g., 'Data Entry Operator', 'Driver', 'Software Developer'.")
    search_keywords: List[str] = Field(..., description="A list of 3-5 optimized search queries for job portals. e.g., 'data entry jobs near Agra', 'freshers job 12th pass'.")

class JobListing(BaseModel):
    """A single job listing found by a scraper."""
    title: str
    company: str
    location: str
    url: str
    source: str # e.g., "Naukri", "LinkedIn"
    description_snippet: Optional[str] = None

class RecommendationResponse(BaseModel):
    """The final response sent to the user."""
    structured_query: JobQueryStructured
    total_jobs_found: int
    best_matches: List[JobListing] = Field(..., description="Jobs that are best suited based on extracted skills.")
    other_jobs: List[JobListing] = Field(..., description="Other relevant jobs found.")