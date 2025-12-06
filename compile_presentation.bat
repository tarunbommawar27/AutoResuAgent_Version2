@echo off
echo ==========================================
echo AutoResuAgent Presentation Compiler
echo ==========================================

WHERE pdflatex
IF %ERRORLEVEL% NEQ 0 (
    echo [ERROR] pdflatex is not found in your PATH.
    echo Please install MiKTeX or TeX Live.
    pause
    exit /b
)

echo.
echo [1/2] Running pdflatex (Pass 1)...
pdflatex -interaction=nonstopmode presentation.tex

echo.
echo [2/2] Running pdflatex (Pass 2 for references)...
pdflatex -interaction=nonstopmode presentation.tex

echo.
if exist presentation.pdf (
    echo [SUCCESS] presentation.pdf created successfully!
) else (
    echo [FAILURE] Something went wrong. Check presentation.log for details.
)

echo.
echo Cleaning up auxiliary files...
del *.aux *.log *.nav *.out *.snm *.toc 2>nul

pause
