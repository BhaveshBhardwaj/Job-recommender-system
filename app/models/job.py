from pydantic import BaseModel
from typing import List

class JobResponse(BaseModel):
    title: str
    company: str
    location: str
    description: str
    skills_required: List[str]
    source: str
    apply_link: str