# AutoResuAgent Web Application

A full-stack web application that allows users to paste raw job postings and resumes (from LinkedIn, PDFs, etc.) and automatically generate tailored resumes using AI.

## Architecture

### Backend (`server.py`)
- **FastAPI** REST API with CORS support
- **LLM-powered parsing** via `DataParser` class
- **Agent execution** using existing `AgentExecutor`
- Endpoints:
  - `POST /parse/job` - Parse raw job text to YAML
  - `POST /parse/resume` - Parse raw resume text to JSON
  - `POST /generate` - Generate tailored resume

### Frontend (`frontend/`)
- **React** + **Vite** for fast development
- **Tailwind CSS** for modern, responsive UI
- Features:
  - "Magic Import" buttons for auto-parsing raw text
  - Real-time structured data preview
  - Download generated results

### Core Logic (`src/parsers.py`)
- `DataParser` class uses OpenAI LLM to extract structured data
- Converts unstructured text to valid YAML/JSON schemas
- Validates against Pydantic models

## Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- OpenAI API key

### 1. Install Backend Dependencies

```bash
# Install web-specific dependencies
pip install -r requirements-web.txt

# Make sure core dependencies are installed
pip install -r requirements.txt
```

### 2. Set OpenAI API Key

```bash
# Windows (PowerShell)
$env:OPENAI_API_KEY="sk-your-key-here"

# Windows (CMD)
set OPENAI_API_KEY=sk-your-key-here

# Linux/Mac
export OPENAI_API_KEY=sk-your-key-here
```

### 3. Start Backend Server

```bash
python server.py
```

The backend will start at `http://localhost:8000`

### 4. Install Frontend Dependencies

```bash
cd frontend
npm install
```

### 5. Start Frontend Dev Server

```bash
npm run dev
```

The frontend will start at `http://localhost:3000`

### 6. Open in Browser

Navigate to `http://localhost:3000` and start using the app!

## Usage Guide

### Step 1: Paste Job Posting
1. Copy a job posting from LinkedIn, company careers page, etc.
2. Paste the raw text into the left text area
3. Click "✨ Magic Import" to auto-convert to structured YAML

### Step 2: Paste Resume
1. Copy your resume from LinkedIn profile, PDF, etc.
2. Paste the raw text into the right text area
3. Click "✨ Magic Import" to auto-convert to structured JSON

### Step 3: Generate
1. Review the structured YAML/JSON (you can manually edit if needed)
2. Click "🚀 Generate Tailored Resume"
3. Wait for the AI to generate your tailored content

### Step 4: Download
1. Review the generated cover letter and bullets
2. Click "Download" to save as a text file
3. Use the content in your actual resume/application!

## API Documentation

Once the backend is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## File Structure

```
autoresuagent/
├── server.py                    # FastAPI backend server
├── src/
│   └── parsers.py              # DataParser class (LLM-powered extraction)
├── frontend/
│   ├── src/
│   │   ├── App.jsx             # Main React component
│   │   ├── main.jsx            # React entry point
│   │   └── index.css           # Tailwind CSS
│   ├── index.html              # HTML template
│   ├── package.json            # Node dependencies
│   ├── vite.config.js          # Vite configuration
│   └── tailwind.config.js      # Tailwind configuration
├── data/
│   └── temp/                   # Temporary storage for uploaded files
└── requirements-web.txt        # Web app dependencies
```

## Development

### Backend Hot Reload
The server runs with `reload=True`, so changes to `server.py` or `src/` will auto-reload.

### Frontend Hot Reload
Vite provides instant HMR (Hot Module Replacement) for React components.

### Debugging
- Backend logs: Check the terminal running `server.py`
- Frontend errors: Check browser console (F12)
- API requests: Use Network tab in browser DevTools

## Production Deployment

### Backend
```bash
# Use production ASGI server
uvicorn server:app --host 0.0.0.0 --port 8000 --workers 4
```

### Frontend
```bash
cd frontend
npm run build
# Serve the 'dist' folder with nginx or your preferred static host
```

### Environment Variables
Create a `.env` file:
```
OPENAI_API_KEY=sk-your-key-here
```

## Troubleshooting

### "Parser not initialized" error
- Ensure `OPENAI_API_KEY` environment variable is set
- Check backend terminal for startup errors

### CORS errors
- Ensure backend is running on port 8000
- Check CORS configuration in `server.py`

### Frontend not connecting to backend
- Verify `API_BASE_URL` in `App.jsx` matches your backend URL
- Ensure backend is running and accessible

### Parsing errors
- Check that raw text has sufficient information
- Try manually editing the YAML/JSON if parsing fails
- Verify OpenAI API key has sufficient credits

## Tech Stack

**Backend:**
- FastAPI 0.109.0
- Uvicorn 0.27.0
- OpenAI GPT-4o-mini
- Pydantic for validation

**Frontend:**
- React 18
- Vite 5
- Tailwind CSS 3
- Modern ES6+ JavaScript

**AI/ML:**
- OpenAI API (parsing + generation)
- Sentence-BERT (semantic retrieval)
- FAISS (vector search)

## License

Same as AutoResuAgent main project.
