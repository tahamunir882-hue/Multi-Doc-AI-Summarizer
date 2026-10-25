import streamlit as st

from db.models import init_db
from src.auth import current_user, logout
from src.translator import t
from src.ui import cards, footer, hero, section, setup, stats

init_db()
setup()

user = current_user()

hero()
if user:
    st.success(f"Welcome back, {user['name']}! 👋")
    c1, c2, c3, c4 = st.columns(4)
    c1.page_link("pages/3_Upload_Documents.py", label="📂 Upload")
    c2.page_link("pages/6_Ask_Questions.py", label="💬 Chat")
    c3.page_link("pages/9_Study_Modes.py", label="🎯 Modes")
    c4.page_link("pages/10_Projects.py", label="📚 Projects")
else:
    c1, c2, _ = st.columns([1, 1, 2])
    c1.page_link("pages/1_Login.py", label="🚀 Get Started")
    c2.page_link("pages/8_About.py", label="ℹ️ Learn more")

st.write("")
stats([("18", "Languages"), ("10", "Summary modes"), ("10", "File types"), ("5", "Export formats")])

section("Core intelligence", "Upload 1 or 100 documents in different languages")
cards([
    ("🌐", "Multi-Language", "Auto-detects 17 languages; summarize in English, Urdu, Roman Urdu, Arabic, Hindi and more."),
    ("📚", "Multi-Document Workspace", "Projects keep every document together as one knowledge base."),
    ("🧠", "10 Summary Modes", "Quick, Standard, Detailed, Executive, Academic, Student, Bullet, TL;DR, Findings, Actions."),
    ("🧩", "Cross-Document Intelligence", "Common points, differences, contradictions and missing information."),
    ("💬", "Chat With Documents", "Ask anything; every answer cites [file, page]."),
    ("🔍", "OCR + Scans", "PDF, DOCX, PPTX, CSV, XLSX, TXT and scanned images."),
])
section("Special modes")
cards([
    ("🎓", "Student Mode", "Topics, MCQs, flashcards, definitions and exam questions."),
    ("📖", "Research Mode", "Paper breakdown and literature review across papers."),
    ("🏢", "Business Mode", "Metrics, risks, opportunities and action items."),
    ("⚖️", "Contract Mode", "Parties, terms, obligations, penalties and clauses."),
    ("🔐", "Privacy First", "Private workspace, delete any document or project anytime."),
    ("📤", "Export", "PDF, DOCX, Markdown, TXT and JSON."),
])
section("How it works")
cards([("", "Upload", "Drop files, pick project, mode and language."),
       ("", "Understand", "OCR, language detection, chunking and page tracking."),
       ("", "Analyze", "Summaries, insights and comparisons by AI."),
       ("", "Ask & Export", "Chat with citations, generate reports, download.")], step=True)
footer()
