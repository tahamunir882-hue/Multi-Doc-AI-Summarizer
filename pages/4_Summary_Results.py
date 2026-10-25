from src.ui import setup
import streamlit as st

from src.auth import require_login
from src.exporter import to_docx, to_json, to_md, to_pdf, to_txt
from src.translator import language_selector, t

setup()
require_login()
st.title(t("results_title"))

res = st.session_state.get("results")
if not res or not res["docs"]:
    st.info(t("no_results"))
    st.stop()

sections = []
if res["combined"]:
    st.subheader(f"🧩 {t('combined')}")
    st.write(res["combined"])
    st.divider()
    sections.append((t("combined"), res["combined"]))

for d in res["docs"]:
    with st.expander(f"📄 {d['name']}  ({d['lang']})", expanded=True):
        st.write(d["summary"])
    sections.append((d["name"], d["summary"]))

c1, c2, c3, c4, c5 = st.columns(5)
c1.download_button("⬇ PDF", to_pdf(sections), "summaries.pdf", "application/pdf")
c2.download_button("⬇ DOCX", to_docx(sections), "summaries.docx")
c3.download_button("⬇ JSON", to_json(sections), "summaries.json", "application/json")
c4.download_button("⬇ MD", to_md(sections), "summaries.md")
c5.download_button("⬇ TXT", to_txt(sections), "summaries.txt")

from db.models import get_setting
from src.ai_tools import send_to_notion

_u = st.session_state["user"]["id"]
if get_setting(_u, "notion_token") and get_setting(_u, "notion_page") and st.button("📝 Send to Notion"):
    try:
        send_to_notion(get_setting(_u, "notion_token"), get_setting(_u, "notion_page"), "Summaries",
                       "\n\n".join(f"{a}\n{b}" for a, b in sections))
        st.success("Sent to Notion.")
    except Exception as e:
        st.error(f"Notion failed: {e}")
