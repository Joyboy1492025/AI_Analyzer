"""Markdown -> styled PDF report."""

import html
import re
from datetime import datetime
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

from config import REPORT_DIR

ACCENT = colors.HexColor("#6d4aff")
DARK = colors.HexColor("#1b1b2f")


def _inline(text: str) -> str:
    """Escape XML, then convert **bold** and `code` to ReportLab markup."""
    text = html.escape(text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"`(.+?)`", r"<font face='Courier'>\1</font>", text)
    return text


def _footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.grey)
    canvas.drawString(2 * cm, 1.2 * cm, "AI Analysis Report")
    canvas.drawRightString(A4[0] - 2 * cm, 1.2 * cm, f"Page {doc.page}")
    canvas.restoreState()


def create_pdf(
    content: str,
    filename: str = "analysis_report.pdf",
    subtitle: str = "",
) -> str:
    path = Path(filename)
    if not path.is_absolute():
        path = REPORT_DIR / path

    doc = SimpleDocTemplate(
        str(path),
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
        title="AI Analysis Report",
    )

    base = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "ReportTitle", parent=base["Title"], textColor=ACCENT, fontSize=24, spaceAfter=4
    )
    sub_style = ParagraphStyle(
        "ReportSub", parent=base["Normal"], textColor=colors.grey, fontSize=9, alignment=1
    )
    h = {
        1: ParagraphStyle("H1", parent=base["Heading1"], textColor=ACCENT, spaceBefore=12),
        2: ParagraphStyle("H2", parent=base["Heading2"], textColor=colors.HexColor("#0f8a5f"), spaceBefore=10),
        3: ParagraphStyle("H3", parent=base["Heading3"], textColor=DARK, spaceBefore=8),
    }
    body = ParagraphStyle("Body", parent=base["BodyText"], leading=15)
    bullet = ParagraphStyle("Bullet", parent=body, leftIndent=16, bulletIndent=4)
    code = ParagraphStyle(
        "Code", parent=body, fontName="Courier", fontSize=8.5, leading=11,
        backColor=colors.HexColor("#f3f1ff"), leftIndent=8,
    )

    story = [Paragraph("AI Analysis Report", title_style)]
    meta = f"Generated {datetime.now():%d %b %Y, %H:%M}"
    if subtitle:
        meta += f"  |  {html.escape(subtitle)}"
    story += [Paragraph(meta, sub_style), Spacer(1, 18)]

    in_code = False
    for raw in content.splitlines():
        line = raw.rstrip()

        if line.strip().startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            story.append(Paragraph(html.escape(line).replace(" ", "&nbsp;") or "&nbsp;", code))
            continue
        if not line.strip():
            story.append(Spacer(1, 6))
            continue
        if re.fullmatch(r"\s*[-*_]{3,}\s*", line):
            story.append(Spacer(1, 8))
            continue

        m = re.match(r"^(#{1,6})\s+(.*)", line)
        if m:
            level = min(len(m.group(1)), 3)
            story.append(Paragraph(_inline(m.group(2)), h[level]))
            continue

        m = re.match(r"^\s*([-*+]|\d+\.)\s+(.*)", line)
        if m:
            marker = "\u2022" if m.group(1) in "-*+" else m.group(1)
            story.append(Paragraph(_inline(m.group(2)), bullet, bulletText=marker))
            continue

        story.append(Paragraph(_inline(line), body))

    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
    return str(path)