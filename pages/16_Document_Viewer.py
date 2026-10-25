from src.ui import setup
import html

import streamlit as st

from db.models import get_documents, get_text
from src.auth import require_login
from src.language import LANGUAGES
from src.summarizer import _ask

setup()
user = require_login()
st.title("📖 Document Viewer")

docs = get_documents(user["id"])
if not docs:
    st.info("Upload documents first.")
    st.stop()
names = {d["id"]: d["filename"] for d in docs}

if target := st.session_state.pop("view", None):          # opened from a citation
    st.session_state["vdoc"], st.session_state["vchunk"] = target[0], target[2]
    st.session_state["vpage"] = max(1, min(int(target[1]), len(get_text(target[0]).split("\f"))))
doc = st.selectbox("Document", list(names), format_func=names.get, key="vdoc")
pages = get_text(doc).split("\f")
n = len(pages)
st.session_state["vpage"] = max(1, min(st.session_state.get("vpage", 1), n))

left, right = st.columns([3, 2])
with left:
    page = st.number_input(f"Page / slide (1-{n})", 1, n, key="vpage")
    text, chunk = pages[page - 1], st.session_state.get("vchunk", "").strip()
    body = html.escape(text)
    if chunk and chunk in text:
        body = body.replace(html.escape(chunk), f"<mark style='background:#f0abfc;color:#000'>{html.escape(chunk)}</mark>", 1)
    st.markdown(f"<div style='white-space:pre-wrap;background:rgba(255,255,255,.05);border:1px solid rgba(217,70,239,.3);"
                f"border-radius:14px;padding:18px;max-height:560px;overflow:auto'>{body or '(empty page)'}</div>",
                unsafe_allow_html=True)
    st.caption("Showing the extracted text of this page. Highlighted = the evidence cited in chat.")

with right:
    st.subheader("AI panel")
    lang = st.selectbox("Language", list(LANGUAGES.values()))
    tasks = {"📝 Summary": "Summarize this page in 3-5 sentences.",
             "🔑 Key findings & facts": "List the key findings and important facts on this page as bullets.",
             "❓ Questions": "Write 5 useful questions this page can answer, with short answers."}
    for label, instr in tasks.items():
        if st.button(label, disabled=not text.strip()):
            with st.spinner("..."):
                st.markdown(_ask(f"{instr} Write in {lang}. Use only this text.\n\n{text[:8000]}", 800))
