# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Application Overview

This is a social media research template application that studies meme-based alternatives to aggressive online comments. The system analyzes user comments for personal attacks and negative emotions, then recommends appropriate memes as communication alternatives. It includes comprehensive user activity tracking and survey collection for research purposes.

## Development Commands

### Run the Application
```bash
python web.py
```
- Main Flask app runs on `http://127.0.0.1:5000`
- Entry point: `/` (input.html for user registration)
- Admin data viewer: `/data-viewer`

### Testing
This project uses manual testing with individual test files:
```bash
# Test core functionality
python test_complete_functionality.py
python test_flask_app.py
python test_excel_structure.py

# Test AI integration
python test_claude.py
python test_survey_api.py

# Test meme recommendation system
python test_meme_matching.py
python test_cosine_similarity.py

# Test data management
python test_comment_manager_memes.py
python test_sender_data.py
```

### No formal testing framework is used - tests are standalone Python scripts that print results to console.

## Core Architecture

### Data Flow Pattern
```
User Input → Emotion Analysis (OpenAI/Claude) → Meme Recommendation → Survey Collection → Excel/JSON Storage
```

### Key Components

**Backend (Python/Flask)**
- `web.py` - Main Flask application with REST API endpoints
- `comment_manager.py` - Handles news posts, comments, and meme recommendations
- `excel_manager.py` - Thread-safe Excel operations for user activity tracking
- `claude_sentence_emotion.py` - Advanced emotion analysis using Claude API
- `config.py` - Configuration for API keys and file paths

**Frontend (HTML/CSS/JavaScript)**
- `templates/` - Jinja2 templates for different user roles
- `static/js/` - Vanilla JavaScript for user interactions
- `static/css/` - Responsive styling with CSS Grid/Flexbox

**Data Storage**
- `user_data.xlsx` - Multi-sheet Excel file for user activity tracking
- `meme_survey_data.json` / `receiver_survey_data.json` - Survey responses
- `static/Comments_Meme_Similarity.xlsx` - Pre-computed meme-comment relationships

### API Architecture

All API endpoints are prefixed with `/api/`:
- `/api/analyze-comment` - Real-time emotion analysis and meme recommendation
- `/api/submit-meme-survey` / `/api/submit-receiver-survey` - Survey data collection
- `/api/log-activity` - User activity tracking
- `/api/detect-personal-attack` - Personal attack detection

## Important Implementation Details

### Emotion Analysis System
- **Primary**: OpenAI GPT-4o-mini for real-time analysis
- **Secondary**: Claude 3.5 Sonnet for advanced analysis with confidence scores
- **Classifications**: contempt, anger, disgust with numerical confidence values
- **Process**: Personal attack detection → Emotion classification → Meme recommendation

### Meme Recommendation Algorithm
- Uses cosine similarity between user emotion vectors and pre-classified meme emotions
- Three-tier recommendation system (high/medium/low similarity)
- Database contains 50 memes with pre-computed emotion profiles
- Recommendations stored in Excel for research analysis

### User Role System
- **Sender**: Analyzes aggressive comments and selects memes as alternatives
- **Receiver**: Views recommended memes and evaluates their effectiveness
- Content filtering based on file naming conventions (_1/_2 for senders, _3/_4 for receivers)

### Data Collection for Research
- Comprehensive activity logging in Excel with three worksheets:
  - `User_Activity`: General user actions
  - `Sender_Actions`: Comment analysis and meme selection
  - `Receiver_Actions`: Meme viewing and evaluation
- Survey responses in JSON format for detailed analysis
- Thread-safe operations for concurrent user access

## Configuration Requirements

### Required API Keys (in config.py)
- `OPENAI_API_KEY` - For primary emotion analysis
- `CLAUDE_API_KEY` - For advanced analysis features
- Firebase configuration (partially implemented)

### Required Assets Structure
```
static/
├── news/           # 16 news images categorized by intentionality/severity
├── meme_50/        # 50 meme images for recommendations
├── contempt/       # Emotion-specific meme folders
├── anger/
├── disgust/
└── Comments_Meme_Similarity.xlsx  # Pre-computed similarity database
```

### Content Distribution
- Sender pages show files ending with _1.png and _2.png
- Receiver pages show files ending with _3.png and _4.png
- This ensures appropriate content filtering for different user roles

## Language and Localization
- Primary language: Traditional Chinese
- Comments and UI text are in Chinese
- AI prompts are structured for Chinese language processing
- Some variable names and documentation in English for development

## Security and Privacy
- No user authentication - uses anonymous user IDs
- API keys should be environment variables in production
- Excel files contain research data and should be backed up regularly
- Thread-safe file operations prevent data corruption

## Development Notes
- Excel-based storage limits scalability but suits research needs
- Manual testing approach - run test files individually
- Modular design allows independent development of AI, UI, and data components
- Survey validation ensures data quality for research analysis