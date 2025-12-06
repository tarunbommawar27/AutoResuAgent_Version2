# AutoResuAgent Presentation Package

This folder contains the LaTeX source code for the AutoResuAgent final project presentation.

## Files
- **`presentation.tex`**: The main Beamer presentation source file.
- **`compile_presentation.bat`**: Windows batch script to compile the PDF.
- **`AutoResuAgent_Technical_Deep_Dive.tex`**: Technical handout with architecture details.

## Prerequisites
You need a LaTeX distribution installed on your system:
- **Windows**: [MiKTeX](https://miktex.org/download) (Recommended) or TeX Live.
- **Mac/Linux**: TeX Live (`sudo apt install texlive-full` or MacTeX).

## How to Compile
1. Double-click `compile_presentation.bat`.
2. The script will run `pdflatex` twice to resolve slide numbers and references.
3. `presentation.pdf` will be generated in the same folder.

## Speaker Notes
The presentation includes speaker notes. To view them while presenting:
- Open `presentation.pdf` in Adobe Acrobat or a similar PDF reader.
- Use "Presenter View" if available, or print the slides with notes enabled.

## Customization
- To change the theme, edit line 4 of `presentation.tex`: `\usetheme{Madrid}`.
- To add your own images, replace the placeholders in the `figure` environments.
