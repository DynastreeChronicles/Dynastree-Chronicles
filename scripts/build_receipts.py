#!/usr/bin/env python3
"""The Receipts Archive: receipts/index.html. Run after build_ledger.py:  python scripts/build_receipts.py

Automatic: every issue's `hits` (chat greatest hits), `quote` (quote of the week) and `bold` (predictions, scored from data/history.json).
Hand-fed (data/receipts.json): extra hot takes from the chat log, with status and used_in. Grouped by season (volume), newest first."""
import json, os, random, re, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import build_site as bs
import seasons as ss
from build_site import esc, av, jload, ROOT
R = "../"
KINDS = {"quote": "Quote of the Week", "chat": "Chat Greatest Hit", "take": "Hot Take", "bold": "Bold Prediction"}
STATUS = {"hit": ("Aged well", "ok"), "aged_well": ("Aged well", "ok"), "miss": ("Aged badly", "bad"), "aged_badly": ("Aged badly", "bad"), "pending": ("Pending", "pend")}

def build():
    mg = list(bs.managers()); H = jload("data/history.json", {}) or {}; reg = ss.load()
    res = H.get("predictions") or {}
    def handles(t): return [m for m in mg if m.lower() in t.lower()]
    items, seen = [], set()
    def add(**e):
        k = (re.sub(r"\W+", "", e["text"].lower()), e["who"])
        if k in seen: return
        seen.add(k); items.append(e)
    for y, n, f in sorted(bs.issue_files(), key=lambda x: (x[0], x[1])):
        d = bs.canon(json.load(open(f, encoding="utf-8")))
        q = d.get("quote") or {}
        if q.get("text"):
            who = next((m for m in mg if q.get("by", "").startswith(m)), "")
            add(season=str(y), kind="quote", who=who, text=q["text"], ctx=q.get("by", "")[len(who):].lstrip(", "), issue=n, desk=q.get("desk", ""))
        for h in d.get("hits") or []:
            add(season=str(y), kind="chat", who=h[1], text=h[0], ctx="", issue=n, desk="")
        for i, b in enumerate(d.get("bold") or []):
            r = res.get(f"{y}-{n}-{i}") or {}
            add(season=str(y), kind="bold", who="The desk", text=b[0], ctx=b[1], issue=n, desk=r.get("note", ""), status=r.get("result", "pending"))
    for t in (jload("data/receipts.json", {}) or {}).get("takes", []):
        used = t.get("used_in") or []
        add(season=str(t.get("season", "")), kind="take", who=t.get("who", ""), text=t["text"], ctx=t.get("context", ""), issue=None, desk=t.get("note", ""),
            status=t.get("status", "pending"), date=t.get("date", ""), used=used, tags=t.get("tags") or [])

    def card(e, num):
        who = e["who"] if e["who"] in mg else ""
        head = (f'<a class="ml" href="{R}managers/{who.lower()}/">{av(who, 30, R)}<b>{esc(who)}</b></a>' if who else f'<b>{esc(e["who"] or "Unattributed")}</b>')
        st = STATUS.get(e.get("status", ""), None) if e["kind"] in ("bold", "take") else None
        badges = f'<span class="kind">{KINDS[e["kind"]]}</span>' + (f'<span class="st {st[1]}">{st[0]}</span>' if st else "")
        if e["kind"] == "take" and e.get("used"):
            badges += f'<span class="st fresh">Used in Issue {", ".join(map(str, e["used"]))}</span>'
        src = (f'<a href="{R}issues/{e["season"]}/issue-{e["issue"]:02d}/">Issue {e["issue"]}</a>' if e.get("issue") else esc(e.get("date", "") or "Chat log"))
        tags = "".join(f'<span class="tg">#{esc(x)}</span>' for x in e.get("tags", []))
        mans = " ".join(m.lower() for m in set(([e["who"]] if e["who"] in mg else []) + handles(e["text"] + " " + e["ctx"])))
        bb = f'<img class="rc-b" src="{R}assets/badge-bold-prediction.webp" alt="" width="46" height="49" loading="lazy">' if e["kind"] == "bold" else ""
        body = f'<blockquote>{"&ldquo;" if e["kind"] != "bold" else ""}{esc(e["text"])}{"&rdquo;" if e["kind"] != "bold" else ""}</blockquote>'
        body += f'<p class="cx">{esc(e["ctx"])}</p>' if e["ctx"] else ""
        body += f'<p class="dk">{"Ruling: " if e["kind"] == "bold" else "The desk: "}{esc(e["desk"])}</p>' if e["desk"] else ""
        return (f'<article class="rc" data-k="{e["kind"]}" data-m="{esc(mans)}"><div class="rh"><span class="no">No. {num:03d}</span>{badges}{bb}</div>'
                f'{body}<div class="rf">{head}<span class="sr">{src}</span></div>{("<div class=tgs>" + tags + "</div>") if tags else ""}</article>')

    items.sort(key=lambda e: (e["season"], e.get("issue") or 0), reverse=True)
    num = len(items) + 1; sec = ""
    for i, y in enumerate(dict.fromkeys(e["season"] for e in items)):
        mine = [e for e in items if e["season"] == y]; cards = ""
        for e in mine:
            num -= 1; cards += card(e, num)
        vol = ss.volume(y, reg) if y in reg else ""
        sec += f'<details class="yr rc-sec"{" open" if i == 0 else ""}><summary>{"Volume " + str(vol) + " &middot; " if vol else ""}{esc(y)} <small>{len(mine)} receipts</small></summary><div class="rc-grid">{cards}</div></details>'
    counts = {k: sum(1 for e in items if e["kind"] == k) for k in KINDS}
    chips = "".join(f"<div><b>{v}</b><small>{KINDS[k]}s</small></div>" for k, v in counts.items() if v)
    opts = "".join(f'<option value="{m.lower()}">{esc(m)}</option>' for m in sorted(mg, key=str.lower))
    kb = '<button data-k="all" aria-pressed="true">All</button>' + "".join(f'<button data-k="{k}" aria-pressed="false">{v}s</button>' for k, v in KINDS.items())
    body = (f'<section class="hf-hero"><small>Archiving your receipts</small><h2>The Receipts <i>Archive</i></h2><p>Every hot take, every public negotiation, every prediction with a deadline. Filed by season so the desk can pull it back out when the timing is cruel.</p><div class="hf-stats">{chips}</div></section>'
            f'<div class="rc-bar"><div class="lg-filter" role="group" aria-label="Filter receipts">{kb}</div><div class="rc-ctl"><select id="rcm" aria-label="Manager"><option value="">All managers</option>{opts}</select>'
            f'<input id="rcq" type="search" placeholder="Search receipts" aria-label="Search receipts"><button id="rcr" class="rnd">&#127922; Random receipt</button></div><p id="rcn" class="meta"></p></div>' + sec)
    p = os.path.join(ROOT, "receipts", "index.html"); os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, "w", encoding="utf-8").write(shell(body)); print(f"built receipts page ({len(items)} receipts)")

