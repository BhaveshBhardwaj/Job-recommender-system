# api_client.py
import asyncio
import httpx
import os
from typing import List, Optional, Dict, Any, Union
from models import JobQueryStructured, JobListing

# --- Helper Function for Safe Data Extraction ---

def safe_get(data: Union[Dict, Any], key_path: str, default: Any = "N/A") -> Any:
    """
    Safely get a nested value from a dictionary.
    Example: safe_get(data, 'location.display_name', 'Remote')
    """
    try:
        keys = key_path.split('.')
        value = data
        for key in keys:
            if isinstance(value, dict):
                value = value[key]
            elif isinstance(value, list) and key.isdigit() and len(value) > int(key):
                value = value[int(key)]
            else:
                return default
        return value if value is not None else default
    except (KeyError, TypeError, IndexError):
        return default

# --- ================================== ---
# --- (NO-KEY) Publicly Available APIs ---
# --- ================================== ---

async def fetch_remotive_jobs(query: JobQueryStructured, client: httpx.AsyncClient) -> List[JobListing]:
    """
    Fetches remote jobs from Remotive.io.
    Requires NO API key.
    Docs: https://github.com/remotive-com/remote-jobs-api
    """
    print("[API Client] Querying Remotive (No-Key)...")
    jobs_list: List[JobListing] = []
    
    # Use the first skill as the search term
    search_term = query.skills[0] if query.skills else (query.job_titles[0] if query.job_titles else "developer")
    url = f"https://remotive.com/api/remote-jobs?search={search_term}&limit=20"
    
    try:
        response = await client.get(url, timeout=10.0)
        if response.status_code != 200:
            print(f"[API Client ERROR - Remotive] Status {response.status_code}: {response.text}")
            return []
            
        data = response.json()
        
        for item in data.get("jobs", []):
            jobs_list.append(JobListing(
                title=safe_get(item, 'title'),
                company=safe_get(item, 'company_name'),
                location=safe_get(item, 'candidate_required_location', 'Remote'),
                url=safe_get(item, 'url', '#'),
                source="Remotive.io",
                description_snippet=safe_get(item, 'description', '')[:250].replace('<br>', ' ') + "..."
            ))
        
        print(f"[API Client] Found {len(jobs_list)} jobs from Remotive.")
        
    except httpx.RequestError as e:
        print(f"[API Client ERROR - Remotive] {e}")
    except Exception as e:
        print(f"[API Client PARSE ERROR - Remotive] {e}")
        
    return jobs_list

async def fetch_usajobs_public(query: JobQueryStructured, client: httpx.AsyncClient) -> List[JobListing]:
    """
    Fetches US government jobs from USAJobs.
    This is a *public* endpoint that does not require the main API key,
    but it is less powerful. We will use it as a no-key example.
    """
    print("[API Client] Querying USAJobs (Public No-Key)...")
    jobs_list: List[JobListing] = []
    
    search_term = " ".join(query.skills) if query.skills else query.job_titles[0]
    location = query.locations[0] if query.locations else ""
    
    url = f"https://jobs.usajobs.gov/search/results?k={search_term}&l={location}&p=1"
    
    try:
        # We must set a user-agent to avoid being blocked
        headers = {"User-Agent": "Python-Job-Recommender-Client"}
        # We must follow redirects for this public endpoint
        response = await client.get(url, headers=headers, timeout=10.0, follow_redirects=True)
        
        # This endpoint doesn't return JSON, it's a search page.
        # This is a placeholder to show how a public endpoint works.
        # A full implementation would require scraping this page.
        # For this example, we will just show that the query was built.
        
        print(f"[API Client] USAJobs (Public) query built. Full scraping not implemented. URL: {url}")
        
        # Example of what you *would* add if this were a JSON API:
        # data = response.json()
        # for item in data.get("SearchResult", {}).get("SearchResultItems", []):
        #     jobs_list.append(JobListing(...))
        
    except httpx.RequestError as e:
        print(f"[API Client ERROR - USAJobs (Public)] {e}")
    
    return jobs_list

