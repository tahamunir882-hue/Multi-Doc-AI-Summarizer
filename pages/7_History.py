from src.ui import setup
import streamlit as st

from db.models import delete_summary, search_summaries
from src.auth import require_login
from src.translator import language_selector

setup()
user = require_login()
st.title("🕘 History")

q = st.text_input("Search (file name or text)")
rows = search_summaries(user["id"], q)
st.caption(f"{len(rows)} summaries")
for r in rows:
    with st.expander(f"{r['title']} - {r['out_language']}, {r['length']} - {r['created_at']}"):
        st.write(r["content"])
        c1, c2 = st.columns(2)
        c1.download_button("⬇ Text", r["content"], f"summary_{r['id']}.txt", key=f"dl{r['id']}")
        if c2.button("🗑 Delete", key=f"del{r['id']}"):
            delete_summary(r["id"], user["id"])
            st.rerun()
