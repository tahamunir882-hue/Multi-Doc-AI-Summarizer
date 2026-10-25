from src.ui import cards, section, setup
import pandas as pd
import streamlit as st

from db.models import list_projects, recent_summaries, usage, user_stats
from src.auth import require_login
from src.translator import t

setup()
user = require_login()
st.title(f"{t('dashboard')} - {user['name']}")

docs, sums = user_stats(user["id"])
chars, per_day = usage(user["id"])
saved_min = int(chars / 1000 * 0.85)          # ~1000 chars read per minute
c1, c2, c3, c4 = st.columns(4)
c1.metric(t("documents"), docs)
c2.metric(t("summaries"), sums)
c3.metric("Words processed", f"{chars // 6:,}")
c4.metric("⏱ Time saved (est.)", f"{saved_min // 60}h {saved_min % 60}m")

section("Usage analytics", "Summaries created per day")
if per_day:
    st.bar_chart(pd.DataFrame(per_day).set_index("day")["n"])
else:
    st.caption("No activity yet. Upload your first document!")

projects = list_projects(user["id"])
if projects:
    section("Active projects")
    cards([("📁", p["name"], f"{p['docs']} documents") for p in projects[:6]])

st.subheader(t("recent"))
for r in recent_summaries(user["id"], 5):
    with st.expander(f"{r['title']} ({r['out_language']}, {r['length']}) - {r['created_at']}"):
        st.write(r["content"])