# --- ======================================== ---
# --- (KEY-REQUIRED) General & Tech Job APIs ---
# --- ======================================== ---

async def fetch_adzuna_jobs(query: JobQueryStructured, client: httpx.AsyncClient) -> List[JobListing]:
    """
    Fetches jobs from Adzuna (India).
    Requires: ADZUNA_APP_ID and ADZUNA_APP_KEY
    """
    print("[API Client] Querying Adzuna (Key Required)...")
    jobs_list: List[JobListing] = []
    app_id = os.getenv("ADZUNA_APP_ID")
    app_key = os.getenv("ADZUNA_APP_KEY")
    
    if not all([app_id, app_key]):
        print("[API Client] ADZUNA_APP_ID or ADZUNA_APP_KEY not set. Skipping Adzuna.")
        return []

    search_term = " ".join(query.skills) if query.skills else query.job_titles[0]
    location = query.locations[0] if query.locations else "India"
    country_code = "in" # We found this for India
    
    url = f"https://api.adzuna.com/v1/api/jobs/{country_code}/search/1"
    params = {
        "app_id": app_id,
        "app_key": app_key,
        "what": search_term,
        "where": location,
        "results_per_page": 20
    }
    
    try:
        response = await client.get(url, params=params, timeout=10.0)
        response.raise_for_status()
        data = response.json()
        
        for item in data.get("results", []):
            jobs_list.append(JobListing(
                title=safe_get(item, 'title'),
                company=safe_get(item, 'company.display_name'),
                location=safe_get(item, 'location.display_name'),
                url=safe_get(item, 'redirect_url', '#'),
                source="Adzuna",
                description_snippet=safe_get(item, 'description', '')
            ))
        print(f"[API Client] Found {len(jobs_list)} jobs from Adzuna.")
        
    except httpx.RequestError as e:
        print(f"[API Client ERROR - Adzuna] {e}")
    except Exception as e:
        print(f"[API Client PARSE ERROR - Adzuna] {e}")
        
    return jobs_list

async def fetch_jooble_jobs(query: JobQueryStructured, client: httpx.AsyncClient) -> List[JobListing]:
    """
    Fetches jobs from Jooble.
    Requires: JOOBLE_API_KEY
    """
    print("[API Client] Querying Jooble (Key Required)...")
    jobs_list: List[JobListing] = []
    api_key = os.getenv("JOOBLE_API_KEY")

    if not api_key:
        print("[API Client] JOOBLE_API_KEY not set. Skipping Jooble.")
        return []

    url = "https://jooble.org/api/"
    headers = {"Content-Type": "application/json"}
    payload = {
        "keywords": " ".join(query.skills) if query.skills else query.job_titles[0],
        "location": query.locations[0] if query.locations else "India"
    }

    try:
        response = await client.post(url + api_key, headers=headers, json=payload, timeout=10.0)
        response.raise_for_status()
        data = response.json()

        for item in data.get("jobs", []):
            jobs_list.append(JobListing(
                title=safe_get(item, 'title'),
                company=safe_get(item, 'company'),
                location=safe_get(item, 'location'),
                url=safe_get(item, 'link', '#'),
                source="Jooble",
                description_snippet=safe_get(item, 'snippet', '')
            ))
        print(f"[API Client] Found {len(jobs_list)} jobs from Jooble.")

    except httpx.RequestError as e:
        print(f"[API Client ERROR - Jooble] {e}")
    except Exception as e:
        print(f"[API Client PARSE ERROR - Jooble] {e}")

    return jobs_list

