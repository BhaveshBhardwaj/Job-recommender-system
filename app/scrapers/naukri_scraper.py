from typing import List, Optional
import aiohttp
from bs4 import BeautifulSoup
from app.models.job import JobResponse
import json
import os
from dotenv import load_dotenv

load_dotenv()

class NaukriScraper:
    def __init__(self):
        self.base_url = "https://www.naukri.com/jobs-in-india"
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
        Search for jobs on Naukri.com based on skills and other criteria
        """
        try:
            # Construct search query
            keywords = "-".join(skills)
            search_url = f"{self.base_url}/{keywords}"
            if location:
                search_url += f"-in-{location}"

            async with aiohttp.ClientSession(headers=self.headers) as session:
                async with session.get(search_url) as response:
                    if response.status == 200:
                        html = await response.text()
                        return self._parse_jobs(html)
                    else:
                        return []

        except Exception as e:
            print(f"Error scraping Naukri: {str(e)}")
            return []

    def _parse_jobs(self, html: str) -> List[JobResponse]:
        """
        Parse Naukri jobs from HTML response
        """
        jobs = []
        soup = BeautifulSoup(html, 'html.parser')
        job_cards = soup.find_all('article', class_='jobTuple')

        for card in job_cards:
            try:
                title = card.find('a', class_='title').text.strip()
                company = card.find('a', class_='subTitle').text.strip()
                location = card.find('li', class_='location').text.strip()
                link = card.find('a', class_='title').get('href')
                
                # Get detailed job description
                description, skills_required = self._get_job_details(link)

                jobs.append(JobResponse(
                    title=title,
                    company=company,
                    location=location,
                    description=description,
                    skills_required=skills_required,
                    source="Naukri",
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
        Convert years of experience to Naukri's filter format
        """
        if years <= 1:
            return "0-1"
        elif years <= 3:
            return "1-3"
        elif years <= 5:
            return "3-5"
        elif years <= 10:
            return "5-10"
        else:
            return "10-50"