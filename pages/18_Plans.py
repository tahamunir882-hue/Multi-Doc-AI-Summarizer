from src.ui import cards, section, setup
import os

import streamlit as st

from db.database import get_conn
from db.models import PLANS, daily_count, get_setting, set_setting
from src.auth import require_login
from src.security import audit

setup()
user = require_login()
st.title("💎 Plans")
section("Choose your plan", "Simple monthly pricing")
cards([("🆓", "Free · $0", "5 documents per day · summaries · chat · export"),
       ("⭐", "Pro · $3 / month", "10 documents per day · advanced search · research · compare · OCR · all exports"),
       ("🏢", "Business · $7 / month", "Unlimited documents · priority features · analytics · everything in Pro")])

plan = get_setting(user["id"], "plan", "free")
st.markdown(f"**Your plan:** {plan.title()} · today {daily_count(user['id'])} of {PLANS[plan] or 'unlimited'} documents")
demo = os.getenv("DEMO_PLANS", "1") == "1"
if demo:
    new = st.selectbox("Switch plan (test mode, no payment)", list(PLANS), index=list(PLANS).index(plan), format_func=str.title)
    if st.button("Switch plan", disabled=new == plan):
        set_setting(user["id"], "plan", new)
        audit(user["id"], "plan_change", new)
        st.rerun()
else:
    c1, c2 = st.columns(2)
    for col, key, price in ((c1, "PRO", 3), (c2, "BUSINESS", 7)):
        if link := os.getenv(f"PAYMENT_LINK_{key}"):
            col.link_button(f"Upgrade to {key.title()} · ${price}/month", link, use_container_width=True)
    st.caption("After payment, your plan is activated by the admin (usually within a day).")
    if plan != "free" and st.button("Downgrade to Free"):
        set_setting(user["id"], "plan", "free")
        st.rerun()

if os.getenv("ADMIN_EMAIL", "").strip().lower() == user["email"]:
    st.subheader("🛠 Admin: activate a plan")
    target = st.text_input("User email").strip().lower()
    chosen = st.selectbox("Plan", list(PLANS), key="adm_plan")
    if st.button("Set plan"):
        with get_conn() as c:
            row = c.execute("SELECT id FROM users WHERE email=?", (target,)).fetchone()
        if row:
            set_setting(row["id"], "plan", chosen)
            audit(user["id"], "admin_set_plan", f"{target} -> {chosen}")
            st.success("Plan updated.")
        else:
            st.error("No user with this email.")
