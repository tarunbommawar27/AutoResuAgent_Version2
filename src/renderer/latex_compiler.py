"""
LaTeX Compiler
Compiles LaTeX files to PDF using pdflatex.
"""

import logging
import subprocess
import shutil
from pathlib import Path

logger = logging.getLogger(__name__)


def compile_tex_to_pdf(tex_path: Path, output_dir: Path) -> Path:
    """
    Compile a .tex file to PDF using pdflatex.

    Args:
        tex_path: Path to .tex file
        output_dir: Directory to save PDF and logs

    Returns:
        Path to generated PDF

    Raises:
        RuntimeError: If pdflatex not found or compilation fails

    Example:
        >>> pdf_path = compile_tex_to_pdf(
        ...     Path("outputs/resume.tex"),
        ...     Path("outputs")
        ... )
    """
    logger.info(f"Compiling {tex_path} to PDF")

    # Check if pdflatex is available
    if not check_pdflatex_installed():
        raise RuntimeError(
            "pdflatex not found. Please install LaTeX (e.g., TeX Live, MiKTeX) "
            "to compile PDFs. For testing without LaTeX, the .tex files are still generated."
        )

    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    # Create logs directory
    logs_dir = output_dir / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

    # Run pdflatex twice (for references)
    # First pass
    logger.debug(f"Running pdflatex (pass 1/2)...")
    result1 = _run_pdflatex(tex_path, output_dir, logs_dir)

    if result1.returncode != 0:
        logger.error(f"pdflatex failed (pass 1): {result1.stderr}")
        _save_compilation_log(tex_path, result1, logs_dir, pass_num=1)
        raise RuntimeError(
            f"LaTeX compilation failed. Check logs in {logs_dir / tex_path.stem}_pass1.log"
        )

    # Second pass (for table of contents, references, etc.)
    logger.debug(f"Running pdflatex (pass 2/2)...")
    result2 = _run_pdflatex(tex_path, output_dir, logs_dir)

    if result2.returncode != 0:
        logger.error(f"pdflatex failed (pass 2): {result2.stderr}")
        _save_compilation_log(tex_path, result2, logs_dir, pass_num=2)
        raise RuntimeError(
            f"LaTeX compilation failed. Check logs in {logs_dir / tex_path.stem}_pass2.log"
        )

    # Check PDF was created
    pdf_path = output_dir / f"{tex_path.stem}.pdf"
    if not pdf_path.exists():
        raise RuntimeError(f"PDF not created: {pdf_path}")

    # Clean up auxiliary files
    cleanup_aux_files(tex_path, output_dir)

    logger.info(f"PDF compiled successfully: {pdf_path}")
    return pdf_path


def check_pdflatex_installed() -> bool:
    """
    Check if pdflatex is available in PATH.

    Returns:
        True if pdflatex found, False otherwise
    """
    return shutil.which("pdflatex") is not None


def _run_pdflatex(tex_path: Path, output_dir: Path, logs_dir: Path) -> subprocess.CompletedProcess:
    """
    Run pdflatex on a .tex file.

    Args:
        tex_path: Path to .tex file
        output_dir: Directory for PDF output
        logs_dir: Directory for log files

    Returns:
        CompletedProcess result
    """
    try:
        result = subprocess.run(
            [
                "pdflatex",
                "-interaction=nonstopmode",  # Don't stop on errors
                f"-output-directory={output_dir}",
                str(tex_path)
            ],
            capture_output=True,
            text=True,
            timeout=30,  # 30 second timeout
            cwd=tex_path.parent  # Run from tex file directory
        )
        return result

    except subprocess.TimeoutExpired as e:
        logger.error(f"pdflatex timed out after 30 seconds")
        raise RuntimeError("LaTeX compilation timed out")

    except FileNotFoundError as e:
        logger.error(f"pdflatex not found: {e}")
        raise RuntimeError("pdflatex executable not found")


def _save_compilation_log(
    tex_path: Path,
    result: subprocess.CompletedProcess,
    logs_dir: Path,
    pass_num: int
):
    """
    Save compilation logs for debugging.

    Args:
        tex_path: Path to .tex file that was compiled
        result: CompletedProcess result
        logs_dir: Directory to save logs
        pass_num: Compilation pass number
    """
    log_path = logs_dir / f"{tex_path.stem}_pass{pass_num}.log"

    with open(log_path, 'w', encoding='utf-8') as f:
        f.write(f"=== LaTeX Compilation Log (Pass {pass_num}) ===\n\n")
        f.write(f"File: {tex_path}\n")
        f.write(f"Return code: {result.returncode}\n\n")
        f.write("=== STDOUT ===\n")
        f.write(result.stdout)
        f.write("\n\n=== STDERR ===\n")
        f.write(result.stderr)

    logger.info(f"Compilation log saved: {log_path}")


def cleanup_aux_files(tex_path: Path, output_dir: Path):
    """
    Remove auxiliary LaTeX files after compilation.

    Args:
        tex_path: Path to .tex file
        output_dir: Directory where auxiliary files are located
    """
    base_name = tex_path.stem
    aux_extensions = ['.aux', '.log', '.out', '.toc', '.synctex.gz', '.fls', '.fdb_latexmk']

    for ext in aux_extensions:
        aux_file = output_dir / f"{base_name}{ext}"
        if aux_file.exists():
            try:
                aux_file.unlink()
                logger.debug(f"Removed auxiliary file: {aux_file.name}")
            except Exception as e:
                logger.warning(f"Failed to remove {aux_file}: {e}")
