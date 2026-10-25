from src.ui import setup
import json
import re

import pandas as pd
import streamlit as st

from src.auth import require_login
from src.language import LANGUAGES
from src.summarizer import _ask

setup()
require_login()
st.title("📈 Data Analysis")

f = st.file_uploader("Excel or CSV file", type=["csv", "xlsx"])
if not f:
    st.info("Upload a spreadsheet to get totals, averages, trends, outliers and charts.")
    st.stop()
df = pd.read_csv(f) if f.name.lower().endswith(".csv") else pd.read_excel(f)
st.caption(f"{len(df):,} rows × {len(df.columns)} columns")
st.dataframe(df.head(50), use_container_width=True)

num = df.select_dtypes("number")
if not num.empty:
    st.subheader("Key numbers")
    st.dataframe(pd.DataFrame({"Total": num.sum(), "Average": num.mean(), "Maximum": num.max(), "Minimum": num.min()}),
                 use_container_width=True)
    rows = []
    for col in num:
        s = num[col].dropna()
        q1, q3 = s.quantile(.25), s.quantile(.75)
        out = int(((s < q1 - 1.5 * (q3 - q1)) | (s > q3 + 1.5 * (q3 - q1))).sum())
        h = len(s) // 2
        trend = (s.iloc[h:].mean() - s.iloc[:h].mean()) / abs(s.iloc[:h].mean()) * 100 if h and s.iloc[:h].mean() else 0
        rows.append({"Column": col, "Outliers": out, "Trend (2nd half vs 1st)": f"{trend:+.1f}%"})
    st.subheader("Trends & outliers")
    st.dataframe(pd.DataFrame(rows), use_container_width=True)


def draw(kind, x, ys):
    data = df.head(300).set_index(x)[ys]
    {"line": st.line_chart, "bar": st.bar_chart, "area": st.area_chart}.get(kind, st.line_chart)(data)


st.subheader("Charts")
ask = st.text_input("💬 Describe the chart you want", placeholder="e.g. make a bar chart of sales by month")
if ask:
    raw = _ask('Columns: ' + ", ".join(map(str, df.columns)) + '\nReply ONLY JSON: {"type": "line|bar|area", "x": "<column>", '
               '"y": ["<numeric columns>"]} for this request: ' + ask, 200)
    m = re.search(r"\{.*\}", raw, re.S)
    try:
        spec = json.loads(m.group(0))
        draw(spec["type"], spec["x"], spec["y"])
    except Exception:
        st.warning("Could not build that chart. Try naming the columns.")
else:
    c1, c2, c3 = st.columns(3)
    kind = c1.selectbox("Type", ["line", "bar", "area"])
    x = c2.selectbox("X axis", list(df.columns))
    ys = c3.multiselect("Y axis", list(num.columns), default=list(num.columns)[:1])
    if ys:
        draw(kind, x, ys)

lang = st.selectbox("Insights language", list(LANGUAGES.values()))
if st.button("🧠 AI insights"):
    with st.spinner("Analysing..."):
        st.markdown(_ask(f"Analyse this data in {lang}: main trends, outliers, notable patterns and 3 recommendations. "
                         "Use only the data.\n\n" + df.describe(include="all").to_string()[:6000] + "\n\n" + df.head(20).to_string(), 1500))
