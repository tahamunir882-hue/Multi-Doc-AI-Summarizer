from src.ui import setup
import streamlit as st

from db.models import delete_all, user_stats
from src.auth import require_login

setup()
user = require_login()
st.title("⚙️ Settings & Privacy")

docs, sums = user_stats(user["id"])
st.markdown(f"**Account:** {user['name']} ({user['email']})  \n**Stored:** {docs} documents, {sums} summaries")
st.info("Private workspace: your files and summaries are stored locally in the `data/` folder and are "
        "only visible after you log in. Passwords are stored as salted hashes.")

st.subheader("Delete my data")
sure = st.checkbox("I understand this deletes all my documents, projects and summaries permanently")
if st.button("Delete everything", disabled=not sure):
    delete_all(user["id"])
    for k in ("results", "insights", "compare", "rag_key", "rag_index", "chat", "mode_out"):
        st.session_state.pop(k, None)
    st.success("All your documents, projects and summaries were deleted.")

from db.models import get_setting, set_setting

st.subheader("🔌 Integrations")
hook = st.text_input("Webhook URL (receives every new summary as JSON)", value=get_setting(user["id"], "webhook"),
                     placeholder="https://hooks.example.com/...")
if st.button("Save webhook"):
    set_setting(user["id"], "webhook", hook.strip())
    st.success("Saved.")

from db.models import purge_old
from src.security import audit, recent_audit

st.subheader("📝 Notion")
ntok = st.text_input("Notion integration token", value=get_setting(user["id"], "notion_token"), type="password")
npage = st.text_input("Notion parent page ID", value=get_setting(user["id"], "notion_page"))
if st.button("Save Notion settings"):
    set_setting(user["id"], "notion_token", ntok.strip())
    set_setting(user["id"], "notion_page", npage.strip())
    st.success("Saved. A 'Send to Notion' button now appears on the results page.")

st.subheader("🗓️ Data retention")
days = st.number_input("Delete my documents older than (days)", 1, 3650, 90)
if st.button("Delete old documents"):
    n = purge_old(user["id"], days)
    audit(user["id"], "purge_old", f"{n} documents older than {days} days")
    st.success(f"Deleted {n} documents.")

st.subheader("🧾 Audit log (last 20 actions)")
st.dataframe([dict(r) for r in recent_audit(user["id"])], use_container_width=True)
