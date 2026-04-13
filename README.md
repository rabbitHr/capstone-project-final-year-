# Khetra Mitra - Smart Agriculture Assistant

Khetra Mitra is an AI-powered agriculture platform designed to assist farmers in Punjab, India. It provides crop yield predictions, intelligent farming advice, government scheme matching, labour/job management, and multilingual voice support.

Built as a capstone project for LPU CAP-463.

---

## Architecture Diagram

```
+------------------------------------------------------------------+
|                        CLIENT (Browser)                          |
|                                                                  |
|  +---------------------------+  +-----------------------------+  |
|  |     capstone.html         |  |   User Interactions         |  |
|  |  (Single Page Frontend)   |  |                             |  |
|  |                           |  |  - Text Chat / Voice Input  |  |
|  |  HTML + CSS + JavaScript  |  |  - Crop Yield Prediction    |  |
|  |  Fetch API (REST calls)   |  |  - Crop Recommendation      |  |
|  |  Web Audio API (voice)    |  |  - Govt Scheme Matching     |  |
|  +---------------------------+  |  - Job Board (Post/Browse)  |  |
|                                 |  - Farmer/Labour Register   |  |
|                                 +-----------------------------+  |
+-------------------------------+----------------------------------+
                                |
                          HTTP / REST
                          JSON + JWT
                                |
+-------------------------------v----------------------------------+
|                     FLASK BACKEND (app.py)                       |
|                                                                  |
|  +-------------------+  +--------------------+  +--------------+ |
|  |   Auth Module     |  |   API Endpoints    |  |   Serving    | |
|  |                   |  |                    |  |              | |
|  | /api/register     |  | /api/chat          |  | / (frontend) | |
|  | /api/login        |  | /api/voice         |  +--------------+ |
|  | JWT Token Mgmt    |  | /api/predict       |                   |
|  +-------------------+  | /api/recommend-crop|                   |
|                         | /api/schemes       |                   |
|  +-------------------+  | /api/tts           |                   |
|  |  Data Module      |  | /api/jobs          |                   |
|  |                   |  | /api/farmer/register                   |
|  | Farmer CRUD       |  | /api/labour/register                  |
|  | Labour CRUD       |  | /api/chat/history  |                   |
|  | Job CRUD          |  +--------------------+                   |
|  | Chat History      |                                           |
|  | Predictions       |                                           |
|  +-------------------+                                           |
+--------+--------------------------+------------------------------+
         |                          |
         v                          v
+--------+---------+  +-------------+---------------------------+
|    SQLite DB     |  |        AI SERVICE LAYER                 |
| (khetra_mitra.db)|  |        (ai_services.py)                 |
|                  |  |                                         |
|  Tables:         |  |  +----------------------------------+  |
|  - User          |  |  |        Groq Cloud API            |  |
|  - Farmer        |  |  |   (LLaMA 3.3-70B Versatile)      |  |
|  - Labour        |  |  |                                  |  |
|  - Job           |  |  |  - chat_with_ai()                |  |
|  - Prediction    |  |  |  - predict_crop_yield()          |  |
|  - ChatHistory   |  |  |  - recommend_crop()              |  |
|  +---------------+  |  |  - match_government_schemes()    |  |
|  | ORM: Flask-   |  |  +----------------------------------+  |
|  | SQLAlchemy    |  |                                         |
|  | (models.py)   |  |  +----------------------------------+  |
|  +---------------+  |  |     Groq Whisper API              |  |
+------------------+  |  |   (whisper-large-v3)              |  |
                      |  |                                  |  |
                      |  |  - transcribe_audio()  (STT)     |  |
                      |  +----------------------------------+  |
                      |                                         |
                      |  +----------------------------------+  |
                      |  |      Sarvam AI API               |  |
                      |  |    (Bulbul v3 Model)             |  |
                      |  |                                  |  |
                      |  |  - text_to_speech_sarvam() (TTS) |  |
                      |  |  - 11 Indian languages supported |  |
                      |  +----------------------------------+  |
                      +-----------------------------------------+
```

---

## Architecture Explanation

### 1. Client Layer (Frontend)

The frontend is a **single-page HTML application** (`capstone.html`) that runs entirely in the browser. It uses vanilla HTML, CSS, and JavaScript with the Fetch API for making REST calls to the backend. The Web Audio API is used to capture voice input from the user's microphone. No frontend framework is used -- everything is self-contained in one file.

### 2. Flask Backend (app.py)

The backend is built with **Flask** and serves as the central API server. It has three logical modules:

- **Auth Module** -- Handles user registration and login using JWT (JSON Web Tokens) via `flask-jwt-extended`. Passwords are hashed with Werkzeug's security utilities. Tokens are valid for 7 days.
- **API Endpoints** -- RESTful routes for all features: AI chat, voice input, crop yield prediction, crop recommendation, government scheme matching, text-to-speech, job posting/browsing, and farmer/labour registration.
- **Data Module** -- Manages CRUD operations for all database entities (farmers, labourers, jobs, predictions, chat history).