async def fetch_the_muse_jobs(query: JobQueryStructured, client: httpx.AsyncClient) -> List[JobListing]:
    """
    Fetches jobs from The Muse. Good for tech & internships.
    Requires: THE_MUSE_API_KEY
    """
    print("[API Client] Querying The Muse (Key Required)...")
    jobs_list: List[JobListing] = []
    api_key = os.getenv("THE_MUSE_API_KEY")

    if not api_key:
        print("[API Client] THE_MUSE_API_KEY not set. Skipping The Muse.")
        return []

    # Build query params
    params = {"api_key": api_key, "page": 1}
    if query.skills:
        params["category"] = query.skills[0] # Muse filters by category
    if query.locations:
        params["location"] = query.locations[0]
    if query.experience_level == 'entry-level':
        params["level"] = "Internship" # Good proxy for entry-level

    url = "https://www.themuse.com/api/public/jobs"
    
    try:
        response = await client.get(url, params=params, timeout=10.0)
        response.raise_for_status()
        data = response.json()

        for item in data.get("results", []):
            jobs_list.append(JobListing(
                title=safe_get(item, 'name'),
                company=safe_get(item, 'company.name'),
                location=safe_get(item, 'locations.0.name', 'N/A'),
                url=safe_get(item, 'refs.landing_page', '#'),
                source="The Muse",
                description_snippet=safe_get(item, 'contents', '...').replace('<br>', ' ')[0:250] + "..."
            ))
        print(f"[API Client] Found {len(jobs_list)} jobs from The Muse.")

    except httpx.RequestError as e:
        print(f"[API Client ERROR - The Muse] {e}")
    except Exception as e:
        print(f"[API Client PARSE ERROR - The Muse] {e}")

    return jobs_list

async def fetch_usajobs_auth(query: JobQueryStructured, client: httpx.AsyncClient) -> List[JobListing]:
    """
    Fetches US government jobs from USAJobs (Authenticated).
    Requires: USAJOBS_EMAIL and USAJOBS_API_KEY
    """
    print("[API Client] Querying USAJobs (Auth Key Required)...")
    jobs_list: List[JobListing] = []
    email = os.getenv("USAJOBS_EMAIL")
    api_key = os.getenv("USAJOBS_API_KEY")

    if not all([email, api_key]):
        print("[API Client] USAJOBS_EMAIL or USAJOBS_API_KEY not set. Skipping USAJobs (Auth).")
        return []

    headers = {
        "Host": "data.usajobs.gov",
        "User-Agent": email,
        "Authorization-Key": api_key
    }
    params = {
        "Keyword": " ".join(query.skills) if query.skills else query.job_titles[0],
        "LocationName": query.locations[0] if query.locations else "",
        "ResultsPerPage": 20
    }
    url = "https://data.usajobs.gov/api/search"

    try:
        response = await client.get(url, params=params, headers=headers, timeout=10.0)
        response.raise_for_status()
        data = response.json()

        for item in data.get("SearchResult", {}).get("SearchResultItems", []):
            job = item.get("MatchedObjectDescriptor", {})
            jobs_list.append(JobListing(
                title=safe_get(job, 'PositionTitle'),
                company=safe_get(job, 'DepartmentName'),
                location=safe_get(job, 'PositionLocationDisplay', 'N/A'),
                url=safe_get(job, 'PositionURI', '#'),
                source="USAJobs.gov",
                description_snippet=safe_get(job, 'UserArea.Details.JobSummary', '')
            ))
        print(f"[API Client] Found {len(jobs_list)} jobs from USAJobs (Auth).")

    except httpx.RequestError as e:
        print(f"[API Client ERROR - USAJobs (Auth)] {e}")
    except Exception as e:
        print(f"[API Client PARSE ERROR - USAJobs (Auth)] {e}")

    return jobs_list
    
# --- ================================== ---
# --- (KEY-REQUIRED) India-Specific APIs ---
# --- ================================== ---

