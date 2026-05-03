#!/usr/bin/env python3
"""
SirenWatch PM — Einfaches Projektmanagement-Tool
TJK-Solutions | sirenwatch.de
"""
import hashlib
import json
import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path

from flask import Flask, g, jsonify, make_response, redirect, render_template_string, request

DB_PATH  = Path(__file__).parent / "pm.db"
PASSWORD = "sirenwatch"   # Kann per Umgebungsvariable PM_PASSWORD überschrieben werden
PORT     = 8083
COOKIE   = "sw_pm"

import os
PASSWORD = os.environ.get("PM_PASSWORD", PASSWORD)


# ── Datenbank ─────────────────────────────────────────────────────────────────

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH, detect_types=sqlite3.PARSE_DECLTYPES)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA journal_mode=WAL")
    return g.db


def init_db():
    with sqlite3.connect(DB_PATH) as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS projects (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT    NOT NULL,
            description TEXT    DEFAULT '',
            color       TEXT    DEFAULT '#dc2626',
            created_at  INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS tasks (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id  INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
            title       TEXT    NOT NULL,
            description TEXT    DEFAULT '',
            status      TEXT    DEFAULT 'todo',
            priority    TEXT    DEFAULT 'normal',
            assignee    TEXT    DEFAULT '',
            due_date    TEXT    DEFAULT '',
            created_at  INTEGER NOT NULL,
            updated_at  INTEGER NOT NULL
        );
        """)


# ── Auth ──────────────────────────────────────────────────────────────────────

def _token():
    return hashlib.sha256(PASSWORD.encode()).hexdigest()[:32]


def is_auth():
    return request.cookies.get(COOKIE) == _token()


def is_api_auth():
    return request.headers.get("X-API-Key") == _token()


def require_auth(fn):
    from functools import wraps
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if is_api_auth():
            return fn(*args, **kwargs)
        if not is_auth():
            if request.path.startswith("/api/"):
                return jsonify({"error": "unauthorized"}), 401
            return redirect("/login")
        return fn(*args, **kwargs)
    return wrapper


# ── HTML Templates ─────────────────────────────────────────────────────────────

_BASE_STYLE = """
<style>
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
:root{
  --bg:#06070a;--surf:#0d1117;--surf2:#161b22;--brd:#21262d;--brd2:#30363d;
  --txt:#e6edf3;--mut:#8b949e;--red:#dc2626;--red2:#f85149;
  --grn:#3fb950;--ylw:#d29922;--ora:#ff7b00;--blu:#58a6ff;--pur:#bc8cff;
  --font:'SF Mono','Fira Code','Courier New',monospace;
}
body{background:var(--bg);color:var(--txt);font-family:var(--font);font-size:13px;min-height:100vh}
a{color:var(--blu);text-decoration:none}
a:hover{text-decoration:underline}
button,input,textarea,select{font-family:var(--font);font-size:13px}
input,textarea,select{background:var(--surf);border:1px solid var(--brd2);border-radius:6px;
  padding:8px 12px;color:var(--txt);outline:none;width:100%}
input:focus,textarea:focus,select:focus{border-color:var(--blu)}
textarea{resize:vertical;min-height:80px}
button{cursor:pointer;border:none;border-radius:6px;padding:8px 16px;font-weight:600}
.btn-red{background:var(--red);color:#fff}.btn-red:hover{background:#b91c1c}
.btn-ghost{background:transparent;border:1px solid var(--brd2);color:var(--txt)}.btn-ghost:hover{border-color:var(--mut)}
.btn-sm{padding:4px 10px;font-size:11px}
label{display:block;font-size:11px;color:var(--mut);text-transform:uppercase;letter-spacing:.5px;margin-bottom:5px}
.form-group{margin-bottom:16px}

header{background:var(--surf);border-bottom:1px solid var(--brd);padding:10px 24px;
  display:flex;align-items:center;justify-content:space-between;position:sticky;top:0;z-index:100}
.logo{display:flex;align-items:center;gap:10px}
.logo-mark{width:28px;height:28px;background:var(--red);border-radius:6px;
  display:flex;align-items:center;justify-content:center;font-size:14px;font-weight:900;color:#fff}
.logo-text{font-size:14px;font-weight:700;color:var(--txt)}
.logo-sub{font-size:10px;color:var(--mut)}
.header-right{display:flex;align-items:center;gap:12px}

.container{max-width:1400px;margin:0 auto;padding:24px}
.page-title{font-size:18px;font-weight:700;margin-bottom:4px}
.page-sub{font-size:12px;color:var(--mut);margin-bottom:24px}

.card{background:var(--surf2);border:1px solid var(--brd);border-radius:10px;padding:20px}
.grid-2{display:grid;grid-template-columns:repeat(auto-fill,minmax(340px,1fr));gap:16px}
.grid-3{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:12px}

.progress-bar{background:var(--brd);border-radius:4px;height:6px;overflow:hidden;margin:8px 0}
.progress-fill{height:100%;border-radius:4px;background:var(--grn);transition:width .3s}

.badge{display:inline-flex;align-items:center;padding:2px 8px;border-radius:20px;font-size:10px;font-weight:600;text-transform:uppercase;letter-spacing:.3px}
.badge-todo{background:#21262d;color:var(--mut)}
.badge-in_progress{background:#1f3a5f;color:var(--blu)}
.badge-done{background:#0f2d1a;color:var(--grn)}
.badge-blocked{background:#3a1a1a;color:var(--red2)}
.badge-low{background:#1a2a1a;color:#6e8f6e}
.badge-normal{background:#1a1a2a;color:#6e6e8f}
.badge-high{background:#2a2a1a;color:var(--ylw)}
.badge-critical{background:#2a1a1a;color:var(--red2)}

.modal-overlay{display:none;position:fixed;inset:0;background:#00000088;z-index:200;
  align-items:center;justify-content:center}
.modal-overlay.open{display:flex}
.modal{background:var(--surf2);border:1px solid var(--brd2);border-radius:12px;padding:28px;
  width:100%;max-width:520px;max-height:90vh;overflow-y:auto}
.modal-title{font-size:15px;font-weight:700;margin-bottom:20px}

.kanban{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;align-items:start}
@media(max-width:900px){.kanban{grid-template-columns:repeat(2,1fr)}}
@media(max-width:500px){.kanban{grid-template-columns:1fr}}
.col-header{font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.5px;
  padding:8px 12px;border-radius:6px 6px 0 0;margin-bottom:1px}
.col-todo .col-header{background:#21262d;color:var(--mut)}
.col-in_progress .col-header{background:#1f3a5f;color:var(--blu)}
.col-done .col-header{background:#0f2d1a;color:var(--grn)}
.col-blocked .col-header{background:#3a1a1a;color:var(--red2)}
.col-body{background:var(--surf);border:1px solid var(--brd);border-radius:0 0 8px 8px;
  padding:8px;display:flex;flex-direction:column;gap:8px;min-height:120px}
.task-card{background:var(--surf2);border:1px solid var(--brd2);border-radius:8px;padding:12px;cursor:pointer}
.task-card:hover{border-color:var(--blu)}
.task-title{font-weight:600;margin-bottom:6px;line-height:1.4}
.task-meta{display:flex;gap:6px;flex-wrap:wrap;align-items:center}
.task-assignee{font-size:10px;color:var(--mut)}
.task-due{font-size:10px;color:var(--mut)}
.task-due.overdue{color:var(--red2)}

.stat{text-align:center}
.stat-val{font-size:22px;font-weight:700;color:var(--blu)}
.stat-lbl{font-size:10px;color:var(--mut);text-transform:uppercase}

footer{text-align:center;padding:24px;font-size:11px;color:var(--brd2)}
</style>
"""

_HEADER = """
<header>
  <div class="logo">
    <div class="logo-mark">S</div>
    <div>
      <div class="logo-text">SirenWatch PM</div>
      <div class="logo-sub">Powered by TJK-Solutions</div>
    </div>
  </div>
  <div class="header-right">
    <span style="color:var(--mut);font-size:11px">{{ user }}</span>
    <a href="/logout"><button class="btn-ghost btn-sm">Abmelden</button></a>
  </div>
</header>
"""

_LOGIN = """<!DOCTYPE html>
<html lang="de"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>SirenWatch PM — Login</title>""" + _BASE_STYLE + """
</head><body>
<div style="display:flex;align-items:center;justify-content:center;min-height:100vh">
<div class="card" style="width:100%;max-width:360px">
  <div style="display:flex;align-items:center;gap:10px;margin-bottom:24px">
    <div class="logo-mark">S</div>
    <div><div class="logo-text">SirenWatch PM</div>
    <div class="logo-sub">Powered by TJK-Solutions</div></div>
  </div>
  <form method="POST" action="/login">
    <div class="form-group">
      <label>Passwort</label>
      <input type="password" name="password" autofocus autocomplete="current-password">
    </div>
    {% if error %}<div style="color:var(--red2);font-size:12px;margin-bottom:12px">Falsches Passwort</div>{% endif %}
    <button type="submit" class="btn-red" style="width:100%">Anmelden →</button>
  </form>
</div>
</div>
</body></html>"""

_PROJECTS = """<!DOCTYPE html>
<html lang="de"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>SirenWatch PM — Projekte</title>""" + _BASE_STYLE + """
</head><body>
""" + _HEADER + """
<div class="container">
  <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:24px">
    <div>
      <div class="page-title">Projekte</div>
      <div class="page-sub">{{ projects|length }} Projekt(e) aktiv</div>
    </div>
    <button class="btn-red" onclick="openNew()">+ Neues Projekt</button>
  </div>

  <!-- Stats -->
  <div class="card" style="margin-bottom:24px">
    <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));gap:16px">
      <div class="stat"><div class="stat-val">{{ total_tasks }}</div><div class="stat-lbl">Aufgaben gesamt</div></div>
      <div class="stat"><div class="stat-val" style="color:var(--grn)">{{ done_tasks }}</div><div class="stat-lbl">Erledigt</div></div>
      <div class="stat"><div class="stat-val" style="color:var(--blu)">{{ inprogress_tasks }}</div><div class="stat-lbl">In Bearbeitung</div></div>
      <div class="stat"><div class="stat-val" style="color:var(--red2)">{{ blocked_tasks }}</div><div class="stat-lbl">Blockiert</div></div>
      <div class="stat"><div class="stat-val">{{ total_pct }}%</div><div class="stat-lbl">Gesamtfortschritt</div></div>
    </div>
  </div>

  <div class="grid-2">
  {% for p in projects %}
    <div class="card" style="border-left:4px solid {{ p.color }};cursor:pointer" onclick="location.href='/project/{{ p.id }}'">
      <div style="display:flex;align-items:flex-start;justify-content:space-between;margin-bottom:12px">
        <div>
          <div style="font-size:15px;font-weight:700">{{ p.name }}</div>
          {% if p.description %}<div style="font-size:12px;color:var(--mut);margin-top:3px">{{ p.description }}</div>{% endif %}
        </div>
        <div style="display:flex;gap:6px" onclick="event.stopPropagation()">
          <button class="btn-ghost btn-sm" onclick="editProject({{ p.id }},'{{ p.name|e }}','{{ p.description|e }}','{{ p.color }}')">✎</button>
          <button class="btn-ghost btn-sm" style="color:var(--red2)" onclick="delProject({{ p.id }})">✕</button>
        </div>
      </div>
      <div style="display:flex;gap:16px;margin-bottom:10px">
        <span style="font-size:11px;color:var(--mut)">{{ p.total }} Aufgaben</span>
        <span style="font-size:11px;color:var(--grn)">{{ p.done }} erledigt</span>
        {% if p.blocked %}<span style="font-size:11px;color:var(--red2)">{{ p.blocked }} blockiert</span>{% endif %}
      </div>
      <div class="progress-bar">
        <div class="progress-fill" style="width:{{ p.pct }}%;background:{{ p.color }}"></div>
      </div>
      <div style="font-size:11px;color:var(--mut);text-align:right">{{ p.pct }}% abgeschlossen</div>
    </div>
  {% else %}
    <div style="color:var(--mut);grid-column:1/-1;text-align:center;padding:40px">
      Noch keine Projekte. Lege das erste an.
    </div>
  {% endfor %}
  </div>
</div>

<footer>SirenWatch PM · Powered by TJK-Solutions · sirenwatch.de</footer>

<!-- Modal: Projekt anlegen/bearbeiten -->
<div class="modal-overlay" id="modal-project">
  <div class="modal">
    <div class="modal-title" id="modal-project-title">Neues Projekt</div>
    <form id="form-project" onsubmit="saveProject(event)">
      <input type="hidden" id="proj-id" value="">
      <div class="form-group"><label>Name</label><input id="proj-name" required></div>
      <div class="form-group"><label>Beschreibung</label><textarea id="proj-desc"></textarea></div>
      <div class="form-group"><label>Farbe</label>
        <div style="display:flex;gap:8px;flex-wrap:wrap" id="color-picker">
          {% for c in ['#dc2626','#2563eb','#16a34a','#9333ea','#d97706','#0891b2','#db2777','#65a30d'] %}
          <div onclick="pickColor('{{ c }}')" style="width:28px;height:28px;border-radius:6px;background:{{ c }};cursor:pointer;border:2px solid transparent" data-color="{{ c }}"></div>
          {% endfor %}
        </div>
      </div>
      <div style="display:flex;gap:8px;justify-content:flex-end">
        <button type="button" class="btn-ghost" onclick="closeModal('modal-project')">Abbrechen</button>
        <button type="submit" class="btn-red">Speichern</button>
      </div>
    </form>
  </div>
</div>

<script>
let _selColor = '#dc2626';
function pickColor(c){
  _selColor=c;
  document.querySelectorAll('#color-picker [data-color]').forEach(el=>{
    el.style.borderColor = el.dataset.color===c ? '#fff' : 'transparent';
  });
}
function openNew(){
  document.getElementById('proj-id').value='';
  document.getElementById('proj-name').value='';
  document.getElementById('proj-desc').value='';
  document.getElementById('modal-project-title').textContent='Neues Projekt';
  pickColor('#dc2626');
  document.getElementById('modal-project').classList.add('open');
  setTimeout(()=>document.getElementById('proj-name').focus(),50);
}
function editProject(id,name,desc,color){
  document.getElementById('proj-id').value=id;
  document.getElementById('proj-name').value=name;
  document.getElementById('proj-desc').value=desc;
  document.getElementById('modal-project-title').textContent='Projekt bearbeiten';
  pickColor(color);
  document.getElementById('modal-project').classList.add('open');
}
function closeModal(id){ document.getElementById(id).classList.remove('open'); }
async function saveProject(e){
  e.preventDefault();
  const id=document.getElementById('proj-id').value;
  const body={name:document.getElementById('proj-name').value,
               description:document.getElementById('proj-desc').value,color:_selColor};
  const url=id ? `/api/projects/${id}` : '/api/projects';
  const method=id ? 'PUT' : 'POST';
  await fetch(url,{method,headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
  location.reload();
}
async function delProject(id){
  if(!confirm('Projekt und alle Aufgaben wirklich löschen?')) return;
  await fetch(`/api/projects/${id}`,{method:'DELETE'});
  location.reload();
}
document.addEventListener('keydown',e=>{ if(e.key==='Escape') document.querySelectorAll('.modal-overlay.open').forEach(m=>m.classList.remove('open')); });
</script>
</body></html>"""

_PROJECT = """<!DOCTYPE html>
<html lang="de"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{{ project.name }} — SirenWatch PM</title>""" + _BASE_STYLE + """
</head><body>
""" + _HEADER + """
<div class="container">
  <div style="display:flex;align-items:center;gap:12px;margin-bottom:6px">
    <a href="/" style="color:var(--mut);font-size:12px">← Alle Projekte</a>
  </div>
  <div style="display:flex;align-items:flex-start;justify-content:space-between;margin-bottom:8px;flex-wrap:wrap;gap:8px">
    <div>
      <div class="page-title" style="border-left:4px solid {{ project.color }};padding-left:10px">{{ project.name }}</div>
      {% if project.description %}<div class="page-sub">{{ project.description }}</div>{% endif %}
    </div>
    <button class="btn-red" onclick="openTask()">+ Neue Aufgabe</button>
  </div>

  <!-- Progress -->
  <div class="card" style="margin-bottom:20px">
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px">
      <span style="font-size:12px;color:var(--mut)">{{ done_count }} / {{ total_count }} Aufgaben erledigt</span>
      <span style="font-size:13px;font-weight:700;color:{{ project.color }}">{{ pct }}%</span>
    </div>
    <div class="progress-bar" style="height:8px">
      <div class="progress-fill" style="width:{{ pct }}%;background:{{ project.color }}"></div>
    </div>
  </div>

  <!-- Kanban -->
  <div class="kanban">
    {% for col_id, col_label in [('todo','📋 Todo'),('in_progress','⚡ In Bearbeitung'),('done','✅ Erledigt'),('blocked','🔒 Blockiert')] %}
    <div class="col-{{ col_id }}">
      <div class="col-header">{{ col_label }} <span style="opacity:.6">({{ tasks_by_status[col_id]|length }})</span></div>
      <div class="col-body" id="col-{{ col_id }}">
        {% for t in tasks_by_status[col_id] %}
        <div class="task-card" onclick="openTask({{ t.id }})">
          <div class="task-title">{{ t.title }}</div>
          {% if t.description %}<div style="font-size:11px;color:var(--mut);margin-bottom:6px;line-height:1.4">{{ t.description[:80] }}{% if t.description|length > 80 %}…{% endif %}</div>{% endif %}
          <div class="task-meta">
            <span class="badge badge-{{ t.priority }}">{{ t.priority }}</span>
            {% if t.assignee %}<span class="task-assignee">👤 {{ t.assignee }}</span>{% endif %}
            {% if t.due_date %}<span class="task-due {% if t.due_date < today and col_id != 'done' %}overdue{% endif %}">📅 {{ t.due_date }}</span>{% endif %}
          </div>
        </div>
        {% endfor %}
      </div>
    </div>
    {% endfor %}
  </div>
</div>

<footer>SirenWatch PM · Powered by TJK-Solutions · sirenwatch.de</footer>

<!-- Modal: Aufgabe -->
<div class="modal-overlay" id="modal-task">
  <div class="modal">
    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:20px">
      <div class="modal-title" style="margin:0" id="modal-task-title">Neue Aufgabe</div>
      <button id="btn-delete-task" class="btn-ghost btn-sm" style="color:var(--red2);display:none" onclick="deleteTask()">Löschen</button>
    </div>
    <form id="form-task" onsubmit="saveTask(event)">
      <input type="hidden" id="task-id" value="">
      <div class="form-group"><label>Titel</label><input id="task-title" required></div>
      <div class="form-group"><label>Beschreibung</label><textarea id="task-desc"></textarea></div>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px">
        <div class="form-group">
          <label>Status</label>
          <select id="task-status">
            <option value="todo">📋 Todo</option>
            <option value="in_progress">⚡ In Bearbeitung</option>
            <option value="done">✅ Erledigt</option>
            <option value="blocked">🔒 Blockiert</option>
          </select>
        </div>
        <div class="form-group">
          <label>Priorität</label>
          <select id="task-priority">
            <option value="low">Niedrig</option>
            <option value="normal" selected>Normal</option>
            <option value="high">Hoch</option>
            <option value="critical">Kritisch</option>
          </select>
        </div>
      </div>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px">
        <div class="form-group"><label>Zugewiesen an</label><input id="task-assignee" placeholder="Name…"></div>
        <div class="form-group"><label>Fällig am</label><input type="date" id="task-due"></div>
      </div>
      <div style="display:flex;gap:8px;justify-content:flex-end">
        <button type="button" class="btn-ghost" onclick="closeModal('modal-task')">Abbrechen</button>
        <button type="submit" class="btn-red">Speichern</button>
      </div>
    </form>
  </div>
</div>

<script>
const PROJECT_ID = {{ project.id }};
function openTask(id){
  document.getElementById('task-id').value = id||'';
  document.getElementById('modal-task-title').textContent = id ? 'Aufgabe bearbeiten' : 'Neue Aufgabe';
  document.getElementById('btn-delete-task').style.display = id ? 'inline-flex' : 'none';
  if(id){
    const t = {{ tasks_list|tojson }}.find(x=>x.id===id);
    if(t){
      document.getElementById('task-title').value    = t.title;
      document.getElementById('task-desc').value     = t.description||'';
      document.getElementById('task-status').value   = t.status;
      document.getElementById('task-priority').value = t.priority;
      document.getElementById('task-assignee').value = t.assignee||'';
      document.getElementById('task-due').value      = t.due_date||'';
    }
  } else {
    document.getElementById('form-task').reset();
    document.getElementById('task-status').value='todo';
    document.getElementById('task-priority').value='normal';
  }
  document.getElementById('modal-task').classList.add('open');
  setTimeout(()=>document.getElementById('task-title').focus(),50);
}
async function saveTask(e){
  e.preventDefault();
  const id=document.getElementById('task-id').value;
  const body={
    project_id: PROJECT_ID,
    title:      document.getElementById('task-title').value,
    description:document.getElementById('task-desc').value,
    status:     document.getElementById('task-status').value,
    priority:   document.getElementById('task-priority').value,
    assignee:   document.getElementById('task-assignee').value,
    due_date:   document.getElementById('task-due').value,
  };
  const url=id?`/api/tasks/${id}`:'/api/tasks';
  const method=id?'PUT':'POST';
  await fetch(url,{method,headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
  location.reload();
}
async function deleteTask(){
  const id=document.getElementById('task-id').value;
  if(!id||!confirm('Aufgabe wirklich löschen?')) return;
  await fetch(`/api/tasks/${id}`,{method:'DELETE'});
  location.reload();
}
function closeModal(id){ document.getElementById(id).classList.remove('open'); }
document.addEventListener('keydown',e=>{ if(e.key==='Escape') document.querySelectorAll('.modal-overlay.open').forEach(m=>m.classList.remove('open')); });
</script>
</body></html>"""


# ── Flask App ─────────────────────────────────────────────────────────────────

app = Flask(__name__)
app.secret_key = "sw-pm-secret-2026"


@app.teardown_appcontext
def close_db(e=None):
    db = g.pop("db", None)
    if db:
        db.close()


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        pw = request.form.get("password", "")
        if pw == PASSWORD:
            resp = make_response(redirect("/"))
            resp.set_cookie(COOKIE, _token(), max_age=3600 * 24 * 7, httponly=True, samesite="Lax")
            return resp
        return render_template_string(_LOGIN, error=True)
    return render_template_string(_LOGIN, error=False)


@app.route("/logout")
def logout():
    resp = make_response(redirect("/login"))
    resp.delete_cookie(COOKIE)
    return resp


@app.route("/")
@require_auth
def projects():
    db = get_db()
    projs = db.execute("SELECT * FROM projects ORDER BY created_at DESC").fetchall()
    result = []
    total_tasks = done_tasks = inprogress_tasks = blocked_tasks = 0
    for p in projs:
        rows = db.execute(
            "SELECT status, COUNT(*) as n FROM tasks WHERE project_id=? GROUP BY status", (p["id"],)
        ).fetchall()
        counts = {r["status"]: r["n"] for r in rows}
        total  = sum(counts.values())
        done   = counts.get("done", 0)
        pct    = round(done / total * 100) if total else 0
        total_tasks     += total
        done_tasks      += done
        inprogress_tasks += counts.get("in_progress", 0)
        blocked_tasks   += counts.get("blocked", 0)
        result.append({**dict(p), "total": total, "done": done,
                       "blocked": counts.get("blocked", 0), "pct": pct})
    total_pct = round(done_tasks / total_tasks * 100) if total_tasks else 0
    return render_template_string(_PROJECTS, projects=result, user="Admin",
                                  total_tasks=total_tasks, done_tasks=done_tasks,
                                  inprogress_tasks=inprogress_tasks, blocked_tasks=blocked_tasks,
                                  total_pct=total_pct)


@app.route("/project/<int:pid>")
@require_auth
def project_detail(pid):
    db = get_db()
    p  = db.execute("SELECT * FROM projects WHERE id=?", (pid,)).fetchone()
    if not p:
        return redirect("/")
    tasks = db.execute("SELECT * FROM tasks WHERE project_id=? ORDER BY priority DESC, created_at",
                       (pid,)).fetchall()
    tasks_list = [dict(t) for t in tasks]
    by_status  = {"todo": [], "in_progress": [], "done": [], "blocked": []}
    for t in tasks_list:
        by_status.setdefault(t["status"], []).append(t)
    total = len(tasks_list)
    done  = len(by_status["done"])
    pct   = round(done / total * 100) if total else 0
    import datetime
    today = datetime.date.today().isoformat()
    return render_template_string(_PROJECT, project=dict(p), tasks_by_status=by_status,
                                  tasks_list=tasks_list,
                                  total_count=total, done_count=done, pct=pct, today=today,
                                  user="Admin")


# ── REST API ──────────────────────────────────────────────────────────────────

@app.route("/api/projects", methods=["POST"])
@require_auth
def create_project():
    d  = request.json
    db = get_db()
    db.execute("INSERT INTO projects (name,description,color,created_at) VALUES (?,?,?,?)",
               (d["name"], d.get("description",""), d.get("color","#dc2626"), int(time.time()*1000)))
    db.commit()
    return jsonify({"ok": True})


@app.route("/api/projects/<int:pid>", methods=["PUT"])
@require_auth
def update_project(pid):
    d  = request.json
    db = get_db()
    db.execute("UPDATE projects SET name=?,description=?,color=? WHERE id=?",
               (d["name"], d.get("description",""), d.get("color","#dc2626"), pid))
    db.commit()
    return jsonify({"ok": True})


@app.route("/api/projects/<int:pid>", methods=["DELETE"])
@require_auth
def delete_project(pid):
    db = get_db()
    db.execute("DELETE FROM tasks WHERE project_id=?", (pid,))
    db.execute("DELETE FROM projects WHERE id=?", (pid,))
    db.commit()
    return jsonify({"ok": True})


@app.route("/api/tasks", methods=["POST"])
@require_auth
def create_task():
    d   = request.json
    db  = get_db()
    now = int(time.time() * 1000)
    db.execute("""INSERT INTO tasks (project_id,title,description,status,priority,assignee,due_date,created_at,updated_at)
                  VALUES (?,?,?,?,?,?,?,?,?)""",
               (d["project_id"], d["title"], d.get("description",""),
                d.get("status","todo"), d.get("priority","normal"),
                d.get("assignee",""), d.get("due_date",""), now, now))
    db.commit()
    return jsonify({"ok": True})


@app.route("/api/tasks/<int:tid>", methods=["PUT"])
@require_auth
def update_task(tid):
    d  = request.json
    db = get_db()
    db.execute("""UPDATE tasks SET title=?,description=?,status=?,priority=?,assignee=?,due_date=?,updated_at=?
                  WHERE id=?""",
               (d["title"], d.get("description",""), d.get("status","todo"),
                d.get("priority","normal"), d.get("assignee",""), d.get("due_date",""),
                int(time.time()*1000), tid))
    db.commit()
    return jsonify({"ok": True})


@app.route("/api/tasks/<int:tid>", methods=["DELETE"])
@require_auth
def delete_task(tid):
    db = get_db()
    db.execute("DELETE FROM tasks WHERE id=?", (tid,))
    db.commit()
    return jsonify({"ok": True})


@app.route("/api/tasks/<int:tid>", methods=["PATCH"])
@require_auth
def patch_task(tid):
    d  = request.json
    db = get_db()
    allowed = {"status", "priority", "assignee", "due_date", "title", "description"}
    fields  = {k: v for k, v in d.items() if k in allowed}
    if not fields:
        return jsonify({"error": "no valid fields"}), 400
    fields["updated_at"] = int(time.time() * 1000)
    sql = "UPDATE tasks SET " + ", ".join(f"{k}=?" for k in fields) + " WHERE id=?"
    db.execute(sql, list(fields.values()) + [tid])
    db.commit()
    task = db.execute("SELECT * FROM tasks WHERE id=?", (tid,)).fetchone()
    return jsonify(dict(task) if task else {"error": "not found"})


@app.route("/api/projects", methods=["GET"])
@require_auth
def list_projects():
    db    = get_db()
    projs = db.execute("SELECT * FROM projects ORDER BY created_at DESC").fetchall()
    result = []
    for p in projs:
        rows   = db.execute(
            "SELECT status, COUNT(*) as n FROM tasks WHERE project_id=? GROUP BY status", (p["id"],)
        ).fetchall()
        counts = {r["status"]: r["n"] for r in rows}
        total  = sum(counts.values())
        done   = counts.get("done", 0)
        result.append({**dict(p), "total_tasks": total, "done_tasks": done,
                       "in_progress_tasks": counts.get("in_progress", 0),
                       "blocked_tasks": counts.get("blocked", 0),
                       "todo_tasks": counts.get("todo", 0),
                       "pct": round(done / total * 100) if total else 0})
    return jsonify(result)


@app.route("/api/tasks", methods=["GET"])
@require_auth
def list_tasks():
    db      = get_db()
    filters = []
    params  = []
    if pid := request.args.get("project_id"):
        filters.append("project_id=?")
        params.append(int(pid))
    if status := request.args.get("status"):
        filters.append("status=?")
        params.append(status)
    if priority := request.args.get("priority"):
        filters.append("priority=?")
        params.append(priority)
    where = ("WHERE " + " AND ".join(filters)) if filters else ""
    tasks = db.execute(
        f"SELECT * FROM tasks {where} ORDER BY priority DESC, created_at", params
    ).fetchall()
    return jsonify([dict(t) for t in tasks])


@app.route("/api/token", methods=["GET"])
@require_auth
def get_token():
    return jsonify({"token": _token()})


if __name__ == "__main__":
    init_db()
    print(f"SirenWatch PM läuft auf http://0.0.0.0:{PORT}")
    print(f"Passwort: {PASSWORD} (überschreibbar mit env PM_PASSWORD=...)")
    app.run(host="0.0.0.0", port=PORT, debug=False)