JS = '''<script>(function(){var K="all",C=[].slice.call(document.querySelectorAll('.rc')),m=document.getElementById('rcm'),q=document.getElementById('rcq'),n=document.getElementById('rcn');
function go(){var s=q.value.toLowerCase(),v=0;C.forEach(function(c){var ok=(K==='all'||c.dataset.k===K)&&(!m.value||(' '+c.dataset.m+' ').indexOf(' '+m.value+' ')>-1)&&(!s||c.textContent.toLowerCase().indexOf(s)>-1);c.hidden=!ok;if(ok)v++});
document.querySelectorAll('.rc-sec').forEach(function(d){var x=d.querySelectorAll('.rc:not([hidden])').length;d.hidden=!x;if(s||K!=='all'||m.value)d.open=!!x});n.textContent=v+' of '+C.length+' receipts'}
document.querySelectorAll('.lg-filter button').forEach(function(b){b.onclick=function(){K=b.dataset.k;document.querySelectorAll('.lg-filter button').forEach(function(x){x.setAttribute('aria-pressed',x===b)});go()}});
m.onchange=go;q.oninput=go;document.getElementById('rcr').onclick=function(){var a=C.filter(function(c){return !c.hidden});if(!a.length)return;var c=a[Math.floor(Math.random()*a.length)];c.closest('details').open=true;c.scrollIntoView({behavior:'smooth',block:'center'});c.classList.remove('flash');void c.offsetWidth;c.classList.add('flash')};go()})();</script>'''

def shell(body):
    fonts = '<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Oswald:wght@500;600;700&display=swap" rel="stylesheet">'
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>The Receipts Archive | Dynastree Chronicles</title><meta name="description" content="Every hot take, quote and bold prediction in the Dynastree dynasty league, filed by season."><meta name="robots" content="noindex">
{fonts}<link rel="stylesheet" href="{R}css/dynastree.css"><link rel="stylesheet" href="{R}css/history.css"><link rel="stylesheet" href="{R}css/ledger.css"><link rel="stylesheet" href="{R}css/receipts.css">
<link rel="icon" type="image/png" sizes="32x32" href="{R}assets/favicon-32.png"><link rel="apple-touch-icon" href="{R}assets/apple-touch-icon.png"></head><body>
<header class="mast"><div class="wrap"><img src="{R}assets/crest-mark.webp" alt="Dynastree Chronicles crest" width="79" height="96"><div><h1><a href="{R}">Dynastree <span>Chronicles</span></a></h1><p>The Receipts Archive</p></div></div></header>
<nav class="sticky"><div class="wrap"><a href="{R}#archive">Issues</a><button class="ddb" type="button" aria-expanded="false" aria-controls="vault">The Vault <i>&#9662;</i></button><a href="{R}#standings">Standings</a><a href="{R}#transactions">Transactions</a><a href="{R}#rules">Rules</a><a href="{R}#scoring">Scoring</a></div><div class="ddm" id="vault" hidden><a href="{R}managers/"><b>Managers</b><small>Meet the suspects</small></a><a href="{R}history/"><b>History</b><small>Hall of Fame &amp; records</small></a><a href="{R}ledger/"><b>Ledger</b><small>Drafts &amp; blockbusters</small></a><a href="{R}receipts/"><b>Receipts</b><small>Hot takes on file</small></a></div></nav>
<main class="wrap">{body}</main>
<footer><div class="wrap"><img class="tree wm" src="{R}assets/logo-dynastree-chronicles.webp" alt="Dynastree Chronicles" width="180" height="69" loading="lazy"><p>Time heals all wounds, but screenshots last forever.</p></div></footer>
<script src="{R}js/site.js"></script><script src="{R}js/nav.js"></script>{JS}</body></html>'''

if __name__ == "__main__":
    build()
