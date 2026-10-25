from src.ui import setup
import streamlit as st
import streamlit.components.v1 as components

from db.models import get_documents, get_text
from src.ai_tools import diff_matrix, html_diff
from src.auth import require_login
from src.language import LANGUAGES

setup()
user = require_login()
st.title("📊 Compare Documents")

docs = get_documents(user["id"])
if len(docs) < 2:
    st.info("Upload at least two documents (or two versions of one document).")
    st.stop()
names = {d["id"]: d["filename"] for d in docs}
c1, c2, c3 = st.columns(3)
a = c1.selectbox("Document A", list(names), format_func=names.get)
b = c2.selectbox("Document B", list(names), format_func=names.get, index=1)
lang = c3.selectbox("Language", list(LANGUAGES.values()))

tab1, tab2 = st.tabs(["🧮 AI comparison matrix", "↔️ Side-by-side version diff"])
with tab1:
    if st.button("Compare with AI"):
        with st.spinner("Comparing..."):
            st.markdown(diff_matrix(names[a], get_text(a), names[b], get_text(b), lang))
with tab2:
    css = ("<style>body{font-family:sans-serif;font-size:13px;background:#fff}table.diff{width:100%}"
           ".diff_add{background:#b7f5c0}.diff_chg{background:#fff1a8}.diff_sub{background:#ffc2c2}"
           ".diff_header{background:#eee}</style>")
    components.html(css + html_diff(get_text(a), get_text(b)), height=520, scrolling=True)
    st.caption("Green = added in B, red = removed from A, yellow = changed.")
