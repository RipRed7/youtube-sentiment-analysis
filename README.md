# YouTube Sentiment Analyzer

A full-stack web application that analyzes YouTube video comments using AI-powered sentiment analysis with BERT transformers.

## Overview

This application uses a hybrid architecture where Streamlit handles the user interface and OAuth authentication, while FastAPI manages video analysis and database operations. Users can analyze YouTube videos to understand the sentiment distribution of comments and identify top negative feedback.

Currently the application is not verified by Google so my application authentcation tokens have been disabled. Verifing the application may take months since the Youtube API im using is listed as one of Google's most sensetive API's. This process could not be completed in time for the project to be turned in as my token was not disabled until a week before the deadline. Luckily it wasn't disabled during the live demo but this is something I cannot fix without changing my architecture to avoid using the Google OAuth token, and I currently do not have the time to refactor everyone. I just wanted to let you know, so the error you will see when running an analysis is due to that reason, I have tried many fixes and none worked. I apologize for this. 


## Features

- **AI-Powered Analysis**: Uses BERT (RoBERTa) transformer model for accurate sentiment classification
- **OAuth Integration**: Secure Google OAuth 2.0 authentication
- **Visual Analytics**: Interactive charts showing sentiment distribution
- **Comment Insights**: Identifies and displays top negative comments
- **Analysis History**: Tracks previously analyzed videos with caching
- **Batch Processing**: Efficient analysis of large comment sets

## Tech Stack

**Frontend**: Streamlit, Plotly  
**Backend**: FastAPI, Uvicorn  
**Database**: PostgreSQL (Neon)  
**ML Model**: Transformers (RoBERTa-based BERT)  
**APIs**: YouTube Data API v3, Google OAuth 2.0  
**ORM**: SQLAlchemy  

## Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd youtube-sentiment-analyzer
```

2. **Install dependencies**
```bash
pip install -r requirements-fastapi.txt
```

3. **Set up environment variables**
Create a `.env` file:
```env
DATABASE_URL=postgresql://user:password@host:port/database
GOOGLE_CLIENT_ID=your_client_id
GOOGLE_CLIENT_SECRET=your_client_secret
FASTAPI_URL=http://localhost:8000
STREAMLIT_REDIRECT_URI=http://localhost:8501
```

4. **Initialize the database**
```bash
python -c "from src.database.db import init_db; init_db()"
```

## Usage

1. **Start the FastAPI backend**
```bash
python main.py
```

2. **Start the Streamlit frontend** (in a new terminal)
```bash
streamlit run Youtube-sentiment-app.py
```

3. **Access the application**
- Streamlit UI: http://localhost:8501
- FastAPI docs: http://localhost:8000/docs

## Running Tests

```bash
# Install test dependencies
pip install pytest pytest-cov

# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html
```

## Project Structure

```
├── main.py                          # FastAPI backend
├── Youtube-sentiment-app.py         # Streamlit frontend
├── src/
│   ├── backend/
│   │   ├── api/                     # YouTube API integration
│   │   └── analyzers/               # BERT sentiment analyzer
│   ├── database/                    # Database models and operations
│   ├── config/                      # Configuration constants
│   └── utils/                       # Logging and exceptions
├── tests/                           # Unit and integration tests
└── schema.sql                       # Database schema
```

## Key Components

**Comment Fetcher**: Retrieves comments from YouTube API and handles API quota limits and disabled comments gracefully.

**BERT Analyzer**: Implements sentiment classification using the RoBERTa model with batch processing for efficiency and singleton pattern to avoid reloading the model.

**Database Layer**: Uses SQLAlchemy ORM for PostgreSQL operations with models for users, videos, comments, and analyses, plus CRUD operations with proper relationship handling.

**Hybrid Architecture**: Streamlit manages UI and OAuth while FastAPI handles computationally intensive analysis and database operations for better separation of concerns.

## Code Organization

The codebase follows a clean architecture pattern with clear separation between layers. The `src/backend` directory contains business logic for API integration and sentiment analysis. The `src/database` directory manages all data persistence with ORM models and CRUD operations. Shared utilities like logging and custom exceptions are centralized in `src/utils`. Configuration values are extracted to `src/config/constants.py` to eliminate magic numbers throughout the code.

## Challenges

**Model Loading**: The BERT model took a significant time to load on first use, I addressed by using a singleton pattern to load the model only once and reuse it multiple times to avoid constant loading. 

**API Rate Limits**: YouTube API has quota limits which could be reached if too many users were using the application at one. I mitigated this somewhat by implementing 24-hour analysis caching and comprehensive error handling for scenarios where the quota is exceeded.

**Large Comment Sets**: Videos with thousands of comments could take minutes to process, which is a good experience for the user. I solved this through batch processing that processed multiple comments at once. I also implemented request timeouts if the analysis did take too long to avoid excessive load times.

## Deployment

The application is configured for deployment on Render (FastAPI) and Streamlit Cloud (frontend). See `render.yaml` for FastAPI deployment configuration and `.devcontainer` for GitHub Codespaces support.

