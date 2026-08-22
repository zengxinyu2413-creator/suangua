"""
core/user_db.py
===============
User account system with per-user data folders.

Structure:
  userdata/
  ├── users.db
  ├── alice/
  │   ├── profile.json
  │   └── charts/
  │       ├── 1.json
  │       └── 2.json
  └── bob/
      └── ...

Password: min 6 chars, must have uppercase + lowercase + digit.
"""
import sqlite3, hashlib, secrets, json, os, re
from datetime import datetime
from typing import Optional, Dict, Any, List

_ROOT = os.path.dirname(os.path.dirname(__file__))
USERDATA_DIR = os.path.join(_ROOT, "userdata")
DB_PATH = os.path.join(USERDATA_DIR, "users.db")

def _ensure_db():
    os.makedirs(USERDATA_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        display_name TEXT DEFAULT '',
        folder_name TEXT UNIQUE NOT NULL,
        token TEXT UNIQUE,
        created_at TEXT DEFAULT (datetime('now'))
    )""")
    conn.execute("""CREATE TABLE IF NOT EXISTS saved_charts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        module TEXT NOT NULL DEFAULT 'bazi',
        title TEXT DEFAULT '',
        summary TEXT DEFAULT '',
        birth_info TEXT DEFAULT '{}',
        chart_data TEXT DEFAULT '{}',
        notes TEXT DEFAULT '',
        tags TEXT DEFAULT '',
        created_at TEXT DEFAULT (datetime('now')),
        updated_at TEXT DEFAULT (datetime('now')),
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    )""")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_charts_user ON saved_charts(user_id)")
    conn.commit()
    return conn

# ── Password ──

def validate_password(password: str) -> Optional[str]:
    if len(password) < 6:
        return "密码长度至少6位"
    if not re.search(r'[A-Z]', password):
        return "密码必须包含至少一个大写字母(A-Z)"
    if not re.search(r'[a-z]', password):
        return "密码必须包含至少一个小写字母(a-z)"
    if not re.search(r'[0-9]', password):
        return "密码必须包含至少一个数字(0-9)"
    return None

def _hash_pw(pw, salt=""):
    if not salt: salt = secrets.token_hex(16)
    return f"{salt}:{hashlib.sha256((salt+pw).encode()).hexdigest()}"

def _verify_pw(pw, stored):
    salt, exp = stored.split(":", 1)
    return hashlib.sha256((salt+pw).encode()).hexdigest() == exp

def _safe_folder(username):
    s = re.sub(r'[^\w\-]', '_', username.strip().lower())
    return s or f"user_{secrets.token_hex(4)}"

def _ensure_user_dir(folder):
    d = os.path.join(USERDATA_DIR, folder)
    os.makedirs(os.path.join(d, "charts"), exist_ok=True)
    pf = os.path.join(d, "profile.json")
    if not os.path.exists(pf):
        with open(pf, "w", encoding="utf-8") as f:
            json.dump({"created": datetime.now().isoformat(), "settings": {}}, f, ensure_ascii=False, indent=2)
    return d

# ── Auth ──

def register(username: str, password: str, display_name: str = "") -> Dict[str, Any]:
    pw_err = validate_password(password)
    if pw_err:
        return {"success": False, "error": pw_err}
    uname = username.strip().lower()
    if len(uname) < 2:
        return {"success": False, "error": "用户名至少2个字符"}
    if len(uname) > 30:
        return {"success": False, "error": "用户名不超过30个字符"}

    conn = _ensure_db()
    try:
        folder = _safe_folder(uname)
        if conn.execute("SELECT 1 FROM users WHERE folder_name=?", (folder,)).fetchone():
            folder = f"{folder}_{secrets.token_hex(3)}"
        token = secrets.token_urlsafe(32)
        conn.execute("INSERT INTO users (username,password_hash,display_name,folder_name,token) VALUES (?,?,?,?,?)",
                     (uname, _hash_pw(password), display_name or username, folder, token))
        conn.commit()
        _ensure_user_dir(folder)
        user = conn.execute("SELECT id,username,display_name,folder_name,token,created_at FROM users WHERE username=?",(uname,)).fetchone()
        return {"success": True, "user": dict(user)}
    except sqlite3.IntegrityError:
        return {"success": False, "error": "用户名已存在"}
    finally:
        conn.close()

def login(username: str, password: str) -> Dict[str, Any]:
    conn = _ensure_db()
    try:
        user = conn.execute("SELECT * FROM users WHERE username=?",(username.strip().lower(),)).fetchone()
        if not user: return {"success": False, "error": "用户名不存在"}
        if not _verify_pw(password, user["password_hash"]): return {"success": False, "error": "密码错误"}
        token = secrets.token_urlsafe(32)
        conn.execute("UPDATE users SET token=? WHERE id=?", (token, user["id"]))
        conn.commit()
        return {"success": True, "user": {
            "id":user["id"],"username":user["username"],"display_name":user["display_name"],
            "folder_name":user["folder_name"],"token":token,"created_at":user["created_at"],
        }}
    finally:
        conn.close()

def get_user_by_token(token: str) -> Optional[Dict[str, Any]]:
    if not token: return None
    conn = _ensure_db()
    try:
        u = conn.execute("SELECT id,username,display_name,folder_name,created_at FROM users WHERE token=?",(token,)).fetchone()
        return dict(u) if u else None
    finally:
        conn.close()

def _charts_dir(user_id: int) -> Optional[str]:
    conn = _ensure_db()
    try:
        u = conn.execute("SELECT folder_name FROM users WHERE id=?",(user_id,)).fetchone()
        if not u: return None
        d = os.path.join(USERDATA_DIR, u["folder_name"], "charts")
        os.makedirs(d, exist_ok=True)
        return d
    finally:
        conn.close()

# ── Charts CRUD ──

def save_chart(user_id, module, title, summary, birth_info, chart_data, notes="", tags=""):
    conn = _ensure_db()
    try:
        conn.execute("INSERT INTO saved_charts (user_id,module,title,summary,birth_info,chart_data,notes,tags) VALUES (?,?,?,?,?,?,?,?)",
            (user_id,module,title,summary,json.dumps(birth_info,ensure_ascii=False),json.dumps(chart_data,ensure_ascii=False),notes,tags))
        conn.commit()
        cid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        # Save JSON to user folder
        cd = _charts_dir(user_id)
        if cd:
            with open(os.path.join(cd, f"{cid}.json"), "w", encoding="utf-8") as f:
                json.dump({"id":cid,"module":module,"title":title,"summary":summary,
                    "birth_info":birth_info,"chart_data":chart_data,"notes":notes,"tags":tags,
                    "created_at":datetime.now().isoformat()}, f, ensure_ascii=False, indent=2)
        return {"success": True, "id": cid}
    finally:
        conn.close()

def list_charts(user_id, module=None, limit=50):
    conn = _ensure_db()
    try:
        sql = "SELECT id,module,title,summary,notes,tags,created_at FROM saved_charts WHERE user_id=?"
        args = [user_id]
        if module: sql += " AND module=?"; args.append(module)
        sql += " ORDER BY created_at DESC LIMIT ?"; args.append(limit)
        return [dict(r) for r in conn.execute(sql, args).fetchall()]
    finally:
        conn.close()

def get_chart(user_id, chart_id):
    conn = _ensure_db()
    try:
        r = conn.execute("SELECT * FROM saved_charts WHERE id=? AND user_id=?",(chart_id,user_id)).fetchone()
        if r:
            d = dict(r)
            d["birth_info"] = json.loads(d.get("birth_info","{}"))
            d["chart_data"] = json.loads(d.get("chart_data","{}"))
            return d
        return None
    finally:
        conn.close()

def update_notes(user_id, chart_id, notes):
    conn = _ensure_db()
    try:
        conn.execute("UPDATE saved_charts SET notes=?,updated_at=datetime('now') WHERE id=? AND user_id=?",(notes,chart_id,user_id))
        conn.commit()
        ok = conn.total_changes > 0
        if ok:
            cd = _charts_dir(user_id)
            if cd:
                fp = os.path.join(cd, f"{chart_id}.json")
                if os.path.exists(fp):
                    with open(fp,"r+",encoding="utf-8") as f:
                        d=json.load(f);d["notes"]=notes;d["updated_at"]=datetime.now().isoformat()
                        f.seek(0);f.truncate();json.dump(d,f,ensure_ascii=False,indent=2)
        return ok
    finally:
        conn.close()

def delete_chart(user_id, chart_id):
    conn = _ensure_db()
    try:
        conn.execute("DELETE FROM saved_charts WHERE id=? AND user_id=?",(chart_id,user_id))
        conn.commit()
        ok = conn.total_changes > 0
        if ok:
            cd = _charts_dir(user_id)
            if cd:
                fp = os.path.join(cd, f"{chart_id}.json")
                if os.path.exists(fp): os.remove(fp)
        return ok
    finally:
        conn.close()


# ── Birth info (个人生辰) ──

def save_birth_info(user_id: int, birth_info: dict) -> bool:
    """Save user's birth info to profile.json and DB."""
    db = _ensure_db()
    cur = db.cursor()
    # Update or create profile
    cur.execute("SELECT id FROM users WHERE id=?", (user_id,))
    if not cur.fetchone():
        return False
    # Save to profile.json
    folder = _charts_dir(user_id)
    if folder:
        parent = os.path.dirname(folder)  # userdata/username/
        profile_path = os.path.join(parent, "profile.json")
        profile = {}
        if os.path.exists(profile_path):
            try:
                with open(profile_path, "r") as f:
                    profile = json.load(f)
            except: pass
        profile["birth_info"] = birth_info
        with open(profile_path, "w") as f:
            json.dump(profile, f, ensure_ascii=False, indent=2)
    return True


def get_birth_info(user_id: int) -> dict:
    """Load user's birth info from profile.json."""
    folder = _charts_dir(user_id)
    if folder:
        parent = os.path.dirname(folder)
        profile_path = os.path.join(parent, "profile.json")
        if os.path.exists(profile_path):
            try:
                with open(profile_path, "r") as f:
                    profile = json.load(f)
                return profile.get("birth_info", {})
            except: pass
    return {}
