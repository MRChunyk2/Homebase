#!/usr/bin/env python3
"""Build firebase-app/public/index.html from the original single-file app.

Extracts every piece of embedded data (staff PII, credentialing logins,
recruiting pipeline, compensation, clinical hours) into seed/seed-data.json
(git-ignored, local only) and rewrites the HTML to load everything from
Firestore behind Google sign-in.
"""
import json, re, sys, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]      # "homebase july1426"
APP = ROOT / 'firebase-app'
SRC = ROOT / 'homebase ready for fire.html'
OUT = APP / 'public' / 'index.html'
SEED = APP / 'seed' / 'seed-data.json'

html = SRC.read_text(encoding='utf-8')
orig_len = len(html)

def extract_json(name, decl):
    """Pull `<decl> <name> = <json>;` (single line) out; return parsed JSON + span."""
    pat = re.compile(re.escape(decl) + r' ' + re.escape(name) + r'\s*=\s*(.+?);\n')
    m = pat.search(html)
    if not m:
        sys.exit(f'ANCHOR MISSING: {decl} {name}')
    return json.loads(m.group(1)), m

def replace_span(m, replacement):
    global html
    html = html[:m.start()] + replacement + html[m.end():]

# ── 1. extract the five embedded datasets ──
staff, m_staff = extract_json('STAFF_ORIG', 'const')
replace_span(m_staff, 'const STAFF_ORIG = []; // staff data lives in Firestore — nothing sensitive ships in this file\n')

recruit, m_rec = extract_json('RECRUIT_ORIG', 'const')
replace_span(m_rec, 'const RECRUIT_ORIG = []; // recruiting data lives in Firestore (kv/app_recruit, admins only)\n')

comp, m_comp = extract_json('COMP_DATA', 'const')
replace_span(m_comp, 'var COMP_DATA = {}; // loaded from Firestore kv/app_comp_data (admins only) during boot\n')

hours, m_hours = extract_json('CLINICAL_HOURS_DATA', 'var')
hours_empty = {k: (dict() if k == 'byId' else v) for k, v in hours.items()}
replace_span(m_hours, 'var CLINICAL_HOURS_DATA = ' + json.dumps(hours_empty) + '; // hours live in Firestore kv/app_clinical_hours\n')

ghours, m_gh = extract_json('GROUP_HOURS_DATA', 'var')
ghours_empty = {k: (dict() if k == 'byId' else v) for k, v in ghours.items()}
replace_span(m_gh, 'var GROUP_HOURS_DATA = ' + json.dumps(ghours_empty) + '; // group hours live in Firestore kv/app_group_hours\n')

# ── 2. remove the localStorage shim (Firestore engine replaces it) ──
start = html.index('// ── STORAGE SHIM ──')
end = html.index('// ── FALLBACK DEFINITIONS ──')
html = html[:start] + (
    '// ── STORAGE ──\n'
    '// window.storage is provided by the Firebase module at the bottom of this\n'
    '// file: same async get/set/delete/list contract, backed by Firestore, so\n'
    '// data is shared and syncs across the whole team. Nothing is stored in\n'
    '// localStorage anymore.\n\n'
) + html[end:]

# ── 3. remove the TEST CANDIDATE block ──
start = html.index('// ── TEST CANDIDATE (delete when no longer needed) ──')
end = html.index('// ── CONSTANTS ──')
html = html[:start] + html[end:]

# ── 4. ADMIN_SESSION is decided by sign-in now ──
html = html.replace(
    'const ADMIN_SESSION = true;',
    'var ADMIN_SESSION = false; // set by the auth module: true only for admin/superadmin sign-ins',
    1)

# ── 5. boot(): IIFE → named function the auth module calls after sign-in ──
old = '(async function boot() {'
if old not in html: sys.exit('ANCHOR MISSING: boot IIFE start')
html = html.replace(old, 'async function boot() { // called by the Firebase auth module once sign-in completes', 1)

old = "  showPage('roster', document.getElementById('nav-roster'));\n})();"
if old not in html: sys.exit('ANCHOR MISSING: boot IIFE end')
html = html.replace(old, "  showPage('roster', document.getElementById('nav-roster'));\n}", 1)

