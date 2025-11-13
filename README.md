# AutoResuAgent

**An agentic NLP system for automated, tailored resume and cover letter generation.**

---

## Overview

AutoResuAgent uses state-of-the-art NLP techniques and an agentic workflow to automatically generate customized resumes and cover letters for job applications. The system:

1. **Reads** structured job descriptions (YAML) and resumes (JSON)
2. **Retrieves** relevant experience using Sentence-BERT embeddings and FAISS vector search
3. **Generates** tailored resume bullets and cover letters using GPT-4o or Claude
4. **Validates** outputs using Pydantic models and custom quality rules
5. **Iterates** through a plan → generate → validate → retry loop until valid
6. **Renders** professional PDFs using LaTeX templates

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                  AutoResuAgent                       │
│                                                      │
│  [Job YAML] + [Resume JSON]                          │
│         ↓                                            │
│  [SentenceBERT + FAISS] → Retrieve relevant exp.    │
│         ↓                                            │
│  [Agent Planner] → Strategy                          │
│         ↓                                            │
│  [LLM Generator] → Draft content                     │
│         ↓                                            │
│  [Validator] → Check quality                         │
│         ↓                                            │
│  Valid? → [Render LaTeX] → [PDF]                     │
│         ↓                                            │
│  Invalid? → [Retry with feedback]                    │
└─────────────────────────────────────────────────────┘
```

---

## Features

- **Semantic Retrieval**: Uses Sentence-BERT + FAISS for intelligent experience matching
- **Multi-LLM Support**: Works with OpenAI GPT-4o or Anthropic Claude
- **Agentic Loop**: Automatically retries generation with feedback until validation passes
- **Async Execution**: Processes multiple jobs concurrently with `asyncio.Semaphore`
- **LaTeX Rendering**: Professional PDF output using Jinja2 templates
- **Pydantic Validation**: Ensures high-quality, consistent output

---

## Installation

### 1. Clone the repository

```bash
git clone <repository-url>
cd autoresuagent
```

### 2. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 3. Install LaTeX (required for PDF generation)

- **Ubuntu/Debian**: `sudo apt-get install texlive-latex-base texlive-latex-extra`
- **macOS**: `brew install --cask mactex`
- **Windows**: Install [MiKTeX](https://miktex.org/) or [TeX Live](https://www.tug.org/texlive/)

### 4. Set up environment variables

Create a `.env` file in the project root:

```bash
# LLM API Keys (set one based on your provider)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Configuration (optional, defaults shown)
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o
EMBEDDING_MODEL=all-MiniLM-L6-v2
RETRIEVAL_TOP_K=5
MAX_RETRIES=3
MAX_CONCURRENT_JOBS=5
```

---

## Usage

### Basic Usage

```bash
python main.py \
  --jobs data/jobs/job1.yaml data/jobs/job2.yaml \
  --resume data/resumes/my_resume.json \
  --output-dir outputs/pdf \
  --llm-provider openai
```

### Arguments

- `--jobs`: One or more job description YAML files
- `--resume`: Resume JSON file
- `--output-dir`: Directory for generated PDFs (default: `./autoresuagent/outputs/pdf`)
- `--llm-provider`: LLM provider (`openai` or `anthropic`)
- `--config`: Optional path to config file
- `--log-level`: Logging level (DEBUG, INFO, WARNING, ERROR)

---

## Project Structure

```
autoresuagent/
├── data/
│   ├── jobs/                  # Job description YAML files
│   ├── resumes/               # Resume JSON files
│   └── templates/             # LaTeX/Jinja2 templates
├── src/
│   ├── models/                # Pydantic data models
│   ├── embeddings/            # SentenceBERT + FAISS
│   ├── llm/                   # LLM client implementations
│   ├── generators/            # Content generators
│   ├── agent/                 # Agentic loop components
│   ├── renderer/              # LaTeX rendering
│   ├── evaluation/            # Quality metrics
│   └── orchestration/         # Pipeline coordination
├── outputs/
│   ├── logs/                  # Application logs
│   └── pdf/                   # Generated PDFs
├── tests/                     # Unit tests
├── main.py                    # CLI entry point
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

---

## Workflow

1. **Input Parsing**: Load and validate job descriptions and resume using Pydantic
2. **Index Building**: Encode resume experiences with SentenceBERT and store in FAISS
3. **Retrieval**: For each job, retrieve top-k relevant experiences
4. **Planning**: Analyze job-resume fit and create tailoring strategy
5. **Generation**: Use LLM to generate tailored bullets and cover letter
6. **Validation**: Check output against Pydantic rules and quality criteria
7. **Retry Loop**: If invalid, provide feedback and regenerate (max 3 attempts)
8. **Rendering**: Populate LaTeX template and compile to PDF

---

## Data Formats

### Job Description (YAML)

```yaml
title: "Senior ML Engineer"
company: "TechCorp"
description: "Full job description text..."
required_skills:
  - Python
  - TensorFlow
  - AWS
responsibilities:
  - Design ML pipelines
  - Deploy models to production
keywords:
  - machine learning
  - deep learning
  - MLOps
seniority_level: "Senior"
```

### Resume (JSON)

```json
{
  "name": "John Doe",
  "email": "john@example.com",
  "summary": "Experienced ML engineer...",
  "experiences": [
    {
      "company": "Company A",
      "title": "ML Engineer",
      "start_date": "2020-01",
      "end_date": "2023-12",
      "bullets": [
        "Built recommendation system serving 1M users",
        "Reduced model latency by 40%"
      ],
      "skills": ["Python", "TensorFlow", "AWS"]
    }
  ],
  "education": [...],
  "projects": [...],
  "skills": {
    "languages": ["Python", "Java"],
    "frameworks": ["TensorFlow", "PyTorch"]
  }
}
```

---

## TODO / Future Enhancements

- [ ] Implement all core modules (currently stubs)
- [ ] Add sample job descriptions and resumes
- [ ] Create LaTeX templates
- [ ] Add unit tests
- [ ] Implement skill synonym matching
- [ ] Add ATS (Applicant Tracking System) compatibility scoring
- [ ] Support additional output formats (Word, HTML)
- [ ] Add web UI
- [ ] Implement feedback loop from user corrections

---

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Implement your changes
4. Add tests
5. Submit a pull request

---

## License

[MIT License](LICENSE) (TODO: Add license file)

---

## Contact

For questions or feedback, please open an issue on GitHub.

---

**AutoResuAgent**: Making job applications smarter, one resume at a time. 🚀
