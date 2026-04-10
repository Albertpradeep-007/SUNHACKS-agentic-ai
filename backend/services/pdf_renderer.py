from __future__ import annotations

from datetime import datetime
from pathlib import Path
import re

import markdown
from jinja2 import Environment, FileSystemLoader

TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "templates"


def _markdown_to_plain_lines(markdown_text: str) -> list[str]:
    lines: list[str] = []
    for raw_line in markdown_text.splitlines():
        line = raw_line.strip()
        if not line:
            lines.append("")
            continue

        line = re.sub(r"^#{1,6}\s*", "", line)
        line = re.sub(r"^[-*]\s+", "- ", line)
        line = re.sub(r"\*\*(.*?)\*\*", r"\1", line)
        line = re.sub(r"\*(.*?)\*", r"\1", line)
        line = re.sub(r"`(.*?)`", r"\1", line)
        lines.append(line)
    return lines


def _render_with_reportlab(report_md: str, output: Path) -> str:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import inch
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

    styles = getSampleStyleSheet()
    story = []

    for line in _markdown_to_plain_lines(report_md):
        if not line:
            story.append(Spacer(1, 0.14 * inch))
            continue
        if line.startswith("# "):
            story.append(Paragraph(line[2:], styles["Heading1"]))
        elif line.startswith("## "):
            story.append(Paragraph(line[3:], styles["Heading2"]))
        elif line.startswith("- "):
            story.append(Paragraph(f"• {line[2:]}", styles["BodyText"]))
        else:
            story.append(Paragraph(line, styles["BodyText"]))

    doc = SimpleDocTemplate(str(output), pagesize=A4, leftMargin=40, rightMargin=40, topMargin=40, bottomMargin=32)
    doc.build(story)
    return str(output)


def render_pdf(report_md: str, output_path: str, title: str = "PEIP Risk Report") -> str:
    html_body = markdown.markdown(report_md, extensions=["tables"])
    env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)), autoescape=True)
    template = env.get_template("report.html")
    html = template.render(title=title, generated_at=datetime.utcnow().isoformat(), body=html_body)

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    try:
        from weasyprint import HTML as WeasyprintHTML  # pyright: ignore[reportMissingImports]

        WeasyprintHTML(string=html, base_url=str(TEMPLATE_DIR)).write_pdf(str(output))
        return str(output)
    except Exception:
        try:
            return _render_with_reportlab(report_md, output)
        except Exception as fallback_exc:
            raise RuntimeError(
                "PDF generation failed. Install WeasyPrint native libs or use reportlab fallback dependencies."
            ) from fallback_exc
