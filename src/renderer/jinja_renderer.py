"""
Jinja2 Template Renderer
Renders LaTeX templates with generated content.
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..models import FullGeneratedPackage, CandidateProfile, JobDescription

logger = logging.getLogger(__name__)


def render_resume_tex(
    pkg: "FullGeneratedPackage",
    resume: "CandidateProfile",
    template_path: Path,
    output_path: Path
) -> Path:
    """
    Render resume to LaTeX using Jinja2 template.

    NOTE:
    For now we do NOT rely on source_experience_id / ids matching.
    Instead, we attach ALL generated bullets to a single primary experience
    so that the Professional Experience section is never empty.

    This is a safe, deterministic behavior for the class project demo.
    """
    from jinja2 import Environment, FileSystemLoader

    logger.info(f"Rendering resume LaTeX to {output_path}")

    # ------------------------------------------------------------------
    # Setup Jinja2 environment
    # ------------------------------------------------------------------
    template_dir = template_path.parent
    env = Environment(loader=FileSystemLoader(str(template_dir)))
    env.filters["latex_escape"] = escape_latex

    template = env.get_template(template_path.name)

    # ------------------------------------------------------------------
    # Build experiences_with_bullets in a SIMPLE, GUARANTEED way
    # ------------------------------------------------------------------
    experiences_with_bullets = []

    # Use the first resume experience (if any) as the "anchor"
    primary_exp = None
    if getattr(resume, "experiences", None):
        if len(resume.experiences) > 0:
            primary_exp = resume.experiences[0]

    if primary_exp and pkg.bullets:
        # Attach ALL generated bullets to this primary experience
        exp_dict = {
            "role": escape_latex(getattr(primary_exp, "role", "")),
            "company": escape_latex(getattr(primary_exp, "company", "")),
            "location": (
                escape_latex(getattr(primary_exp, "location", ""))
                if getattr(primary_exp, "location", None)
                else None
            ),
            "start_date": escape_latex(getattr(primary_exp, "start_date", "")) if getattr(primary_exp, "start_date", None) else "",
            "end_date": escape_latex(getattr(primary_exp, "end_date", "")) if getattr(primary_exp, "end_date", None) else None,
            "bullets": [
                {"text": escape_latex(b.text)}
                for b in pkg.bullets
            ],
        }
        experiences_with_bullets.append(exp_dict)
        logger.info(
            f"Attached {len(pkg.bullets)} generated bullets to primary experience "
            f"'{exp_dict['role']}' at '{exp_dict['company']}'"
        )
    else:
        # Fallback: no primary experience or no bullets; keep it empty
        logger.warning(
            "No primary experience or no generated bullets; "
            "Professional Experience section will be empty."
        )

    logger.info(f"Built {len(experiences_with_bullets)} experiences with generated bullets")

    # ------------------------------------------------------------------
    # Prepare context for Jinja template
    # ------------------------------------------------------------------
    context = {
        "candidate_name": escape_latex(resume.name),
        "candidate_email": escape_latex(resume.email),
        "candidate_phone": escape_latex(resume.phone) if resume.phone else None,
        "candidate_location": escape_latex(resume.location) if resume.location else None,
        "candidate_linkedin_url": getattr(resume, "linkedin_url", None),
        "candidate_github_url": getattr(resume, "github_url", None),
        "summary": (
            escape_latex(getattr(resume, "summary", ""))
            if getattr(resume, "summary", "")
            else None
        ),
        "skills": [
            escape_latex(skill) for skill in (getattr(resume, "skills", []) or [])
        ],
        "experiences": experiences_with_bullets,
        "education": [
            {
                "degree": escape_latex(edu.degree),
                "institution": escape_latex(edu.institution),
                "year": str(edu.year) if edu.year else None,
                "details": [
                    escape_latex(d) for d in (edu.details or [])
                ],
            }
            for edu in (getattr(resume, "education", []) or [])
        ],
        "projects": [
            {
                "title": escape_latex(proj.title),
                "description": escape_latex(proj.description) if proj.description else None,
                "tech_stack": [escape_latex(t) for t in (proj.tech_stack or [])],
                "link": proj.link,  # Don't escape URL
                "github_url": getattr(proj, "github_url", None), # Don't escape URL
                "bullets": [escape_latex(b) for b in (proj.bullets or [])],
            }
            for proj in (getattr(resume, "projects", []) or [])
        ],
    }

    # ------------------------------------------------------------------
    # Render template and write file
    # ------------------------------------------------------------------
    rendered = template.render(**context)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(rendered, encoding="utf-8")

    logger.info(f"Resume LaTeX rendered successfully: {output_path}")
    return output_path



def render_cover_letter_tex(
    pkg: "FullGeneratedPackage",
    resume: "CandidateProfile",
    job: "JobDescription",
    template_path: Path,
    output_path: Path
) -> Path:
    """
    Render cover letter to LaTeX using Jinja2 template.

    Args:
        pkg: Full generated package with cover letter
        resume: Candidate's resume profile
        job: Job description
        template_path: Path to cover_letter.tex.jinja template
        output_path: Path to save rendered .tex file

    Returns:
        Path to rendered .tex file
    """
    from jinja2 import Environment, FileSystemLoader

    logger.info(f"Rendering cover letter LaTeX to {output_path}")

    if not pkg.cover_letter:
        raise ValueError("Package has no cover letter to render")

    cover = pkg.cover_letter

    # 🔹 Split the single `text` field into opening / body / closing
    paragraphs = [
        p.strip()
        for p in cover.text.split("\n\n")
        if p.strip()
    ]

    opening = paragraphs[0] if paragraphs else ""
    closing = paragraphs[-1] if len(paragraphs) > 1 else ""
    if len(paragraphs) > 2:
        body_paras = paragraphs[1:-1]
    else:
        body_paras = paragraphs[1:]
    body = "\n\n".join(body_paras)

    # Setup Jinja2 environment
    template_dir = template_path.parent
    env = Environment(loader=FileSystemLoader(str(template_dir)))

    # Add LaTeX escape filter
    env.filters['latex_escape'] = escape_latex

    # Load template
    template = env.get_template(template_path.name)

    # Prepare context
    context = {
        'candidate_name': escape_latex(resume.name),
        'candidate_email': escape_latex(resume.email),
        'candidate_phone': escape_latex(resume.phone) if resume.phone else None,
        'candidate_location': escape_latex(resume.location) if resume.location else None,
        'date': datetime.now().strftime('%B %d, %Y'),
        'company': escape_latex(job.company),
        'job_title': escape_latex(job.title),

        # ✅ Derived from cover.text, no direct .opening/.body/.closing attrs
        'opening': escape_latex(opening) if opening else None,
        'body': escape_latex(body) if body else None,
        'closing': escape_latex(closing) if closing else None,
    }

    # Render template
    rendered = template.render(**context)

    # Write to file
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(rendered, encoding='utf-8')

    logger.info(f"Cover letter LaTeX rendered successfully: {output_path}")
    return output_path



def escape_latex(text: str) -> str:
    """
    Escape LaTeX special characters.

    Args:
        text: Input text that may contain LaTeX special chars

    Returns:
        Text with special characters escaped

    Note:
        Order matters! Backslash must be replaced first.
    """
    if not text:
        return ""

    # Replace backslash first (before adding more backslashes)
    text = text.replace('\\', r'\textbackslash{}')

    # Replace other special characters
    replacements = {
        '&': r'\&',
        '%': r'\%',
        '$': r'\$',
        '#': r'\#',
        '_': r'\_',
        '{': r'\{',
        '}': r'\}',
        '~': r'\textasciitilde{}',
        '^': r'\^{}',
    }

    for char, escaped in replacements.items():
        text = text.replace(char, escaped)

    return text
