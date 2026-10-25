from src.ui import setup
import streamlit as st

from db.models import get_documents, get_text
from src.auth import require_login
from src.exporter import to_docx, to_md, to_pdf
from src.language import LANGUAGES
from src.modes import MODES, run_task

setup()
user = require_login()
st.title("🎯 Study · Research · Business · Contract")

docs = get_documents(user["id"])
if not docs:
    st.info("Upload documents first.")
    st.stop()

cat = st.radio("Mode", list(MODES), horizontal=True)
task = st.selectbox("What do you want to create?", list(MODES[cat]))
if cat.startswith("⚖️"):
    st.warning("This is a document-analysis tool, not legal advice.")

names = {d["id"]: d["filename"] for d in docs}
chosen = st.multiselect("Documents", list(names), format_func=names.get, default=list(names)[:1])
lang = st.selectbox("Output language", list(LANGUAGES.values()))

if st.button("Generate", type="primary", disabled=not chosen):
    with st.spinner("Working..."):
        st.session_state["mode_out"] = (task, run_task({names[i]: get_text(i) for i in chosen}, MODES[cat][task], lang))

if out := st.session_state.get("mode_out"):
    st.divider()
    st.markdown(out[1])
    sec = [out]
    c1, c2, c3 = st.columns(3)
    c1.download_button("⬇ PDF", to_pdf(sec), "output.pdf", "application/pdf")
    c2.download_button("⬇ DOCX", to_docx(sec), "output.docx")
    c3.download_button("⬇ MD", to_md(sec), "output.md")
