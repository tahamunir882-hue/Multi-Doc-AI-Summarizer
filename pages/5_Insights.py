from src.ui import setup
import streamlit as st

from db.models import get_documents, get_text
from src.auth import require_login
from src.cross_doc import compare_documents
from src.insights import FIELDS
from src.insights import extract_insights
from src.language import LANGUAGES
from src.summarizer import summarize_document
from src.translator import language_selector

setup()
user = require_login()
st.title("💡 Insights")

docs = get_documents(user["id"])
if not docs:
    st.info("Upload documents first.")
    st.stop()

names = {d["id"]: d["filename"] for d in docs}
chosen = st.multiselect("Documents", list(names), format_func=names.get, default=list(names)[:1])
lang = st.selectbox("Output language", list(LANGUAGES.values()))

if st.button("Extract insights", type="primary", disabled=not chosen):
    store = st.session_state.setdefault("insights", {})
    for did in chosen:
        with st.spinner(names[did]):
            store[did] = extract_insights(get_text(did), lang)
    if len(chosen) > 1:
        with st.spinner("Comparing documents..."):
            short = {names[d]: summarize_document(get_text(d), lang, "short") for d in chosen}
            st.session_state["compare"] = compare_documents(short, lang)

LABELS = {"key_points": "🔑 Key points", "action_items": "✅ Action items", "dates": "📅 Dates",
          "people": "👤 People", "organizations": "🏢 Organizations",
          "numbers": "🔢 Numbers", "risks": "⚠️ Risks"}

for did, ins in st.session_state.get("insights", {}).items():
    if did in chosen:
        st.subheader(f"📄 {names[did]}")
        for f in FIELDS:
            if ins[f]:
                with st.expander(LABELS[f], expanded=f in ("key_points", "risks")):
                    for item in ins[f]:
                        st.markdown(f"- {item}")

cmp = st.session_state.get("compare")
if cmp and len(chosen) > 1:
    st.subheader("🧩 Cross-document comparison")
    for k, label in (("common_themes", "Common themes"), ("differences", "Differences"),
                     ("contradictions", "Contradictions"),
                     ("missing_information", "Missing information")):
        if cmp[k]:
            st.markdown(f"**{label}**")
            for item in cmp[k]:
                st.markdown(f"- {item}")
