import collections
import os
import time

import jwt

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from db.database import get_conn

MAX_MB = 25
MAGIC = {"pdf": (b"%PDF",), "docx": (b"PK",), "pptx": (b"PK",), "xlsx": (b"PK",),
         "png": (b"\x89PNG",), "jpg": (b"\xff\xd8",), "jpeg": (b"\xff\xd8",)}
_hits = collections.defaultdict(collections.deque)
_fails = {}


def _secret():
    p = os.path.join("data", ".jwt_secret")
    os.makedirs("data", exist_ok=True)
    if not os.path.exists(p):
        open(p, "w").write(os.urandom(32).hex())
    return open(p).read()


def create_token(user, hours=8):
    return jwt.encode({**user, "exp": int(time.time() + hours * 3600)}, _secret(), algorithm="HS256")


def verify_token(token):
    try:
        return jwt.decode(token, _secret(), algorithms=["HS256"])
    except Exception:
        return None


def rate_limited(user_id, max_calls=60, window=60):
    q, now = _hits[user_id], time.time()
    while q and now - q[0] > window:
        q.popleft()
    if len(q) >= max_calls:
        return True
    q.append(now)
    return False


def is_locked(email, max_fails=5, lock_s=300):
    n, first = _fails.get(email, (0, 0))
    if n and time.time() - first > lock_s:
        _fails.pop(email, None)
        return False
    return n >= max_fails


def record_fail(email):
    n, first = _fails.get(email, (0, time.time()))
    _fails[email] = (n + 1, first)


def clear_fails(email):
    _fails.pop(email, None)


def validate_file(name, data):
    ext = name.rsplit(".", 1)[-1].lower()
    if len(data) > MAX_MB * 1024 * 1024:
        raise ValueError(f"File is larger than {MAX_MB} MB")
    sig = MAGIC.get(ext)
    if sig and not data.startswith(sig):
        raise ValueError("File content does not match its extension (blocked)")


def audit(user_id, action, detail=""):
    with get_conn() as c:
        c.execute("INSERT INTO audit_logs(user_id, action, detail) VALUES(?,?,?)", (user_id, action, detail[:200]))


def recent_audit(user_id, n=20):
    with get_conn() as c:
        return c.execute("SELECT created_at, action, detail FROM audit_logs WHERE user_id=? ORDER BY id DESC LIMIT ?",
                         (user_id, n)).fetchall()
