from src.ui import setup
import datetime
import re

import streamlit as st

from db.models import get_documents, get_text
from src.auth import require_login
from src.exporter import to_docx, to_md, to_pdf, to_txt
from src.language import LANGUAGES
from src.modes import run_task

setup()
user = require_login()
st.title("📑 Report Generator")

docs = get_documents(user["id"])
if not docs:
    st.info("Upload documents first.")
    st.stop()
names = {d["id"]: d["filename"] for d in docs}
title = st.text_input("Report title", "Document Analysis Report")
chosen = st.multiselect("Documents", list(names), format_func=names.get, default=list(names)[:5])
lang = st.selectbox("Language", list(LANGUAGES.values()))

INSTR = ("Write a professional report in markdown with these headings: Executive Summary, Document Overview, "
         "Key Findings, Analysis, Comparison (a table if there are several documents), Research Gaps, "
         "Recommendations, References (list the source documents and any references they mention), "
         "Appendix (key figures, dates, terms).")
if st.button("Generate professional report", type="primary", disabled=not chosen):
    with st.spinner("Writing report..."):
        body = run_task({names[i]: get_text(i) for i in chosen}, INSTR, lang)
    cover = f"{title}\n\nGenerated: {datetime.date.today():%d %B %Y}\nPrepared for: {user['name']}\n\nDocuments analysed:\n" + \
            "\n".join(f"- {names[i]}" for i in chosen)
    st.session_state["report"] = [("Cover Page", cover), ("Report", body)]

if rep := st.session_state.get("report"):
    st.divider()
    st.markdown(f"## {rep[0][1].splitlines()[0]}")
    st.caption("\n".join(rep[0][1].splitlines()[2:]))
    st.markdown(rep[1][1])
    plain = [(t, re.sub(r"^#+\s*", "", x, flags=re.M).replace("**", "")) for t, x in rep]
    c1, c2, c3, c4 = st.columns(4)
    c1.download_button("⬇ PDF", to_pdf(plain), "report.pdf", "application/pdf")
    c2.download_button("⬇ DOCX", to_docx(plain), "report.docx")
    c3.download_button("⬇ MD", to_md(rep), "report.md")
    c4.download_button("⬇ TXT", to_txt(plain), "report.txt")
