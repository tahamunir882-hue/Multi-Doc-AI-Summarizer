from src.ui import setup
import streamlit as st

from db.models import get_documents, get_text
from src.ai_tools import find_contradictions
from src.auth import require_login
from src.language import LANGUAGES

setup()
user = require_login()
st.title("🚨 Contradiction Detector")
st.caption("Shows where documents disagree and why. It does not decide which claim is true.")

docs = get_documents(user["id"])
if len(docs) < 2:
    st.info("Upload at least two documents.")
    st.stop()
names = {d["id"]: d["filename"] for d in docs}
chosen = st.multiselect("Documents (2 or more)", list(names), format_func=names.get, default=list(names)[:3])
lang = st.selectbox("Language", list(LANGUAGES.values()))

if st.button("Detect conflicts", type="primary", disabled=len(chosen) < 2):
    with st.spinner("Comparing claims..."):
        found = find_contradictions({names[i]: get_text(i) for i in chosen}, lang)
    if not found:
        st.success("No clear contradictions found.")
    for c in found:
        with st.expander(f"⚠️ CONFLICT: {c.get('topic', '')}", expanded=True):
            for cl in c.get("claims", []):
                st.markdown(f"**{cl.get('document', '')}**: “{cl.get('claim', '')}”")
            if c.get("possible_reasons"):
                st.markdown("**Possible reasons**")
                for r in c["possible_reasons"]:
                    st.markdown(f"- {r}")
