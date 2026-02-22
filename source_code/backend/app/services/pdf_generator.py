import os
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML

TEMPLATES_DIR = Path(__file__).parent.parent / "templates"
OUTPUT_DIR = Path("/tmp/cv_docs")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

_jinja_env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))


def _markdown_to_html_paragraphs(text: str) -> str:
    """Convert simple markdown-ish text to HTML paragraphs."""
    lines = text.split("\n")
    html_lines = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            html_lines.append("")
            continue
        # Headers
        if stripped.startswith("### "):
            html_lines.append(f"<h3>{stripped[4:]}</h3>")
        elif stripped.startswith("## "):
            html_lines.append(f"<h2>{stripped[3:]}</h2>")
        elif stripped.startswith("# "):
            html_lines.append(f"<h1>{stripped[2:]}</h1>")
        # Bullet points
        elif stripped.startswith("- ") or stripped.startswith("* "):
            html_lines.append(f"<li>{stripped[2:]}</li>")
        elif stripped.startswith("**") and stripped.endswith("**"):
            html_lines.append(f"<strong>{stripped[2:-2]}</strong>")
        else:
            html_lines.append(f"<p>{stripped}</p>")

    # Wrap consecutive <li> items in <ul>
    result = []
    in_list = False
    for line in html_lines:
        if line.startswith("<li>"):
            if not in_list:
                result.append("<ul>")
                in_list = True
            result.append(line)
        else:
            if in_list:
                result.append("</ul>")
                in_list = False
            result.append(line)
    if in_list:
        result.append("</ul>")

    return "\n".join(result)


def generate_cv_pdf(session_id: str, cv_text: str) -> Path:
    template = _jinja_env.get_template("improved_cv.html")
    content_html = _markdown_to_html_paragraphs(cv_text)
    html_str = template.render(content=content_html)

    output_path = OUTPUT_DIR / f"{session_id}_cv.pdf"
    HTML(string=html_str).write_pdf(str(output_path))
    return output_path


def generate_cover_letter_pdf(session_id: str, cover_letter_text: str) -> Path:
    template = _jinja_env.get_template("cover_letter.html")
    content_html = _markdown_to_html_paragraphs(cover_letter_text)
    html_str = template.render(content=content_html)

    output_path = OUTPUT_DIR / f"{session_id}_cover_letter.pdf"
    HTML(string=html_str).write_pdf(str(output_path))
    return output_path
