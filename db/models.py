from db.database import get_conn


def init_db():
    with get_conn() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            salt TEXT NOT NULL,
            pw_hash TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS documents(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            filename TEXT NOT NULL,
            language TEXT,
            char_count INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS summaries(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            document_id INTEGER,          -- NULL = combined summary
            out_language TEXT,
            length TEXT,
            content TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        """)


def add_document(user_id, filename, language, char_count, project_id=None):
    with get_conn() as c:
        cur = c.execute(
            "INSERT INTO documents(user_id, filename, language, char_count, project_id) VALUES(?,?,?,?,?)",
            (user_id, filename, language, char_count, project_id))
        return cur.lastrowid


def add_summary(user_id, document_id, out_language, length, content):
    with get_conn() as c:
        c.execute(
            "INSERT INTO summaries(user_id, document_id, out_language, length, content) VALUES(?,?,?,?,?)",
            (user_id, document_id, out_language, length, content))


def user_stats(user_id):
    with get_conn() as c:
        docs = c.execute("SELECT COUNT(*) n FROM documents WHERE user_id=?", (user_id,)).fetchone()["n"]
        sums = c.execute("SELECT COUNT(*) n FROM summaries WHERE user_id=?", (user_id,)).fetchone()["n"]
    return docs, sums


def recent_summaries(user_id, limit=10):
    with get_conn() as c:
        return c.execute("""
            SELECT s.id, COALESCE(d.filename, 'Combined summary') AS title,
                   s.out_language, s.length, s.content, s.created_at
            FROM summaries s LEFT JOIN documents d ON d.id = s.document_id
            WHERE s.user_id=? ORDER BY s.id DESC LIMIT ?""", (user_id, limit)).fetchall()


# ---------- extra helpers (documents text, history search) ----------
import os


def save_text(doc_id, text):
    os.makedirs(os.path.join("data", "uploads"), exist_ok=True)
    with open(os.path.join("data", "uploads", f"{doc_id}.txt"), "w", encoding="utf-8") as f:
        f.write(text)


def get_text(doc_id):
    p = os.path.join("data", "uploads", f"{doc_id}.txt")
    return open(p, encoding="utf-8").read() if os.path.exists(p) else ""


def get_documents(user_id):
    with get_conn() as c:
        return c.execute("SELECT id, filename, language, char_count, created_at FROM documents "
                         "WHERE user_id=? ORDER BY id DESC", (user_id,)).fetchall()


def search_summaries(user_id, q=""):
    with get_conn() as c:
        return c.execute("""
            SELECT s.id, COALESCE(d.filename, 'Combined summary') AS title,
                   s.out_language, s.length, s.content, s.created_at
            FROM summaries s LEFT JOIN documents d ON d.id = s.document_id
            WHERE s.user_id=? AND (s.content LIKE ? OR COALESCE(d.filename,'') LIKE ?)
            ORDER BY s.id DESC""", (user_id, f"%{q}%", f"%{q}%")).fetchall()


def delete_summary(summary_id, user_id):
    with get_conn() as c:
        c.execute("DELETE FROM summaries WHERE id=? AND user_id=?", (summary_id, user_id))


# ---------- projects + privacy (these definitions override the ones above) ----------
_init_base = init_db


def init_db():
    _init_base()
    with get_conn() as c:
        c.execute("CREATE TABLE IF NOT EXISTS projects(id INTEGER PRIMARY KEY AUTOINCREMENT, "
                  "user_id INTEGER NOT NULL, name TEXT NOT NULL, created_at TEXT DEFAULT CURRENT_TIMESTAMP)")
        have = [r[1] for r in c.execute("PRAGMA table_info(documents)")]
        for col in ("project_id INTEGER", "tags TEXT"):
            if col.split()[0] not in have:
                c.execute(f"ALTER TABLE documents ADD COLUMN {col}")
        c.execute("CREATE TABLE IF NOT EXISTS settings(user_id INTEGER, k TEXT, v TEXT, PRIMARY KEY(user_id, k))")
        if "parent_id" not in [r[1] for r in c.execute("PRAGMA table_info(projects)")]:
            c.execute("ALTER TABLE projects ADD COLUMN parent_id INTEGER")
        c.execute("CREATE TABLE IF NOT EXISTS password_resets(email TEXT PRIMARY KEY, code_hash TEXT, expires REAL, attempts INTEGER DEFAULT 0)")
        c.execute("CREATE TABLE IF NOT EXISTS audit_logs(id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, action TEXT, detail TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP)")
        c.execute("CREATE TABLE IF NOT EXISTS conversations(id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, title TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP)")
        c.execute("CREATE TABLE IF NOT EXISTS messages(id INTEGER PRIMARY KEY AUTOINCREMENT, conversation_id INTEGER NOT NULL, role TEXT, content TEXT, sources TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP)")


def create_project(user_id, name):
    with get_conn() as c:
        c.execute("INSERT INTO projects(user_id, name) VALUES(?,?)", (user_id, name.strip()))


def list_projects(user_id):
    with get_conn() as c:
        return c.execute("SELECT p.id, p.name, COUNT(d.id) AS docs FROM projects p "
                         "LEFT JOIN documents d ON d.project_id = p.id WHERE p.user_id=? "
                         "GROUP BY p.id ORDER BY p.id DESC", (user_id,)).fetchall()


def get_documents(user_id, project_id=None):
    """project_id None = all documents, 0 = documents without a project."""
    q, args = "SELECT id, filename, language, char_count, created_at, project_id, tags FROM documents WHERE user_id=?", [user_id]
    if project_id == 0:
        q += " AND project_id IS NULL"
    elif project_id:
        q += " AND project_id=?"
        args.append(project_id)
    with get_conn() as c:
        return c.execute(q + " ORDER BY id DESC", args).fetchall()


def delete_document(doc_id, user_id):
    with get_conn() as c:
        if c.execute("SELECT 1 FROM documents WHERE id=? AND user_id=?", (doc_id, user_id)).fetchone():
            c.execute("DELETE FROM summaries WHERE document_id=?", (doc_id,))
            c.execute("DELETE FROM documents WHERE id=?", (doc_id,))
    p = os.path.join("data", "uploads", f"{doc_id}.txt")
    if os.path.exists(p):
        os.remove(p)


def delete_project(project_id, user_id):
    for d in get_documents(user_id, project_id):
        delete_document(d["id"], user_id)
    with get_conn() as c:
        c.execute("DELETE FROM projects WHERE id=? AND user_id=?", (project_id, user_id))


def delete_all(user_id):
    for d in get_documents(user_id):
        delete_document(d["id"], user_id)
    with get_conn() as c:
        c.execute("DELETE FROM summaries WHERE user_id=?", (user_id,))
        c.execute("DELETE FROM projects WHERE user_id=?", (user_id,))


def set_tags(doc_id, tags):
    with get_conn() as c:
        c.execute("UPDATE documents SET tags=? WHERE id=?", (tags, doc_id))


def usage(user_id):
    with get_conn() as c:
        chars = c.execute("SELECT COALESCE(SUM(char_count),0) n FROM documents WHERE user_id=?", (user_id,)).fetchone()["n"]
        days = c.execute("SELECT date(created_at) day, COUNT(*) n FROM summaries WHERE user_id=? "
                         "GROUP BY day ORDER BY day DESC LIMIT 14", (user_id,)).fetchall()
    return chars, [dict(d) for d in reversed(days)]


def get_setting(user_id, key, default=""):
    with get_conn() as c:
        r = c.execute("SELECT v FROM settings WHERE user_id=? AND k=?", (user_id, key)).fetchone()
    return r["v"] if r else default


def set_setting(user_id, key, value):
    with get_conn() as c:
        c.execute("INSERT OR REPLACE INTO settings(user_id, k, v) VALUES(?,?,?)", (user_id, key, value))


# ---------- saved chats (conversations + messages; citations are stored with each message) ----------
def new_conversation(user_id, title):
    with get_conn() as c:
        return c.execute("INSERT INTO conversations(user_id, title) VALUES(?,?)", (user_id, title)).lastrowid


def add_message(conv_id, role, content, sources_json="[]"):
    with get_conn() as c:
        c.execute("INSERT INTO messages(conversation_id, role, content, sources) VALUES(?,?,?,?)",
                  (conv_id, role, content, sources_json))


def list_conversations(user_id):
    with get_conn() as c:
        return c.execute("SELECT id, title FROM conversations WHERE user_id=? ORDER BY id DESC", (user_id,)).fetchall()


def get_messages(conv_id):
    with get_conn() as c:
        return c.execute("SELECT role, content, sources FROM messages WHERE conversation_id=? ORDER BY id", (conv_id,)).fetchall()


# ---------- encryption at rest, folders, plans, retention (override earlier definitions) ----------
PLANS = {"free": 5, "pro": 10, "business": None}      # documents per day (None = unlimited)


def _fernet():
    from cryptography.fernet import Fernet
    p = os.path.join("data", ".key")
    os.makedirs("data", exist_ok=True)
    if not os.path.exists(p):
        open(p, "wb").write(Fernet.generate_key())
    return Fernet(open(p, "rb").read())


def save_text(doc_id, text):
    os.makedirs(os.path.join("data", "uploads"), exist_ok=True)
    with open(os.path.join("data", "uploads", f"{doc_id}.txt"), "wb") as f:
        f.write(_fernet().encrypt(text.encode("utf-8")))


def get_text(doc_id):
    p = os.path.join("data", "uploads", f"{doc_id}.txt")
    if not os.path.exists(p):
        return ""
    raw = open(p, "rb").read()
    try:
        return _fernet().decrypt(raw).decode("utf-8")
    except Exception:                                   # older, unencrypted files
        return raw.decode("utf-8", "ignore")


def create_project(user_id, name, parent_id=None):
    with get_conn() as c:
        c.execute("INSERT INTO projects(user_id, name, parent_id) VALUES(?,?,?)", (user_id, name.strip(), parent_id))


def project_labels(user_id):
    """{project_id: 'Parent / Child'} for folder hierarchy."""
    with get_conn() as c:
        rows = {r["id"]: (r["name"], r["parent_id"]) for r in
                c.execute("SELECT id, name, parent_id FROM projects WHERE user_id=? ORDER BY id", (user_id,))}
    def path(i, depth=0):
        n, p = rows[i]
        return path(p, depth + 1) + " / " + n if p in rows and depth < 6 else n
    return {i: path(i) for i in rows}


def monthly_count(user_id):
    with get_conn() as c:
        return c.execute("SELECT COUNT(*) n FROM documents WHERE user_id=? AND "
                         "strftime('%Y-%m', created_at)=strftime('%Y-%m','now')", (user_id,)).fetchone()["n"]


def purge_old(user_id, days):
    with get_conn() as c:
        ids = [r["id"] for r in c.execute("SELECT id FROM documents WHERE user_id=? AND created_at < datetime('now', ?)",
                                          (user_id, f"-{int(days)} days"))]
    for i in ids:
        delete_document(i, user_id)
    return len(ids)


def daily_count(user_id):
    """Documents uploaded today (server date)."""
    with get_conn() as c:
        return c.execute("SELECT COUNT(*) n FROM documents WHERE user_id=? AND "
                         "strftime('%Y-%m-%d', created_at)=strftime('%Y-%m-%d','now')", (user_id,)).fetchone()["n"]
