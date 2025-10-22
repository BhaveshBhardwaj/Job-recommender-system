from typing import List, Optional
import aiohttp
import aiohttp.client_exceptions
from aiohttp import ClientSession
from bs4 import BeautifulSoup
from app.models.job import JobResponse
import json
import os
from dotenv import load_dotenv

load_dotenv()

class LinkedInScraper:
    def __init__(self):
        self.base_url = "https://www.linkedin.com/jobs/search"
        # You would need to handle authentication and headers properly
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

    async def search_jobs(
        self,
        skills: List[str],
        location: Optional[str] = None,
        experience: Optional[int] = None
    ) -> List[JobResponse]:
        """
        Search for jobs on LinkedIn based on skills and other criteria
        """
        try:
            # Construct search query
            keywords = " ".join(skills)
            params = {
                "keywords": keywords,
                "location": location if location else "",
                "f_E": self._get_experience_filter(experience) if experience else "",
                "sortBy": "R"  # Sort by relevance
            }

            async with aiohttp.ClientSession(headers=self.headers) as session:
                async with session.get(self.base_url, params=params) as response:
                    if response.status == 200:
                        html = await response.text()
                        return self._parse_jobs(html)
                    else:
                        return []

        except Exception as e:
            print(f"Error scraping LinkedIn: {str(e)}")
            return []

    def _parse_jobs(self, html: str) -> List[JobResponse]:
        """
        Parse LinkedIn jobs from HTML response
        """
        jobs = []
        soup = BeautifulSoup(html, 'html.parser')
        job_cards = soup.find_all('div', class_='job-search-card')

        for card in job_cards:
            try:
                title = card.find('h3', class_='base-search-card__title').text.strip()
                company = card.find('h4', class_='base-search-card__subtitle').text.strip()
                location = card.find('span', class_='job-search-card__location').text.strip()
                link = card.find('a', class_='base-card__full-link').get('href')
                
                # Get detailed job description
                description, skills_required = self._get_job_details(link)

                jobs.append(JobResponse(
                    title=title,
                    company=company,
                    location=location,
                    description=description,
                    skills_required=skills_required,
                    source="LinkedIn",
                    apply_link=link
                ))

            except Exception as e:
                print(f"Error parsing job card: {str(e)}")
                continue

        return jobs

    def _get_job_details(self, job_url: str) -> tuple[str, List[str]]:
        """
        Get detailed job information from the job page
        """
        # This would need to be implemented with proper rate limiting and error handling
        # For now, return placeholder data
        return "Job description placeholder", ["Skill 1", "Skill 2"]

    def _get_experience_filter(self, years: int) -> str:
        """
        Convert years of experience to LinkedIn's filter format
        """
        if years <= 1:
            return "1"
        elif years <= 3:
            return "2"
        elif years <= 5:
            return "3"
        elif years <= 10:
            return "4"
        else:
            return "5"