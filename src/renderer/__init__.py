"""
Renderer Package
Handles LaTeX template rendering and PDF compilation.
"""

from .jinja_renderer import render_resume_tex, render_cover_letter_tex, escape_latex
from .latex_compiler import compile_tex_to_pdf, check_pdflatex_installed, cleanup_aux_files

__all__ = [
    "render_resume_tex",
    "render_cover_letter_tex",
    "escape_latex",
    "compile_tex_to_pdf",
    "check_pdflatex_installed",
    "cleanup_aux_files",
]