async def fetch_mantiks_jobs(query: JobQueryStructured, client: httpx.AsyncClient) -> List[JobListing]:
    """
    Fetches India-specific jobs from Mantiks (via RapidAPI).
    Requires: RAPIDAPI_KEY and RAPIDAPI_HOST
    """
    print("[API Client] Querying Mantiks (RapidAPI Key Required)...")
    jobs_list: List[JobListing] = []
    api_key = os.getenv("RAPIDAPI_KEY")
    api_host = os.getenv("RAPIDAPI_HOST") # e.g., "mantiks-india-jobs.p.rapidapi.com"

    if not all([api_key, api_host]):
        print("[API Client] RAPIDAPI_KEY or RAPIDAPI_HOST not set. Skipping Mantiks.")
        return []

    url = f"https://{api_host}/jobs"
    headers = {
        "X-RapidAPI-Key": api_key,
        "X-RapidAPI-Host": api_host
    }
    params = {
        "q": " ".join(query.skills) if query.skills else query.job_titles[0],
        "l": query.locations[0] if query.locations else "India",
        "p": "1"
    }

    try:
        response = await client.get(url, params=params, headers=headers, timeout=10.0)
        response.raise_for_status()
        data = response.json()

        # NOTE: Mantiks response structure may vary. Adjust keys as needed.
        for item in data.get("data", []):
            jobs_list.append(JobListing(
                title=safe_get(item, 'job_title'),
                company=safe_get(item, 'company_name'),
                location=safe_get(item, 'location'),
                url=safe_get(item, 'job_url', '#'),
                source="Mantiks (India)",
                description_snippet=safe_get(item, 'description', '')[:250] + "..."
            ))
        print(f"[API Client] Found {len(jobs_list)} jobs from Mantiks.")

    except httpx.RequestError as e:
        print(f"[API Client ERROR - Mantiks] {e}")
    except Exception as e:
        print(f"[API Client PARSE ERROR - Mantiks] {e}")

    return jobs_list

async def fetch_mgnrega_data(query: JobQueryStructured, client: httpx.AsyncClient) -> List[JobListing]:
    """
    Fetches MGNREGA rural job *statistics* from data.gov.in.
    This provides *context* (e.g., "10k job cards in Agra") not *postings*.
    Requires: DATA_GOV_IN_API_KEY
    """
    print("[API Client] Querying MGNREGA Stats (Key Required)...")
    jobs_list: List[JobListing] = []
    api_key = os.getenv("DATA_GOV_IN_API_KEY")
    
    if not api_key:
        print("[API Client] DATA_GOV_IN_API_KEY not set. Skipping MGNREGA.")
        return []

    url = "https://api.data.gov.in/resource/ee03643a-ee4c-48c2-ac30-9f2ff26ab722"
    params = {
        "api-key": api_key,
        "format": "json",
        "limit": 50 # Get top 50 districts
    }
    
    # Filter by location if provided
    if query.locations:
        params["filters[district_name]"] = query.locations[0].capitalize()

    try:
        response = await client.get(url, params=params, timeout=10.0)
        response.raise_for_status()
        data = response.json()

        for item in data.get("records", []):
            # This is not a job listing, so we format it as one
            jobs_list.append(JobListing(
                title=f"MGNREGA Rural Work ({safe_get(item, 'district_name')})",
                company="Govt. of India (MGNREGA)",
                location=f"{safe_get(item, 'district_name')}, {safe_get(item, 'state_name')}",
                url="https://nrega.nic.in/",
                source="data.gov.in",
                description_snippet=f"Registered Workers: {safe_get(item, 'total_no_of_workers')}. Job Cards Issued: {safe_get(item, 'total_no_of_jobcards_issued')}. This is statistical data."
            ))
        print(f"[API Client] Found {len(jobs_list)} records from MGNREGA.")

    except httpx.RequestError as e:
        print(f"[API Client ERROR - MGNREGA] {e}")
    except Exception as e:
        print(f"[API Client PARSE ERROR - MGNREGA] {e}")
        
    return jobs_list

