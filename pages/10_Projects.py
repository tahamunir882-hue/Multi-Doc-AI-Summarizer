from src.ui import setup
import streamlit as st

from db.models import create_project, delete_document, delete_project, get_documents, list_projects, project_labels
from src.auth import require_login

setup()
user = require_login()
st.title("📚 Projects & Documents")

labels = project_labels(user["id"])
c1, c2, c3 = st.columns([3, 3, 1])
name = c1.text_input("New project / folder name", placeholder="e.g. Semester 5")
parent = c2.selectbox("Inside folder", [0] + list(labels), format_func=lambda i: "— top level —" if i == 0 else labels[i])
if c3.button("Create", disabled=not name.strip()):
    create_project(user["id"], name, parent or None)
    st.rerun()


def show_docs(pid):
    for d in get_documents(user["id"], pid):
        a, b = st.columns([5, 1])
        a.markdown(f"📄 **{d['filename']}** · {d['language']} · {d['char_count']:,} chars · 🏷 {d['tags'] or '-'}")
        if b.button("🗑", key=f"d{d['id']}"):
            delete_document(d["id"], user["id"])
            st.rerun()


for p in list_projects(user["id"]):
    with st.expander(f"📁 {labels.get(p['id'], p['name'])} ({p['docs']} documents)"):
        show_docs(p["id"])
        if st.button("Delete whole project", key=f"p{p['id']}"):
            delete_project(p["id"], user["id"])
            st.rerun()

with st.expander("📄 Documents without a project"):
    show_docs(0)
