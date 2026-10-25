import io
import json
import os
import re

RTL = re.compile(r"[\u0600-\u06FF]")
FONTS = ["fonts/NotoNastaliqUrdu-Regular.ttf", "fonts/NotoSans-Regular.ttf",
         "C:/Windows/Fonts/arial.ttf", "C:/Windows/Fonts/tahoma.ttf",
         "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]


def to_json(sections) -> bytes:
    return json.dumps([{"title": t, "text": x} for t, x in sections],
                      ensure_ascii=False, indent=2).encode("utf-8")


def to_docx(sections) -> bytes:
    from docx import Document
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    d = Document()
    d.add_heading("Document Summaries", 0)
    for title, text in sections:
        d.add_heading(title, 1)
        for para in text.split("\n"):
            p = d.add_paragraph(para)
            if RTL.search(para):
                p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    buf = io.BytesIO()
    d.save(buf)
    return buf.getvalue()


def to_pdf(sections) -> bytes:
    """Uses a Unicode TTF font so Urdu/Hindi/Arabic text is embedded (put one in fonts/)."""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.utils import simpleSplit
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.pdfgen import canvas
    font = "Helvetica"
    for p in FONTS:
        if os.path.exists(p):
            pdfmetrics.registerFont(TTFont("U", p))
            font = "U"
            break
    try:
        import arabic_reshaper
        from bidi.algorithm import get_display
        shape = lambda s: get_display(arabic_reshaper.reshape(s))
    except ImportError:
        shape = lambda s: s
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    W, H = A4
    y = H - 50

    def write(txt, size):
        nonlocal y
        c.setFont(font, size)
        for para in txt.split("\n"):
            for ln in simpleSplit(para, font, size, W - 100) or [""]:
                if y < 50:
                    c.showPage(); c.setFont(font, size); y = H - 50
                if RTL.search(ln):
                    c.drawRightString(W - 50, y, shape(ln))
                else:
                    c.drawString(50, y, ln)
                y -= size + 4

    for title, text in sections:
        write(title, 14)
        y -= 4
        write(text, 11)
        y -= 14
    c.save()
    return buf.getvalue()


def to_md(sections) -> bytes:
    return "\n\n".join(f"## {t}\n\n{x}" for t, x in sections).encode("utf-8")


def to_txt(sections) -> bytes:
    return "\n\n".join(f"== {t} ==\n{x}" for t, x in sections).encode("utf-8")
