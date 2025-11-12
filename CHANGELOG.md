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
- **models.py**
  - SentimentLabel class that contains positive, negative, or neutral enum labels.
  - Sentiment data class containing label and confidence variables. 3 addition methods (is_positive, is_neutral, and is_confident) to determine the label and confidence of the analysis.
  - Comment data class containing id, author, text, and sentiment variables. Also the analyze_sentiment method which will be moved to a different layer in the future. This method analyses a comment.
  - Video data class containing id and comments variables. An add_comment and get_sentiment_distribution method that adds a comment to the list of comments associated with said video. The get_sentiment_distribution method will also be moved to a different layer in the future.

- **main.py**
  - Removed tensorflow warnings from appearing in the terminal.

### Notes
- Next goal: Continue to refactor into a Layered Architecture - Data / Service / App separation. Also move business logic methods out of the data layer.


## [v0.1.2] - 2025-10-21
### Added
- **Repository Layer (src/repositories/)**
  - Created `ICommentRepository` interface defining the contract for comment data access operations (add, get_by_id, update, get_all, delete).
  - Implemented `InMemoryCommentRepo` as a concrete in-memory implementation using a dictionary for storage with auto-incrementing ID generation.
  - Added `__init__.py` to export repository components for clean imports.

- **Service Layer (src/services/)**
  - Created `CommentService` class to encapsulate all comment-related business logic.
  - Implemented `fetch_and_store_comments()` method to coordinate fetching from API and storing in repository.
  - Implemented `analyze_comment_sentiment()` method to analyze individual comments and persist results.
  - Implemented `analyze_all_comments()` method for batch sentiment analysis.
  - Implemented `get_sentiment_distrib()` method to calculate sentiment distribution across all comments.
  - Added comment retrieval methods: `get_comment()` and `get_all_comments()`.

- **Backend API Layer (src/backend/api/)**
  - Created `ICommentFetcher` interface defining contract for comment fetching implementations.
  - Refactored YouTube API handler into `YoutubeCommentFetcher` implementing the interface.
  - Moved API-specific logic out of the main application entry point.

- **Backend Analyzer Layer (src/backend/analyzers/)**
  - Created `ISentimentAnalyzer` interface for sentiment analysis implementations.
  - Refactored sentiment analyzer into `BertSentimentAnalyzer` implementing the interface.
  - Maintained singleton-like pattern for BERT model initialization.

### Changed
- **main.py**
  - Refactored to use dependency injection pattern with service layer.
  - Removed direct API and analyzer instantiation in favor of clean layered architecture.
  - Updated to use `CommentService` as the single point of interaction for all comment operations.
  - Improved separation of concerns: main now only handles orchestration and display.

- **models.py**
  - Removed `analyze_sentiment()` method from `Comment` class (moved to service layer).
  - Removed `get_sentiment_distribution()` method from `Video` class (moved to service layer).
  - Domain models now focus solely on data representation.

### Architecture
- Successfully transitioned from monolithic structure to Layered Architecture.
- Established clear separation: Domain → Repository → Service → Application layers.
- Implemented Dependency Inversion Principle through interfaces (ICommentRepository, ICommentFetcher, ISentimentAnalyzer).
- Business logic now properly resides in Service layer rather than Domain models.
- Code now follows SOLID principles with clear interface contracts and dependency injection.
- Project structure now supports easy testing through interface mocking.

### Notes
- Successfully completed the layered architecture refactoring goal from v0.1.1.
- Business logic properly extracted from domain layer into service layer.
- Next goal: Add comprehensive error handling, logging infrastructure, and unit tests for each layer.

## [v0.1.3] - 2025-11-12
### Added
- **Logging Module (src/utils/logger.py)**
  - Created `AppLogger` class with singleton pattern for centralized logging across the application.
  - Implemented automatic configuration loading from JSON file with fallback to basic config.
  - Added logging methods: `debug()`, `info()`, `warning()`, `error()`, `critical()`, and `exception()` with traceback support.
  - Created `get_logger()` function for easy logger instance retrieval.

