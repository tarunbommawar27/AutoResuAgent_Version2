"""
Data Parser Module
Uses LLM to parse raw text into structured YAML/JSON for job descriptions and resumes.
"""

import json
import yaml
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .llm import BaseLLMClient

logger = logging.getLogger(__name__)


class DataParser:
    """
    Parse raw text into structured data using LLM.

    Converts unstructured job postings and resumes (from LinkedIn, PDFs, etc.)
    into valid YAML/JSON that matches our Pydantic schemas.

    Example:
        >>> parser = DataParser(llm_client)
        >>> job_yaml = await parser.parse_raw_job("Senior ML Engineer at TechCorp...")
        >>> resume_json = await parser.parse_raw_resume("John Doe | ML Engineer...")
    """

    def __init__(self, llm: "BaseLLMClient"):
        """
        Initialize parser with LLM client.

        Args:
            llm: LLM client (OpenAI or Anthropic) for extraction
        """
        self.llm = llm

    async def parse_raw_job(self, raw_text: str) -> str:
        """
        Parse raw job posting text into structured YAML.

        Extracts job details from unstructured text (LinkedIn, company careers page, etc.)
        and converts it into valid YAML matching the JobDescription schema.

        Args:
            raw_text: Raw job posting text

        Returns:
            YAML string matching JobDescription schema

        Example:
            >>> yaml_str = await parser.parse_raw_job('''
            ... Senior ML Engineer at TechCorp
            ... San Francisco, CA
            ...
            ... Responsibilities:
            ... - Build ML models
            ... - Deploy to production
            ...
            ... Requirements:
            ... - Python, TensorFlow
            ... - 5+ years experience
            ... ''')
        """
        prompt = f"""You are a job posting extraction expert. Extract structured information from the raw job posting below.

Raw Job Posting:
{raw_text}

Your task is to extract and return ONLY valid YAML in the following schema. Do not include any explanations, markdown formatting, or code blocks - return ONLY the raw YAML text.

Required Schema:
job_id: string (generate a unique ID like "job-YYYY-MM-DD-company-title")
title: string (job title)
company: string (company name, or "Unknown" if not found)
location: string (location or "Remote" if not specified)
seniority: string (e.g., "Entry", "Mid-Level", "Senior", "Lead", or "Not Specified")
employment_type: string (e.g., "Full-time", "Part-time", "Contract", or "Not Specified")
posted_on: string (date in YYYY-MM-DD format, or today's date if unknown)
required_skills: list of strings (extract must-have technical skills)
nice_to_have_skills: list of strings (extract preferred/nice-to-have skills, or empty list)
responsibilities: list of strings (extract key job responsibilities/duties)

Important:
- Extract ALL skills mentioned in requirements, qualifications, or "must-haves"
- Extract nice-to-have skills from "preferred", "nice-to-have", or "bonus" sections
- Extract responsibilities from "what you'll do", "responsibilities", "duties" sections
- If a field is not found, use reasonable defaults (don't leave fields empty)
- Generate a unique job_id based on company and title
- Return ONLY the YAML text, no markdown code blocks or explanations

Example Output Format:
job_id: "job-2025-12-04-techcorp-senior-ml"
title: "Senior ML Engineer"
company: "TechCorp"
location: "San Francisco, CA"
seniority: "Senior"
employment_type: "Full-time"
posted_on: "2025-12-04"
required_skills:
  - Python
  - TensorFlow
  - AWS
nice_to_have_skills:
  - Kubernetes
  - MLOps
responsibilities:
  - Build and deploy ML models
  - Lead ML infrastructure projects
"""

        response = await self.llm.generate(prompt)

        # Clean up response (remove markdown code blocks if present)
        yaml_text = response.strip()
        if yaml_text.startswith("```yaml"):
            yaml_text = yaml_text[7:]
        if yaml_text.startswith("```"):
            yaml_text = yaml_text[3:]
        if yaml_text.endswith("```"):
            yaml_text = yaml_text[:-3]
        yaml_text = yaml_text.strip()

        # Validate it's parseable YAML
        try:
            yaml.safe_load(yaml_text)
        except yaml.YAMLError as e:
            raise ValueError(f"Generated invalid YAML: {e}\n\nGenerated text:\n{yaml_text}")

        return yaml_text

    async def parse_raw_resume(self, raw_text: str) -> str:
        """
        Parse raw resume text into structured JSON.

        Extracts candidate information from unstructured text (LinkedIn profile,
        PDF resume, etc.) and converts it into valid JSON matching the CandidateProfile schema.

        Args:
            raw_text: Raw resume text

        Returns:
            JSON string matching CandidateProfile schema

        Example:
            >>> json_str = await parser.parse_raw_resume('''
            ... John Doe
            ... ML Engineer | San Francisco, CA
            ... john@example.com
            ...
            ... Experience:
            ... Senior ML Engineer at TechCorp (2020-Present)
            ... - Built recommendation system
            ... - Deployed to production
            ... ''')
        """
        prompt = f"""You are a resume extraction expert. Extract structured information from the raw resume/profile below.

Raw Resume/Profile:
{raw_text}

Your task is to extract and return ONLY valid JSON in the following schema. Do not include any explanations, markdown formatting, or code blocks - return ONLY the raw JSON text.

Required Schema:
{{
  "candidate_id": "string (generate unique ID like 'cand-YYYY-MM-DD-lastname')",
  "name": "string (full name)",
  "email": "string (email address, or 'unknown@example.com' if not found)",
  "phone": "string or null (phone number if available)",
  "location": "string or null (current location)",
  "linkedin_url": "string or null (LinkedIn URL if mentioned)",
  "github_url": "string or null (GitHub URL if mentioned)",
  "skills": ["array of skill strings"],
  "experiences": [
    {{
      "id": "string (e.g., 'exp-1', 'exp-2')",
      "role": "string (job title)",
      "company": "string (company name)",
      "location": "string or null",
      "start_date": "string (e.g., 'Jan 2020', '2020-01')",
      "end_date": "string or null (null for current position)",
      "bullets": ["array of accomplishment strings"]
    }}
  ],
  "education": [
    {{
      "institution": "string (school/university name)",
      "degree": "string (degree name)",
      "location": "string or null",
      "start_date": "string or null",
      "end_date": "string or null",
      "gpa": "string or null"
    }}
  ],
  "projects": [
    {{
      "id": "string (e.g., 'proj-1', 'proj-2')",
      "title": "string (project name)",
      "description": "string (brief description)",
      "tech_stack": ["array of technologies"],
      "link": "string or null (GitHub/demo URL)",
      "bullets": ["array of accomplishment strings"]
    }}
  ]
}}

Important Extraction Rules:
- Extract ALL technical skills mentioned throughout the resume
- For experiences: create separate entries for each job
- For each experience: extract ALL bullet points/accomplishments
- For projects: extract personal/academic/side projects mentioned
- Generate unique IDs (exp-1, exp-2, proj-1, proj-2, etc.)
- If email not found, use "unknown@example.com"
- Parse dates carefully (handle formats like "Jan 2020", "2020-01", "2020-2022")
- For current positions, set end_date to null
- Extract education even if minimal (degree + institution minimum)
- Return ONLY the JSON text, no markdown code blocks or explanations

Example Output Format:
{{
  "candidate_id": "cand-2025-12-04-doe",
  "name": "John Doe",
  "email": "john@example.com",
  "phone": "+1-555-0123",
  "location": "San Francisco, CA",
  "linkedin_url": "linkedin.com/in/johndoe",
  "github_url": "github.com/johndoe",
  "skills": ["Python", "TensorFlow", "AWS", "Docker"],
  "experiences": [
    {{
      "id": "exp-1",
      "role": "Senior ML Engineer",
      "company": "TechCorp",
      "location": "San Francisco, CA",
      "start_date": "Jan 2020",
      "end_date": null,
      "bullets": [
        "Built recommendation system serving 1M+ users",
        "Reduced model latency by 40%"
      ]
    }}
  ],
  "education": [
    {{
      "institution": "Stanford University",
      "degree": "Master of Science in Computer Science",
      "location": "Stanford, CA",
      "start_date": "2017",
      "end_date": "2019",
      "gpa": "3.9"
    }}
  ],
  "projects": [
    {{
      "id": "proj-1",
      "title": "ML Pipeline",
      "description": "End-to-end ML pipeline for production",
      "tech_stack": ["Python", "Kubernetes", "TensorFlow"],
      "link": "github.com/johndoe/ml-pipeline",
      "bullets": [
        "Built scalable pipeline handling 10M requests/day",
        "Reduced deployment time by 60%"
      ]
    }}
  ]
}}
"""

        response = await self.llm.generate(prompt)

        # Clean up response (remove markdown code blocks if present)
        json_text = response.strip()
        if json_text.startswith("```json"):
            json_text = json_text[7:]
        if json_text.startswith("```"):
            json_text = json_text[3:]
        if json_text.endswith("```"):
            json_text = json_text[:-3]
        json_text = json_text.strip()

        # Validate it's parseable JSON
        try:
            json.loads(json_text)
        except json.JSONDecodeError as e:
            raise ValueError(f"Generated invalid JSON: {e}\n\nGenerated text:\n{json_text}")

        return json_text

    async def generate_resume_latex(
        self,
        candidate_data: dict,
        tailored_bullets: list[dict],
        job_title: str = "Software Engineer",
        company: str = "Target Company"
    ) -> str:
        """
        Generate professional LaTeX resume from tailored bullets.

        Args:
            candidate_data: Candidate profile dict (from CandidateProfile)
            tailored_bullets: List of tailored bullet dicts with 'text' field
            job_title: Target job title
            company: Target company name

        Returns:
            LaTeX source code ready to compile

        Example:
            >>> latex = await parser.generate_resume_latex(
            ...     candidate_data=resume.dict(),
            ...     tailored_bullets=[{"text": "Built ML system..."}, ...],
            ...     job_title="ML Engineer",
            ...     company="Google"
            ... )
        """
        logger.info(f"Generating LaTeX resume for {candidate_data.get('name', 'Unknown')}...")

        # Format bullets as text list
        bullets_text = "\n".join([f"- {b.get('text', '')}" for b in tailored_bullets])

        # Format skills
        skills = candidate_data.get('skills', [])
        skills_text = ', '.join(skills[:20]) if skills else "Python, JavaScript, SQL"

        # Format education
        education = candidate_data.get('education', [])
        education_text = ""
        for edu in education:
            education_text += f"{edu.get('degree', 'Degree')} - {edu.get('institution', 'University')}\n"

        # Format projects
        projects = candidate_data.get('projects', [])
        projects_text = ""
        for proj in projects[:3]:  # Limit to 3 projects
            projects_text += f"**{proj.get('title', 'Project')}**: {proj.get('description', '')}\n"
            for bullet in proj.get('bullets', [])[:2]:  # 2 bullets per project
                projects_text += f"- {bullet}\n"

        prompt = f"""Generate a professional, ATS-friendly LaTeX resume. Return ONLY the LaTeX code, no explanations.

CANDIDATE INFO:
Name: {candidate_data.get('name', 'Candidate Name')}
Email: {candidate_data.get('email', 'email@example.com')}
Phone: {candidate_data.get('phone', '(555) 555-5555')}
Location: {candidate_data.get('location', 'City, State')}
LinkedIn: {candidate_data.get('linkedin_url', '')}
GitHub: {candidate_data.get('github_url', '')}

TARGET JOB: {job_title} at {company}

TAILORED BULLETS (use these in experience section):
{bullets_text}

SKILLS: {skills_text}

EDUCATION:
{education_text if education_text else "Bachelor of Science in Computer Science"}

PROJECTS:
{projects_text if projects_text else "No projects listed"}

REQUIREMENTS:
1. Use standard article or moderncv document class
2. Clean, professional layout (no fancy graphics)
3. Header: Name, contact info (email, phone, location, LinkedIn, GitHub)
4. Sections: EDUCATION, EXPERIENCE, PROJECTS, TECHNICAL SKILLS
5. In EXPERIENCE section, use the TAILORED BULLETS provided above
6. Keep formatting simple for ATS compatibility
7. Use standard LaTeX packages (geometry, enumitem, hyperref)
8. 1-page format preferred

Return ONLY the complete LaTeX document starting with \\documentclass and ending with \\end{{document}}.
Do NOT include markdown code blocks or explanations."""

        try:
            response = await self.llm.generate(prompt)

            # Clean up response
            latex_text = response.strip()
            if latex_text.startswith("```latex"):
                latex_text = latex_text[8:]
            if latex_text.startswith("```tex"):
                latex_text = latex_text[6:]
            if latex_text.startswith("```"):
                latex_text = latex_text[3:]
            if latex_text.endswith("```"):
                latex_text = latex_text[:-3]
            latex_text = latex_text.strip()

            # Basic validation - check for required LaTeX commands
            if "\\documentclass" not in latex_text or "\\end{document}" not in latex_text:
                logger.error("Generated LaTeX is missing document structure")
                raise ValueError("Generated LaTeX is missing required document structure")

            logger.info(f"✅ Successfully generated LaTeX resume ({len(latex_text)} chars)")
            return latex_text

        except Exception as e:
            logger.error(f"LaTeX resume generation error: {e}")
            raise

    async def generate_cover_letter_latex(
        self,
        cover_letter_text: str,
        candidate_name: str = "Candidate",
        candidate_email: str = "email@example.com",
        candidate_phone: str = "(555) 555-5555",
        job_title: str = "Position",
        company: str = "Company"
    ) -> str:
        """
        Generate professional LaTeX cover letter.

        Args:
            cover_letter_text: Plain text cover letter content
            candidate_name: Candidate's full name
            candidate_email: Email address
            candidate_phone: Phone number
            job_title: Target job title
            company: Target company name

        Returns:
            LaTeX source code for cover letter

        Example:
            >>> latex = await parser.generate_cover_letter_latex(
            ...     cover_letter_text="Dear Hiring Manager...",
            ...     candidate_name="John Doe",
            ...     candidate_email="john@example.com",
            ...     candidate_phone="+1-555-0123",
            ...     job_title="ML Engineer",
            ...     company="Google"
            ... )
        """
        logger.info(f"Generating LaTeX cover letter for {candidate_name}...")

        prompt = f"""Generate a professional cover letter in LaTeX format. Return ONLY the LaTeX code, no explanations.

CANDIDATE:
Name: {candidate_name}
Email: {candidate_email}
Phone: {candidate_phone}

TARGET: {job_title} at {company}

COVER LETTER TEXT:
{cover_letter_text}

REQUIREMENTS:
1. Use letter document class or article class with professional formatting
2. Include header with candidate contact info
3. Add hiring manager address placeholder
4. Format the cover letter text provided above
5. Professional business letter style
6. Signature line with candidate name
7. Use standard LaTeX packages (geometry, hyperref)

Return ONLY the complete LaTeX document starting with \\documentclass and ending with \\end{{document}}.
Do NOT include markdown code blocks or explanations."""

        try:
            response = await self.llm.generate(prompt)

            # Clean up response
            latex_text = response.strip()
            if latex_text.startswith("```latex"):
                latex_text = latex_text[8:]
            if latex_text.startswith("```tex"):
                latex_text = latex_text[6:]
            if latex_text.startswith("```"):
                latex_text = latex_text[3:]
            if latex_text.endswith("```"):
                latex_text = latex_text[:-3]
            latex_text = latex_text.strip()

            # Basic validation
            if "\\documentclass" not in latex_text or "\\end{document}" not in latex_text:
                logger.error("Generated LaTeX is missing document structure")
                raise ValueError("Generated LaTeX is missing required document structure")

            logger.info(f"✅ Successfully generated LaTeX cover letter ({len(latex_text)} chars)")
            return latex_text

        except Exception as e:
            logger.error(f"LaTeX cover letter generation error: {e}")
            raise

    async def generate_change_summary(
        self,
        original_resume_data: dict,
        tailored_bullets: list[dict],
        job_description: dict
    ) -> str:
        """
        Generate semantic diff summary explaining how resume was tailored.

        Analyzes the original resume vs tailored bullets and explains specific
        improvements, keyword additions, metric quantifications, etc.

        Args:
            original_resume_data: Original candidate profile dict
            tailored_bullets: List of tailored bullet dicts
            job_description: Job description dict

        Returns:
            Human-readable summary of changes (bulleted list)

        Example:
            >>> summary = await parser.generate_change_summary(
            ...     original_resume_data=resume.dict(),
            ...     tailored_bullets=[{"text": "..."}, ...],
            ...     job_description=job.dict()
            ... )
            >>> print(summary)
            - Added keywords: Python, TensorFlow, AWS (matched job requirements)
            - Quantified impact metrics in 3 bullets (e.g., "30% improvement")
            - Emphasized ML/NLP experience to align with job responsibilities
            - Reframed cloud experience to highlight AWS specifically
        """
        logger.info("Generating change summary...")

        # Extract original bullets for comparison
        original_bullets = []
        for exp in original_resume_data.get('experiences', []):
            original_bullets.extend(exp.get('bullets', []))
        for proj in original_resume_data.get('projects', []):
            original_bullets.extend(proj.get('bullets', []))

        original_bullets_text = "\n".join([f"- {b}" for b in original_bullets[:20]])  # Limit to avoid token overflow
        tailored_bullets_text = "\n".join([f"- {b.get('text', '')}" for b in tailored_bullets])

        # Job requirements
        job_skills = job_description.get('required_skills', []) + job_description.get('nice_to_have_skills', [])
        job_responsibilities = job_description.get('responsibilities', [])

        prompt = f"""Compare the original resume bullets with tailored resume bullets and explain the improvements.

TARGET JOB:
Title: {job_description.get('title', 'Unknown')}
Company: {job_description.get('company', 'Unknown')}
Required Skills: {', '.join(job_skills[:15])}
Key Responsibilities:
{chr(10).join([f'- {r}' for r in job_responsibilities[:5]])}

ORIGINAL RESUME BULLETS:
{original_bullets_text}

TAILORED RESUME BULLETS:
{tailored_bullets_text}

TASK: Analyze and explain improvements as a bulleted list. Focus on:
1. Keywords added to match job requirements
2. Metrics/numbers quantified
3. Experience reframing
4. Technical skills highlighted
5. Strategic improvements

Return as bulleted list using - prefix. Be specific. NO markdown code blocks.

Example:
- Added keywords: Docker, Kubernetes, CI/CD to match required skills
- Quantified 4 accomplishments with metrics (30% improvement, 10M requests/day)
- Emphasized AWS cloud experience for infrastructure requirements
- Reframed NLP projects to highlight production ML deployment"""

        try:
            response = await self.llm.generate(prompt)

            # Clean up response
            summary_text = response.strip()
            if summary_text.startswith("```"):
                # Remove code blocks if present
                lines = summary_text.split('\n')
                summary_text = '\n'.join([l for l in lines if not l.strip().startswith('```')])
                summary_text = summary_text.strip()

            logger.info(f"✅ Successfully generated change summary")
            return summary_text

        except Exception as e:
            logger.error(f"Change summary generation error: {e}")
            raise
