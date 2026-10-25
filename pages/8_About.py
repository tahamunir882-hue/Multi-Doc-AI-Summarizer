from src.ui import setup
import streamlit as st

setup()
st.title("ℹ️ About")
st.markdown("""
**Universal AI: Multilingual Document Intelligence & Research Assistant**
*Upload Anything. Understand Everything.*

- **Input:** PDF, DOCX, PPTX, XLSX, CSV, TXT, images (OCR), audio/video (speech-to-text), web links
- **Languages:** auto-detect 17 languages, output in 18 (incl. Urdu and Roman Urdu)
- **Summaries:** 10 modes + tone/persona
- **Chat:** hybrid RAG (vector + keyword + optional embeddings), page citations, click to open the page
- **Research:** paper breakdown, literature review, research gaps, deep research, contradiction detector, compare
- **Modes:** Student, Business, Contract, Data Analysis, Report Generator, Audio Overview, Mind Map, Agent mode
- **Workspace:** projects with folders, tags, saved chats, history, Notion/webhook integrations
- **Security:** JWT sessions, password hashing, login lock, rate limiting, file validation, encryption at rest, audit log, data retention and delete
- **Plans:** Free / Pro / Business (demo limits)

AI can make mistakes: check important facts in the source documents.
""")