async def fetch_pmkvy_centers(query: JobQueryStructured, client: httpx.AsyncClient) -> List[JobListing]:
    """
    Fetches PMKVY *skilling centers* from API Setu.
    This provides *training opportunities*, not *jobs*.
    Requires: API_SETU_CLIENT_ID and API_SETU_CLIENT_SECRET
    """
    print("[API Client] Querying PMKVY Centers (Key Required)...")
    jobs_list: List[JobListing] = []
    client_id = os.getenv("API_SETU_CLIENT_ID")
    client_secret = os.getenv("API_SETU_CLIENT_SECRET")
    
    if not all([client_id, client_secret]):
        print("[API Client] API_SETU_CLIENT_ID or API_SETU_CLIENT_SECRET not set. Skipping PMKVY.")
        return []
    
    # PMKVY API requires a state name. Use first location or default.
    state_name = query.locations[0] if query.locations else "Uttar Pradesh"

    # NOTE: This API uses a complex auth flow (not shown).
    # This is a placeholder for the /getTrainingCentres endpoint.
    # A real implementation needs an OAuth token handler.
    # Docs: https://betadirectory.api-setu.in/api-collection/pmkvyofficial
    
    print(f"[API Client] PMKVY query built. Full OAuth flow not implemented. Would search for centers in: {state_name}")
    
    # Example of what you would append after getting a token:
    # headers = {"Authorization": "Bearer YOUR_ACCESS_TOKEN", ...}
    # params = {"state": state_name}
    # response = await client.get(url, params=params, headers=headers)
    # ... parse response ...
    
    # For now, return a placeholder
    jobs_list.append(JobListing(
        title=f"Find PMKVY Skilling Centers near {state_name}",
        company="Govt. of India (Skill India)",
        location=state_name,
        url="http://pmkvyofficial.org",
        source="api.setu.in",
        description_snippet="This API shows locations for government-sponsored skill training (PMKVY). Full API integration requires OAuth."
    ))
        
    return jobs_list

async def fetch_ncs_jobs(query: JobQueryStructured, client: httpx.AsyncClient) -> List[JobListing]:
    """
    NEW PLACEHOLDER: Fetches jobs from National Career Service (NCS).
    This is a key government portal for all types of Indian jobs.
    Requires: NCS_API_KEY (example)
    """
    print("[API Client] Querying National Career Service (NCS)...")
    api_key = os.getenv("NCS_API_KEY")
    if not api_key:
        print("[API Client] NCS_API_KEY not set. Skipping NCS.")
        return []
        
    # The NCS API is complex. This is a placeholder showing how you'd add it.
    # You would need to register on their portal to get real endpoints and keys.
    print(f"[API Client] NCS query built. This is a placeholder.")
    
    # Placeholder result:
    return [JobListing(
        title=f"Jobs on National Career Service Portal",
        company="Govt. of India (NCS)",
        location=query.locations[0] if query.locations else "India",
        url="https://www.ncs.gov.in/",
        source="ncs.gov.in",
        description_snippet="This is a placeholder for jobs from the official Govt. of India job portal. Go to the URL to search for live vacancies."
    )]


# --- ========================== ---
# --- Main Orchestrator Function ---
# --- ========================== ---

async def scrape_all_platforms(query: JobQueryStructured) -> List[JobListing]:
    """
    Runs all API client functions concurrently using a shared httpx.AsyncClient.
    """
    all_jobs: List[JobListing] = []
    
    async with httpx.AsyncClient() as client:
        # Define all tasks to run in parallel
        tasks = [
            # --- No-Key APIs (Run First) ---
            fetch_remotive_jobs(query, client),
            # fetch_usajobs_public(query, client), # Disabled as it's not a real JSON API
            
            # --- General Key-Required APIs ---
            fetch_adzuna_jobs(query, client),
            fetch_jooble_jobs(query, client),
            fetch_the_muse_jobs(query, client),
            
            # --- India-Specific APIs ---
            fetch_mantiks_jobs(query, client),
            fetch_mgnrega_data(query, client),
            fetch_pmkvy_centers(query, client),
            fetch_ncs_jobs(query, client),
            
            # --- US-Specific API ---
            fetch_usajobs_auth(query, client)
        ]
        
        results_list = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results_list:
            if isinstance(result, list):
                all_jobs.extend(result)
            elif isinstance(result, Exception):
                print(f"[API Orchestrator] An API client failed: {result}")
                
    return all_jobs