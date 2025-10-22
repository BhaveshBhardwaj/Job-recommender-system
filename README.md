# Job Recommendation System

A FastAPI-based job recommendation system that extracts skills from user queries and finds relevant jobs from multiple platforms like LinkedIn and Naukri.com.

## Features

- Skill extraction from natural language queries
- Multi-platform job search (LinkedIn, Naukri.com)
- Location-based job filtering
- Experience-based filtering
- Asynchronous job scraping
- REST API interface

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Download the spaCy model:
```bash
python -m spacy download en_core_web_sm
```

4. Create a `.env` file with your credentials (if needed):
```
LINKEDIN_API_KEY=your_api_key
NAUKRI_API_KEY=your_api_key
```

## Running the Application

1. Start the FastAPI server:
```bash
uvicorn app.main:app --reload
```

2. Access the API documentation at `http://localhost:8000/docs`

## API Usage

### Recommend Jobs

```bash
POST /recommend-jobs
```

Request body:
```json
{
    "query": "Looking for Python developer position with experience in Django and FastAPI",
    "location": "Bangalore",
    "age": 25,
    "experience": 3
}
```

Response:
```json
[
    {
        "title": "Senior Python Developer",
        "company": "Example Corp",
        "location": "Bangalore",
        "description": "Job description...",
        "skills_required": ["Python", "Django", "FastAPI"],
        "source": "LinkedIn",
        "apply_link": "https://..."
    }
]
```

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a new Pull Request