Flask also serves the frontend HTML file directly from the root (`/`) route, so no separate web server is needed during development.

### 3. Database Layer (SQLite + Flask-SQLAlchemy)

The application uses **SQLite** as the database (`khetra_mitra.db`), accessed through **Flask-SQLAlchemy** ORM. The data models are defined in `models.py` and include six tables:

| Table | Purpose |
|-------|---------|
| `User` | Authentication credentials and roles (farmer/labour/employer) |
| `Farmer` | Farmer profiles with village, phone, and land size |
| `Labour` | Labour profiles with work type, location, experience, and rating |
| `Job` | Job listings with district, wage, and experience requirements |
| `Prediction` | Stored crop yield prediction results and AI analysis |
| `ChatHistory` | Conversation logs with language and voice/text flag |

### 4. AI Service Layer (ai_services.py)

This is the intelligence layer of the application, integrating three external AI APIs:

- **Groq Cloud API (LLaMA 3.3-70B Versatile)** -- Powers the core AI features:
  - `chat_with_ai()` -- General farming advice chatbot with multilingual support (English, Hindi, Punjabi)
  - `predict_crop_yield()` -- Analyzes farm parameters (area, rainfall, fertilizer, pesticide) and predicts yield in quintals
  - `recommend_crop()` -- Suggests top 3 crops based on district, season, soil type, and land size
  - `match_government_schemes()` -- Matches farmer profiles to relevant Indian government schemes (PM Kisan, PMFBY, eNAM, etc.)

- **Groq Whisper API (whisper-large-v3)** -- Speech-to-text transcription for voice input, enabling farmers to speak queries instead of typing

- **Sarvam AI (Bulbul v3)** -- Text-to-speech conversion supporting 11 Indian languages. Converts AI responses to spoken audio so farmers can listen to advice in their native language

### Data Flow

1. **Text Chat**: User types message -> Frontend sends POST to `/api/chat` -> Backend calls `chat_with_ai()` via Groq API -> Response returned as text + optional TTS audio
2. **Voice Chat**: User records audio -> Frontend sends audio file to `/api/voice` -> Whisper transcribes to text -> `chat_with_ai()` generates response -> TTS converts to audio -> All three (transcription, text response, audio) returned
3. **Crop Prediction**: User enters farm parameters -> POST to `/api/predict` -> Groq LLM analyzes and predicts yield -> Result stored in DB and returned
4. **Job Board**: Employers post jobs via `/api/jobs` POST -> Labourers browse via `/api/jobs` GET with optional district filter

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Frontend | HTML, CSS, JavaScript (vanilla) |
| Backend | Python, Flask |
| Database | SQLite, Flask-SQLAlchemy |
| Authentication | JWT (flask-jwt-extended) |
| AI/LLM | Groq API (LLaMA 3.3-70B) |
| Speech-to-Text | Groq Whisper (whisper-large-v3) |
| Text-to-Speech | Sarvam AI (Bulbul v3) |
| HTTP Client | httpx |
| CORS | flask-cors |

---

## Setup

### Prerequisites

- Python 3.9+
- Groq API key (get from [console.groq.com](https://console.groq.com))
- Sarvam AI API key (optional, for TTS)

### Installation

```bash
# Clone the repository
git clone <repo-url>
cd capstone-project

# Install dependencies
cd backend
pip install -r requirements.txt

# Create .env file
cat > .env << EOF
GROQ_API_KEY=your_groq_api_key_here
SARVAM_API_KEY=your_sarvam_api_key_here
JWT_SECRET_KEY=your_secret_key_here
EOF

# Run the server
python app.py
```

The application will be available at `http://localhost:5000`.

---

## Project Structure

```
capstone-project/
├── capstone.html              # Frontend (single-page application)
├── backend/
│   ├── app.py                 # Flask server and API routes
│   ├── ai_services.py         # AI integrations (Groq, Sarvam)
│   ├── models.py              # SQLAlchemy database models
│   ├── requirements.txt       # Python dependencies
│   └── instance/
│       └── khetra_mitra.db    # SQLite database (auto-created)
├── .gitignore
└── README.md
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/register` | Register a new user |
| POST | `/api/login` | Login and get JWT token |
| POST | `/api/farmer/register` | Register farmer profile |
| POST | `/api/labour/register` | Register labour profile |
| POST | `/api/jobs` | Post a new job |
| GET | `/api/jobs` | List open jobs (optional `?district=` filter) |
| POST | `/api/chat` | Send message to AI chatbot |
| POST | `/api/voice` | Send voice audio for transcription + AI response |
| POST | `/api/predict` | Predict crop yield |
| POST | `/api/recommend-crop` | Get crop recommendations |
| POST | `/api/schemes` | Match government schemes |
| POST | `/api/tts` | Convert text to speech |
| GET | `/api/chat/history` | Get recent chat history |
