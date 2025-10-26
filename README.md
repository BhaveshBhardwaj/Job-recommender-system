# 🌟 Smart Job Recommendation System

A **FastAPI-powered intelligent job recommender** that uses a **Groq-based LLM (via LangChain)** to understand natural language queries like:

> _"12th pass near Agra, computer aata hai"_

and returns not just **live job postings**, but also **rural employment statistics** and **skill training opportunities** — aggregating data from **9+ APIs**.

---

## 🚀 Core Features

- 🧠 **Natural Language Parsing:**  
  Uses a Groq LLM (via LangChain) to parse complex queries into structured JSON.

- 🔗 **Multi-API Aggregation:**  
  Concurrently queries 9+ different APIs for jobs, statistics, and training data.

- 🌍 **Holistic Recommendations:**  
  Returns three distinct recommendation types:
  1. **Live Job Postings:** Platforms like _Adzuna_, _Jooble_, _The Muse_, and _Remotive_  
  2. **Contextual Statistics:** Rural employment data from _data.gov.in (MGNREGA)_  
  3. **Training Opportunities:** Skilling centers from _API Setu (PMKVY)_

- ⚡ **Asynchronous Backend:**  
  Built with `FastAPI` and `httpx` for fast, non-blocking API calls.

---

## ⚙️ How It Works

1. The user sends a query from `index.html`.
2. `main.py` receives it at the `/recommend` endpoint.
3. The query is passed to `llm_parser.py`, which uses Groq to create a structured `JobQueryStructured` model.
4. `api_client.py` asynchronously calls all registered APIs.
5. Results are normalized into a single schema and returned as a JSON response.

---

## 🧩 Project Structure

```bash
├── .env                 # Create this file for API keys
├── .gitignore
├── requirements.txt      # Dependencies list
├── main.py               # FastAPI app entry point
├── api_client.py         # API fetching logic
├── llm_parser.py         # LangChain & Groq integration
├── models.py             # Pydantic data models
└── index.html            # Simple web frontend
🧰 Setup & Installation
1️⃣ Prerequisites
Python 3.9+

Git

2️⃣ Create Virtual Environment
bash
Copy code
# macOS/Linux
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
.\venv\Scripts\activate
3️⃣ Create requirements.txt
txt
Copy code
fastapi
uvicorn[standard]
langchain
langchain-groq
langchain-core
pydantic
python-dotenv
httpx
asyncio
4️⃣ Install Dependencies
bash
Copy code
pip install -r requirements.txt
🔑 Configure API Keys (Most Important Step)
Create a .env file in the project root and add the following:

bash
Copy code
# --- LLM API Key ---
# Get from: https://console.groq.com/
GROQ_API_KEY=gsk_...

# --- ================= ---
# --- Job API Keys (7) ---
# --- ================= ---

# 1. Adzuna
# https://developer.adzuna.com/register
ADZUNA_APP_ID=your_app_id
ADZUNA_APP_KEY=your_app_key

# 2. Jooble
# https://jooble.org/api/about
JOOBLE_API_KEY=your_api_key

# 3. The Muse
# https://www.themuse.com/developers/api/v2
THE_MUSE_API_KEY=your_api_key

# 4. USAJobs
# https://developer.usajobs.gov/signup
USAJOBS_EMAIL=your_email@gmail.com
USAJOBS_API_KEY=your_api_key

# 5. Mantiks (via RapidAPI)
# https://rapidapi.com/mantiks-mantiks-default/api/mantiks-india-jobs
RAPIDAPI_KEY=your_rapidapi_key
RAPIDAPI_HOST=mantiks-india-jobs.p.rapidapi.com

# 6. data.gov.in (for MGNREGA)
# https://api.data.gov.in/signup
DATA_GOV_IN_API_KEY=your_api_key

# 7. API Setu (for PMKVY)
# https://api.setu.in/
API_SETU_CLIENT_ID=your_client_id
API_SETU_CLIENT_SECRET=your_client_secret
🌐 API Key Registration Summary
Service	Environment Variables	Registration URL	Description
Groq	GROQ_API_KEY	console.groq.com	For LLM parsing
Adzuna	ADZUNA_APP_ID, ADZUNA_APP_KEY	developer.adzuna.com	Live jobs
Jooble	JOOBLE_API_KEY	jooble.org/api/about	Job listings
The Muse	THE_MUSE_API_KEY	themuse.com/developers	Tech & internship jobs
USAJobs	USAJOBS_EMAIL, USAJOBS_API_KEY	developer.usajobs.gov	US government jobs
Mantiks	RAPIDAPI_KEY, RAPIDAPI_HOST	RapidAPI	India-specific jobs
data.gov.in	DATA_GOV_IN_API_KEY	api.data.gov.in	Rural employment data
API Setu	API_SETU_CLIENT_ID, API_SETU_CLIENT_SECRET	api.setu.in	PMKVY skilling centers

💡 Note: Remotive.io is also used but requires no API key.

▶️ Running the Application
bash
Copy code
uvicorn main:app --reload
Then open in your browser:

Web UI: http://localhost:8000/

Swagger Docs: http://localhost:8000/docs

📡 API Usage
🔸 Endpoint
POST /recommend

🔸 Example Request
json
Copy code
{
  "query": "Sir, main Rampur gaon se hu, Bareilly ke paas. 12th pass kiya hai aur computer thoda bahut aata hai. Koi kaam dilwa do."
}
🔸 Example Response
json
Copy code
{
  "structured_query": {
    "skills": ["Data Entry", "Basic Computer", "Back Office"],
    "locations": ["Bareilly", "Rampur"],
    "experience_level": "entry-level",
    "job_titles": ["Data Entry Operator", "Back Office Executive", "Computer Operator"],
    "search_keywords": [
      "data entry jobs near Bareilly",
      "12th pass jobs Rampur",
      "fresher computer operator jobs Bareilly"
    ]
  },
  "total_jobs_found": 18,
  "best_matches": [
    {
      "title": "Data Entry Operator (Work From Home)",
      "company": "TechSolutions Pvt. Ltd.",
      "location": "Bareilly, Uttar Pradesh",
      "url": "https://www.adzuna.com/",
      "source": "Adzuna",
      "description_snippet": "We are hiring 12th pass freshers for data entry roles. Must know basic computer operations and MS Office..."
    }
  ],
  "other_jobs": [
    {
      "title": "MGNREGA Rural Work (Bareilly)",
      "company": "Govt. of India (MGNREGA)",
      "location": "Bareilly, UTTAR PRADESH",
      "url": "https://nrega.nic.in/",
      "source": "data.gov.in",
      "description_snippet": "Registered Workers: 54321. Job Cards Issued: 12345. This is statistical data."
    },
    {
      "title": "Find PMKVY Skilling Centers near Bareilly",
      "company": "Govt. of India (Skill India)",
      "location": "Bareilly",
      "url": "http://pmkvyofficial.org",
      "source": "api.setu.in",
      "description_snippet": "This API shows government-sponsored skill training centers (PMKVY)."
    }
  ]
}
💬 Summary
This project bridges the gap between job seekers and opportunities using:

🚀 FastAPI + LangChain + Groq

🌍 9+ Job & Government APIs

🧠 Intelligent Natural Language Understanding

Perfect for creating inclusive, AI-powered employment discovery tools.