# ── 6. inside boot: load COMP_DATA from Firestore + apply signed-in identity ──
old = '  await loadCompChecklist();\n'
if old not in html: sys.exit('ANCHOR MISSING: loadCompChecklist call')
html = html.replace(old, old +
    "  try{ const r=await window.storage.get('app_comp_data'); if(r&&r.value){ COMP_DATA=JSON.parse(r.value)||{}; } }catch(e){}\n"
    '  if (window.__applyIdentity) window.__applyIdentity(); // set role/scoping from the signed-in account before first render\n',
    1)

# ── 7. only real admins may enter god-view ──
old = 'function setViewAs(val){\n'
if old not in html: sys.exit('ANCHOR MISSING: setViewAs')
html = html.replace(old, old +
    "  if(!ADMIN_SESSION && (val==='__admin__' || !val)) return; // server rules are the real gate; this keeps the UI honest\n",
    1)

# ── 8. sidebar sign-out button ──
old = '\n  </nav>'
if old not in html: sys.exit('ANCHOR MISSING: </nav>')
html = html.replace(old, '''
    <div style="margin-top:auto;padding:10px 9px 16px">
      <button class="nav-item" onclick="window.__signOut && window.__signOut()"><span class="nav-icon">🚪</span>Sign out</button>
      <div id="signed-in-email" style="font-size:9.5px;color:#7d86b8;padding:4px 12px 0;word-break:break-all"></div>
    </div>
  </nav>''', 1)

# ── 8b. top-bar log-out button (next to the record-count chip) ──
old = '<span class="count-chip" id="count-chip">—</span>'
if old not in html: sys.exit('ANCHOR MISSING: count-chip')
html = html.replace(old, old + '''
      <button onclick="window.__signOut && window.__signOut()" title="Sign out of Homebase"
        style="display:flex;align-items:center;gap:6px;padding:6px 12px;border:1px solid #e0ddd6;border-radius:9px;background:#faf9f5;color:#8a8680;font-size:12px;font-weight:600;font-family:inherit;cursor:pointer"
        onmouseover="this.style.color='#b91c1c';this.style.borderColor='#fca5a5';this.style.background='#fef2f2'"
        onmouseout="this.style.color='#8a8680';this.style.borderColor='#e0ddd6';this.style.background='#faf9f5'">🚪 Log out</button>''', 1)

# ── 9. inject sign-in overlay + Firebase module before </body> ──
overlay = (APP / 'build' / 'snippet-overlay.html').read_text(encoding='utf-8')
module = (APP / 'build' / 'snippet-module.html').read_text(encoding='utf-8')
old = '</body>'
if old not in html: sys.exit('ANCHOR MISSING: </body>')
html = html.replace(old, overlay + '\n' + module + '\n</body>', 1)

# ── 10. header comment ──
html = html.replace(
    '<!-- APP Roster & Capacity — Advance Psychotherapy Practice | Version: 2026-06-29 | Last updated: June 29, 2026 -->',
    '<!-- APP Homebase — Advance Psychotherapy Practice | Firebase edition (Auth + Firestore) | Built: '
    + datetime.date.today().isoformat() + ' | Data lives in Firestore, NOT in this file -->',
    1)

# ── write outputs ──
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(html, encoding='utf-8')
SEED.parent.mkdir(parents=True, exist_ok=True)
SEED.write_text(json.dumps({
    'generated': datetime.datetime.now().isoformat(timespec='seconds'),
    'staff': staff,               # order matters: index i → doc id S{i}
    'recruit': recruit,           # index i → _id R{i}
    'comp': comp,
    'clinicalHours': hours,
    'groupHours': ghours,
}, indent=1), encoding='utf-8')

print(f'source        : {orig_len:,} chars')
print(f'public/index  : {len(html):,} chars')
print(f'staff records : {len(staff)}  |  recruit: {len(recruit)}  |  comp keys: {len(comp)}')
print(f'hours byId    : {len(hours["byId"])}  |  group byId: {len(ghours["byId"])}')
