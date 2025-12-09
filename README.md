# AutoResuAgent - AI-Powered Resume Tailoring System

AutoResuAgent is an intelligent resume tailoring system that uses advanced NLP and LLMs to automatically customize resumes for specific job postings. It analyzes job descriptions, extracts relevant experiences from your resume, and generates tailored bullets and cover letters optimized for ATS systems.

## 🎥 Demo Video

Watch AutoResuAgent in action: [Click here to watch ](https://drive.google.com/file/d/13ZppnzB_Y3PIcnT7qRne24_UrsUD9J0c/view?usp=sharing)
## Features

- **Smart Parsing**: Paste raw job postings and resumes - AI automatically structures the data
- **Semantic Matching**: Uses Sentence-BERT + FAISS for intelligent experience retrieval
- **LLM Generation**: GPT-4o-mini generates tailored bullets and cover letters
- **LaTeX Output**: Professional LaTeX source code for resume and cover letter
- **Change Summary**: Detailed explanation of how your resume was tailored
- **Modern UI**: Clean, professional interface with real-time status updates

## Prerequisites

- **Docker** (recommended): Docker Desktop for Windows/Mac
- **OR Manual Setup**:
  - Python 3.10 or higher
  - Node.js 18 or higher
  - OpenAI API Key

## Quick Start (Docker - Recommended)

This is the easiest way to run AutoResuAgent on Windows and Mac (including M-series).

### Step 1: Clone the Repository

```bash
git clone https://github.com/yourusername/autoresuagent.git
cd autoresuagent
```

### Step 2: Set Your OpenAI API Key

**CRITICAL**: The application requires an OpenAI API key to function.

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and add your OpenAI API key:
   ```bash
   # Windows (Notepad)
   notepad .env

   # Mac/Linux
   nano .env
   ```

3. Replace `sk-your-openai-api-key-here` with your actual API key:
   ```
   OPENAI_API_KEY=sk-proj-YOUR_ACTUAL_KEY_HERE
   ```

   **Get an API key**: https://platform.openai.com/api-keys

### Step 3: Start the Application

```bash
docker-compose up --build
```

**What happens**:
- Backend starts on `http://localhost:8000`
- Frontend starts on `http://localhost:3000`
- Both services are automatically connected via Docker network

### Step 4: Access the Application

Open your browser and navigate to:
```
http://localhost:3000
```

### Step 5: Stop the Application

Press `Ctrl+C` in the terminal, then:
```bash
docker-compose down
```

---

## Manual Setup (Without Docker)

If you prefer to run the application without Docker:

### Backend Setup

1. **Install Python Dependencies**

   ```bash
   # Create virtual environment (recommended)
   python -m venv venv

   # Activate virtual environment
   # Windows:
   venv\Scripts\activate
   # Mac/Linux:
   source venv/bin/activate

   # Install dependencies
   pip install -r requirements.txt
   pip install -r requirements-web.txt
   ```

2. **Set Environment Variable**

   ```bash
   # Windows (PowerShell)
   $env:OPENAI_API_KEY="sk-your-key-here"

   # Windows (CMD)
   set OPENAI_API_KEY=sk-your-key-here

   # Mac/Linux
   export OPENAI_API_KEY=sk-your-key-here
   ```

3. **Start Backend Server**

   ```bash
   python server.py
   ```

   Backend will run at `http://localhost:8000`

### Frontend Setup

1. **Install Node Dependencies**

   ```bash
   cd frontend
   npm install
   ```

2. **Start Development Server**

   ```bash
   npm run dev
   ```

   Frontend will run at `http://localhost:3000`

### Access the Application

Open your browser: `http://localhost:3000`

---

## Usage Guide

### 1. Prepare Your Inputs

- **Job Posting**: Copy the full text from LinkedIn, Indeed, or company website
- **Resume**: Copy from LinkedIn profile, PDF export, or text document

### 2. Parse Job Posting

1. Paste the raw job posting text in the **left panel**
2. Click **"Auto-Parse"** to convert to structured YAML
3. Wait for the "Ready" badge

### 3. Parse Resume

1. Paste your resume text in the **right panel**
2. Click **"Auto-Parse"** to convert to structured JSON
3. Wait for the "Ready" badge

### 4. Generate Tailored Resume

1. Click **"Generate Tailored Resume"** (center button)
2. Wait 30-60 seconds for AI processing
3. View results in the success card

### 5. Review Output

The generated output includes:

- **Change Summary**: What was improved and why
- **Cover Letter**: Tailored plain text cover letter
- **Resume Bullets**: Optimized bullet points (3 tabs):
  - Resume Bullets (ready to use)
  - Resume LaTeX (copy and compile)
  - Cover Letter LaTeX (copy and compile)

### 6. Use LaTeX Output

1. Click the **"Resume LaTeX"** or **"Cover Letter LaTeX"** tab
2. Click **"Copy"** button
3. Paste into:
   - Local LaTeX editor (compile with `pdflatex`)
   - [Overleaf](https://www.overleaf.com/) (online LaTeX editor)
4. Compile to get professional PDF

---

## Troubleshooting

### Port Already in Use

**Problem**: `Error: Port 8000 (or 3000) is already in use`

**Solution**:
```bash
# Find and kill the process using the port

# Windows:
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Mac/Linux:
lsof -ti:8000 | xargs kill -9
```

Or change the port in `docker-compose.yml`:
```yaml
ports:
  - "8001:8000"  # Change 8000 to 8001
```

### Docker Build Fails

**Problem**: `Error: failed to solve with frontend dockerfile.v0`

**Solutions**:
1. Ensure Docker Desktop is running
2. Clear Docker cache:
   ```bash
   docker system prune -a
   docker-compose build --no-cache
   ```

### OpenAI API Error

**Problem**: `Error: OPENAI_API_KEY environment variable not set`

**Solutions**:
1. Check `.env` file exists and has the correct key
2. Restart Docker containers:
   ```bash
   docker-compose down
   docker-compose up
   ```
3. Verify API key at: https://platform.openai.com/api-keys

### Frontend Can't Connect to Backend

**Problem**: `Failed to parse job posting: NetworkError`

**Solutions**:
1. Ensure backend is running (`docker-compose ps` shows both services)
2. Check backend health: `http://localhost:8000/` (should show `{"status": "healthy"}`)
3. CORS is configured in `server.py` - check logs for errors

### Generation Takes Too Long

**Problem**: Request hangs or times out

**Solutions**:
1. Check backend logs: `docker-compose logs backend`
2. Verify OpenAI API credits: https://platform.openai.com/usage
3. The process typically takes 30-60 seconds - be patient

### M-Series Mac Issues

**Problem**: Docker build fails on Apple Silicon

**Solution**:
Docker images are multi-platform compatible, but ensure:
```bash
docker-compose build --platform linux/amd64
```

---

## Architecture

### Tech Stack

**Backend**:
- FastAPI (Python 3.11)
- OpenAI GPT-4o-mini (LLM)
- Sentence-BERT (embeddings)
- FAISS (vector search)
- Pydantic (validation)

**Frontend**:
- React 18
- Vite 5
- Tailwind CSS 3
- Modern Slate & Teal theme

**Infrastructure**:
- Docker & Docker Compose
- Nginx (frontend proxy)
- Uvicorn (ASGI server)

### Project Structure

```
autoresuagent/
├── src/                      # Backend source code
│   ├── agent/               # Agent executor & pipeline
│   ├── embeddings/          # Sentence-BERT encoder
│   ├── generators/          # Bullet & cover letter generators
│   ├── llm/                 # OpenAI client
│   ├── models/              # Pydantic schemas
│   └── parsers.py           # Raw text parsers
├── frontend/                # React frontend
│   ├── src/
│   │   ├── App.jsx         # Main component
│   │   └── index.css       # Tailwind styles
│   ├── Dockerfile          # Frontend container
│   └── nginx.conf          # Nginx config
├── data/                    # Job & resume data
│   ├── jobs/               # YAML job descriptions
│   ├── resumes/            # JSON candidate profiles
│   └── temp/               # Temporary files
├── server.py               # FastAPI server
├── Dockerfile              # Backend container
├── docker-compose.yml      # Multi-container orchestration
└── .env.example            # Environment template
```

---

## API Documentation

Once the backend is running, visit:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

### Endpoints

- `POST /parse/job` - Parse raw job text to YAML
- `POST /parse/resume` - Parse raw resume text to JSON
- `POST /generate` - Generate tailored resume

---

## Development

### Run Tests

```bash
# Backend tests
python -m pytest tests/

# Check code quality
python -m pylint src/
python -m mypy src/
```

### Hot Reload

- **Backend**: Auto-reloads on code changes (Uvicorn `--reload`)
- **Frontend**: Hot Module Replacement (Vite HMR)

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
```

---

## Security Notes

- **Never commit `.env` file** - It contains your API key
- `.env` is in `.gitignore` by default
- Use `.env.example` as a template for others
- Rotate API keys regularly
- In production, use secrets management (AWS Secrets Manager, etc.)

---

## Performance Notes

- **Generation Time**: 30-60 seconds (depends on OpenAI API latency)
- **Concurrent Requests**: Backend handles multiple requests via async
- **Caching**: Frontend static assets cached for 1 year
- **Optimization**: Multi-stage Docker builds minimize image size

---

## Credits

- **Author**: Tarun Bommawar
- **Course**: CS 675 - Introduction to AI (Fall 2024)
- **Instructor**: Dr. Ziyu Yao
- **Institution**: George Mason University

**Technologies**:
- OpenAI GPT-4o-mini
- Sentence-BERT (all-MiniLM-L6-v2)
- FAISS (Facebook AI Similarity Search)
- FastAPI, React, Docker

---

## License

MIT License - See LICENSE file for details

---

## Support

For issues, questions, or feedback:

1. Check the **Troubleshooting** section above
2. Review backend logs: `docker-compose logs backend`
3. Open an issue on GitHub (if applicable)

---

## Submission Checklist

For TAs/Graders:

- [ ] Clone repository
- [ ] Create `.env` file with OpenAI API key
- [ ] Run `docker-compose up --build`
- [ ] Access `http://localhost:3000`
- [ ] Paste sample job posting and resume
- [ ] Click "Auto-Parse" on both panels
- [ ] Click "Generate Tailored Resume"
- [ ] Wait ~45 seconds
- [ ] Review generated output (bullets, LaTeX, change summary)
- [ ] Click "Copy" on LaTeX tabs to get source code

**Expected Result**: Full tailored resume with cover letter in ~45 seconds

---

**Thank you for using AutoResuAgent!**
