# Changelog

All notable changes to this project will be documented in this file.  
---

## [v0.1.0] - 2025-10-15
### Added
- **Main.py**
  - Created main application entry point coordinating API and sentiment analysis components.
  - Implemented comment fetching, sentiment processing, and terminal output for analysis results.
  - Integrated dependency imports for modular design via package initialization (`__init__.py`).

- **src/backend/YoutubeAPIHandler.py**
  - Added `APIHandler` class to manage YouTube Data API v3 interactions.
  - Implemented `get_comments()` method to fetch top-level comments with error handling.
  - Added `APIError` exception class for structured API failure management.

- **src/backend/sentiment_analyzer.py**
  - Introduced `SentimentAnalyzer` class leveraging **BERT (DistilBERT)** using HuggingFace Transformers.
  - Implemented a **Singleton-like model initialization** to load the sentiment pipeline only once, improving performance and reducing redundant memory use.
  - Added `analyze()` method for single-text sentiment prediction.

### Architecture
- Initial modular backend structure under `src/backend/` for clean separation of concerns:
  - **APIHandler** for external data retrieval.
  - **SentimentAnalyzer** for NLP model inference.
- Used a lightweight main controller script (`Main.py`) for dependency orchestration.

### Notes
- This version represents the **first working prototype** capable of retrieving YouTube comments and performing sentiment analysis using BERT.
- Designed for extensibility: future versions will add modular logging, error handling, and persistent storage (e.g., database integration).
- Next goal: Refactor into a Layered Architecture - Data / Service / App separation

---


## [v0.1.1] - 2025-10-19
### Added
- models.py
  - SentimentLabel class that contains postive, negative, or neural enums labels.
  - Sentiment data class containing label and confidence variables. 3 addition methods (is_positive, is_neutral, and is_confident) to determine the label and confidence of the analysis.
  - Comment data class containing id, author, text, and sentiment variables. Also the analyze_sentiment method which will be moved to a different layer in the future. This method analyses a comment.
  -  Video data class containing id and comemnts variables. An add_comment and get_sentiment_distribution method that adds a comment to the list of comments associated with said video. The get_sentiment_distribution method will also be moved to a different layer in the future. 

- main.py
  - removed tensorflow warnings from appearing in the terminal.

### Notes
- Next goal: Contuine to refactor into a Layered Architecture - Data / Service / App separation. Also move business logic methods out of the data layer.
