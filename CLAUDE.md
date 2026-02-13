# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is a Master's dissertation repository for MEIA (Master in Artificial Intelligence Engineering) at ISEP/P.PORTO. The thesis focuses on "Automated Software Testing using Multi-Agent Systems (MAS) and Large Language Models (LLMs)" with emphasis on privacy, security, and GDPR considerations.

**Author:** Rui Marinho (1171602)
**Supervisor:** Constantino Martins

## Repository Structure

- `emtrega3_recurso/` - Main working directory for the dissertation document (LaTeX)
- `iteracao1_tpdimeia/` - Iteration deliverables and supplementary materials
- `old_stuff/` - Previous versions and backups (not used in active development)

## Building the Dissertation

### Prerequisites

Ensure you have the following LaTeX tools installed:
- `pdflatex`
- `latexmk`
- `biber`
- `makeglossaries`

### Build Commands

All build commands should be run from the `emtrega3_recurso/` directory:

```bash
cd emtrega3_recurso
```

**Build the PDF:**
```bash
make
```
This compiles `main.tex` and generates `main.pdf` in the current directory. Build artifacts are placed in `build/` subdirectory.

**Clean build artifacts:**
```bash
make clean
```

**Complete clean (including biber cache):**
```bash
make clean-all
```

Note: The `clean-all` target may not work on Windows systems.

## Document Structure

The dissertation is structured using LaTeX with a custom MEIA style class (`meia-style.cls`).

### Main Files

- `main.tex` - Document entry point containing preamble, metadata, and structure
- `mainbibliography.bib` - Bibliography database (BibTeX format)
- `meia-style.cls` - Custom LaTeX class defining document formatting

### Content Organization

- `frontmatter/` - Title page, abstracts, acknowledgments, glossary
- `ch1/` - Chapter 1: Thesis Structure (guidelines and recommendations)
- `ch2/` - Chapter 2: About LaTeX and Template Usage
- `ch3/` - Chapter 3: (working content)
- `appendices/` - Appendix materials

Each chapter is in its own directory with:
- `chapterN.tex` - Main chapter content
- `assets/` - Chapter-specific figures, diagrams, and supporting files (if needed)

### Key Document Settings

The thesis uses:
- **Language:** English (can be changed to Portuguese by modifying document class options)
- **Citation style:** `authoryear-comp` (Harvard-like style) using biblatex with biber backend
- **Font size:** 11pt
- **Spacing:** Single spacing with `parskip` (space between paragraphs)

Alternative citation styles are commented in `main.tex`:
- `numeric-comp` for numeric citations [1], [1-3]
- `alphabetic` for alphabetic citations [Buendía10]

### Important Metadata (in main.tex)

Update thesis metadata at lines 77-101:
- Title, subtitle, author, student number
- Supervisor and co-supervisor names
- Committee members
- Keywords (up to 6)
- Thesis date

### Glossary and Acronyms

Glossary entries are defined in `frontmatter/glossary.tex` and must be included in the preamble. The template uses `makenoidxglossaries` for Overleaf compatibility.

Usage in text:
- `\acrlong{AI}` - First use (expanded form)
- `\acrshort{AI}` - Subsequent uses (abbreviated form)

## LaTeX Development Notes

### When modifying chapters:

1. Each chapter is referenced with a label (e.g., `\label{chap:Chapter1}`)
2. Sections within chapters use descriptive labels (e.g., `\label{sec:chap1_introduction}`)
3. Reference them in text with `Chapter~\ref{chap:Chapter1}` or `Section~\ref{sec:chap1_introduction}`

### Adding new content:

- **New chapter:** Create a new directory `chN/`, add `chapterN.tex`, and include it in `main.tex` with `\input{chN/chapterN}`
- **New appendix:** Add file to `appendices/` and include it in `main.tex` with `\input{appendices/appendixX}`
- **Images/assets:** Place in the chapter's `assets/` subdirectory
- **Bibliography entries:** Add to `mainbibliography.bib` in BibTeX format

### Language switching:

To switch document language, modify `main.tex` line 33-34:
- Comment/uncomment `english` or `portuguese` option
- Delete temporary files: `make clean` before rebuilding

### Common LaTeX packages in use:

- `tikz` and `pgfplots` - Graphics and plots
- `biblatex` - Bibliography management
- `makecell` - Enhanced table cells
- Standard packages: `babel`, `graphicx`, `booktabs`, `listings`, `algorithm`

## Research Notes

The `Google.md` file in `emtrega3_recurso/` appears to contain search results or research notes. This may be a working document for literature review.
