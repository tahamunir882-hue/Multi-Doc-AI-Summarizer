import hashlib
import hmac
import os
import re
import secrets
import smtplib
import sqlite3
import time
from email.message import EmailMessage

import streamlit as st

from db.database import get_conn
from db.models import init_db
from src import security

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _hash(password: str, salt: bytes) -> str:
    return hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 200_000).hex()


def signup(name: str, email: str, password: str):
    if not name.strip() or not EMAIL_RE.match(email.strip()):
        return False, "Please enter your name and a valid email address."
    if len(password) < 6:
        return False, "Password must be at least 6 characters."
    salt = os.urandom(16)
    try:
        with get_conn() as c:
            c.execute("INSERT INTO users(email, name, salt, pw_hash) VALUES(?,?,?,?)",
                      (email.strip().lower(), name.strip(), salt.hex(), _hash(password, salt)))
        return True, "Account created. Please log in."
    except sqlite3.IntegrityError:
        return False, "This email is already registered."


def is_locked(email):
    return security.is_locked(email.strip().lower())


def login(email: str, password: str):
    email = email.strip().lower()
    if security.is_locked(email):
        return None
    with get_conn() as c:
        row = c.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
    ok = row and hmac.compare_digest(row["pw_hash"], _hash(password, bytes.fromhex(row["salt"])))
    if not ok:
        security.record_fail(email)
        return None
    security.clear_fails(email)
    user = {"id": row["id"], "name": row["name"], "email": row["email"]}
    security.audit(user["id"], "login")
    return {**user, "token": security.create_token(user)}


def current_user():
    return st.session_state.get("user")


def require_login():
    """Call at the top of every protected page. Checks the JWT session token."""
    init_db()
    user = current_user()
    if not user or not security.verify_token(user.get("token", "")):
        st.session_state.pop("user", None)
        st.warning("Please log in first (your session may have expired).")
        st.page_link("pages/1_Login.py", label="Go to Login")
        st.stop()
    return user


def logout():
    if current_user():
        security.audit(current_user()["id"], "logout")
    for k in ("user", "results", "insights", "compare", "chat", "rag_key", "rag_index", "loaded_cid"):
        st.session_state.pop(k, None)


# ---------- forgot password (6-digit code, valid 10 minutes) ----------
def _smtp_ready():
    return bool(os.getenv("SMTP_HOST") and os.getenv("SMTP_USER") and os.getenv("SMTP_PASS"))


def _send_mail(to, code):
    msg = EmailMessage()
    msg["Subject"], msg["To"] = "Your password reset code", to
    msg["From"] = os.getenv("SMTP_FROM") or os.getenv("SMTP_USER")
    msg.set_content(f"Your Universal AI password reset code is {code}. It is valid for 10 minutes.\n"
                    "If you did not ask for this, you can ignore this email.")
    with smtplib.SMTP(os.getenv("SMTP_HOST"), int(os.getenv("SMTP_PORT", "587")), timeout=20) as s:
        s.starttls()
        s.login(os.getenv("SMTP_USER"), os.getenv("SMTP_PASS"))
        s.send_message(msg)


def request_reset(email):
    """Returns (status, code). status: sent | demo (no email server set up: code shown on screen) | none | limited | error"""
    email = email.strip().lower()
    if security.rate_limited("reset:" + email, 3, 600):
        return "limited", None
    with get_conn() as c:
        if not c.execute("SELECT 1 FROM users WHERE email=?", (email,)).fetchone():
            return ("sent" if _smtp_ready() else "none"), None      # do not reveal which emails exist
        code = f"{secrets.randbelow(10**6):06d}"
        c.execute("INSERT OR REPLACE INTO password_resets(email, code_hash, expires, attempts) VALUES(?,?,?,0)",
                  (email, hashlib.sha256(code.encode()).hexdigest(), time.time() + 600))
    if not _smtp_ready():
        return "demo", code
    try:
        _send_mail(email, code)
    except Exception:
        return "error", None
    return "sent", None


def reset_password(email, code, new_password):
    email = email.strip().lower()
    if len(new_password) < 6:
        return False, "Password must be at least 6 characters."
    with get_conn() as c:
        row = c.execute("SELECT * FROM password_resets WHERE email=?", (email,)).fetchone()
        if not row or row["expires"] < time.time():
            return False, "Code expired or not requested. Please request a new code."
        if row["attempts"] >= 5:
            c.execute("DELETE FROM password_resets WHERE email=?", (email,))
            return False, "Too many wrong codes. Please request a new code."
        if not hmac.compare_digest(row["code_hash"], hashlib.sha256(code.strip().encode()).hexdigest()):
            c.execute("UPDATE password_resets SET attempts=attempts+1 WHERE email=?", (email,))
            return False, "Wrong code."
        salt = os.urandom(16)
        c.execute("UPDATE users SET salt=?, pw_hash=? WHERE email=?", (salt.hex(), _hash(new_password, salt), email))
        uid = c.execute("SELECT id FROM users WHERE email=?", (email,)).fetchone()["id"]
        c.execute("DELETE FROM password_resets WHERE email=?", (email,))
    security.clear_fails(email)
    security.audit(uid, "password_reset")
    return True, "Password changed. You can log in now."