- **Logging Configuration (src/utils/logging_configs/config.json)**
  - Configured multiple formatters: simple (console), detailed (files), and JSON format support.
  - Set up rotating file handlers with 10MB max size and 5 backup files.
  - Created separate log files: `logs/app.log` (all logs) and `logs/errors.log` (errors only).
  - Configured logger hierarchy with `sentiment_analyzer` as application logger.

- **Custom Exception Hierarchy (src/utils/exceptions.py)**
  - Created base `SentimentnAnalyzerError` exception with structured error details.
  - Added API-specific exceptions: `APIQuotaExceededError`, `APIConnectionError`, `VideoNotFoundError`, `CommentsDisabledError`.
  - Added analysis exceptions: `ModelLoadError`, `AnalysisFailedError`.
  - Added repository exceptions: `CommentNotFoundError`.
  - Added validation exceptions: `InvalidVideoIdError`, `InvalidURLError`.
  - All exceptions now include contextual details and user-friendly suggestions.

- **Streamlit Web Application (Youtube-sentiment-app.py)**
  - Created web-based UI replacing command-line interface in main.py.
  - Implemented URL input field with support for multiple YouTube URL formats.
  - Added real-time progress indicators for comment fetching and analysis.
  - Created visual sentiment distribution display with metrics and bar chart.
  - Integrated comprehensive error handling with user-friendly error messages.
  - Added analyzer caching using `@st.cache_resource` for improved performance.

### Changed
- **src/backend/api/youtube_comment_fetcher.py**
  - Integrated comprehensive logging at all operational stages (initialization, fetch start, success, errors).
  - Enhanced error handling with specific HTTP status code detection (403, 404).
  - Added detailed error logging with status codes and error details.
  - Improved exception raising with proper exception types based on error scenarios.
  - Added critical-level logging for quota exceeded errors.

- **src/backend/analyzers/bert_sentiment_analyzer.py**
  - Added singleton logger at class level to avoid multiple logger instances.
  - Integrated logging for model loading, reuse, and analysis operations.
  - Added debug logging showing text previews and analysis results with confidence scores.
  - Implemented error handling with `ModelLoadError` for model loading failures.
  - Added empty text handling with warning logs and graceful fallback to neutral sentiment.
  - Fixed missing `return` statement in `analyze()` method.

- **src/services/comment_service.py**
  - Added logging throughout all service methods (initialization, fetch, analyze, retrieve).
  - Implemented progress logging every 10 comments during batch analysis.
  - Added success/failure counting and reporting for batch operations.
  - Enhanced error handling with proper exception raising (`CommentNotFoundError`, `AnalysisFailedError`).
  - Added detailed logging for sentiment distribution calculations.

- **src/repositories/commentRepository.py**
  - Integrated logging for all CRUD operations (add, update, get, delete).
  - Added debug logging for ID assignment and repository state (total count, remaining count).
  - Changed exception handling to use custom `CommentNotFoundError` instead of generic `ValueError`.
  - Added logging for both successful and failed operations.

- **src/utils/__init__.py**
  - Updated to export `AppLogger` and `get_logger` from logging module.
  - Updated to export all custom exception classes for easy access throughout application.

### Architecture
- Established centralized logging infrastructure across all application layers.
- Implemented consistent error handling with custom exception hierarchy.
- Transitioned from command-line interface to web-based Streamlit application.
- Added observability through comprehensive logging at debug, info, warning, error, and critical levels.
- Logging follows single responsibility principle with logger singleton pattern.

### Notes
- Successfully implemented comprehensive logging infrastructure goal from v0.1.2.
- All layers (API, Analyzer, Service, Repository) now have full logging coverage.
- Exception handling significantly improved with specific exception types and detailed error messages.
- Web interface provides better user experience compared to terminal-based application.
- Log files rotate automatically to prevent disk space issues.
- Next goals:   
  - Implement unit tests for each layer (Domain, Repository, Service, API, Analyzer)
  - Add integration tests for end-to-end workflows
  - Deploy application to Streamlit Cloud for public access
