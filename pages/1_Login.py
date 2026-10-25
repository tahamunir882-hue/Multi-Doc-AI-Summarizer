from src.ui import setup
import streamlit as st

from db.models import init_db
from src import auth
from src.translator import t

init_db()
setup("Login")


def enter(user):
    st.session_state["user"] = user
    st.switch_page("pages/2_Dashboard.py")


_, mid, _ = st.columns([1, 2, 1])
with mid:
    st.markdown('<div style="text-align:center;font-size:3rem">📄</div>', unsafe_allow_html=True)
    st.title(t("login"))
    st.caption("Welcome! Sign in to summarize your documents with AI.")
    tab_in, tab_up, tab_fp = st.tabs([t("login"), t("signup"), "Forgot password"])

    with tab_in:
        email = st.text_input(t("email"), key="li_email")
        pw = st.text_input(t("password"), type="password", key="li_pw")
        if st.button(t("login"), key="btn_login"):
            user = auth.login(email, pw)
            if user:
                enter(user)
            else:
                st.error("Too many attempts. Try again in 5 minutes." if auth.is_locked(email) else "Wrong email or password.")
        st.caption("Forgot your password? Open the **Forgot password** tab.")

    with tab_up:
        name = st.text_input(t("name"), key="su_name")
        email2 = st.text_input(t("email"), key="su_email")
        pw2 = st.text_input(t("password"), type="password", key="su_pw")
        if st.button(t("signup"), key="btn_signup"):
            ok, msg = auth.signup(name, email2, pw2)
            if ok and (user := auth.login(email2, pw2)):
                enter(user)                      # signed up -> logged in automatically
            else:
                st.error(msg)

    with tab_fp:
        fe = st.text_input(t("email"), key="fp_email")
        if st.button("Send reset code"):
            status, code = auth.request_reset(fe)
            if status == "demo":
                st.info(f"Email is not set up on this server, so your code is shown here: **{code}**")
            elif status == "limited":
                st.error("Too many requests. Please wait 10 minutes.")
            elif status == "error":
                st.error("Could not send the email. Please try again later.")
            elif status == "none":
                st.error("No account found with this email.")
            else:
                st.success("If this email has an account, a 6-digit code was sent. It is valid for 10 minutes.")
        code_in = st.text_input("6-digit code", key="fp_code")
        newpw = st.text_input("New password", type="password", key="fp_new")
        if st.button("Reset password"):
            ok, msg = auth.reset_password(fe, code_in, newpw)
            (st.success if ok else st.error)(msg)
