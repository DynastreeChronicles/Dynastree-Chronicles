#!/usr/bin/env python3
"""Draft & Trade Ledger: ledger/index.html. Run after build_history.py:  python scripts/build_ledger.py

Automatic: every draft pick (data/<season>/draft.json) and every trade (data/<season>/transactions.json),
plus the desk's grades and takes from each issue's wire.trades.
Hand-entered (data/ledger.json): pick verdicts (hit / mid / bust, entered years later) and trade obituaries."""
import datetime, glob, json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import build_site as bs
import seasons as ss
import pick_grades as pg
from build_site import esc, av, jload, ROOT
R = "../"
GR = {"hit": ("Hit", "v-hit"), "mid": ("Mid-tier", "v-mid"), "bust": ("Bust", "v-bust")}
NOTES = []
STATS = {}

def norm(n):
    return " ".join(re.sub(r"\b(jr|sr|ii|iii|iv|v)\b", "", re.sub(r"[^a-z ]", "", n.lower().replace("-", " "))).split())

TODAY = datetime.date.today()

def grade_pick(y, p, L):
    """Automatic verdict for one pick, judged after each season ends (see scripts/pick_grades.py). The 2026 startup draft gets one season-long evaluation; rookie drafts get 1, 2 and 3 season evaluations."""
    n = 1 if startup(y, L) else None
    return pg.grade_pick(y, p, L.get("grading", {}), STATS, norm(p["name"]) + "|" + p["pos"], n)

def startup(y, L):
    return bool(((L.get("drafts") or {}).get(str(y)) or {}).get("startup"))

def trail_html(p, au, su=False):
    """One small line per evaluation: '1-season: WR14 (118% of projection) dot'. The startup draft has a single season-long evaluation."""
    bits = []
    for cp in au["cps"]:
        r = f'{p["pos"]}{cp["posrank"] or "-"}'
        lab = "Season-long" if su else f'{cp["k"]}-season'
        if cp["state"] == "graded":
            ratio = f' ({round(cp["ratio"] * 100)}% of projection)' if cp["ratio"] else ""
            bits.append(f'{lab}: {r}{ratio} <span class="dot {GR[cp["grade"]][1]}"></span>')
        else:
            bits.append(f'{lab}: {r} (season in progress) <span class="dot v-pend"></span>')
    return " &middot; ".join(bits)

def ml(m):
    return f'<a class="ml" href="{R}managers/{esc(m.lower())}/">{esc(m)}</a>'

# ------------------------------------------------------------------ drafts
def drafts(L):
    out = []
    for y in sorted(ss.load()):
        d = jload(f"data/{y}/draft.json", None)
        if d:
            out.append((y, (L.get("drafts", {}).get(y) or {}).get("label", f"{y} Draft"), [bs.canon(p) for p in d]))
    return out

def draft_panel(L):
    D, V = drafts(L), L.get("verdicts", {})
    if not D:
        return '<p class="lg-empty">No drafts on record yet.</p>'
    reg = ss.load(); tally, html = {}, ""
    for i, (y, label, picks) in enumerate(reversed(D)):
        su = startup(y, L); rows, cur = "", None
        for p in sorted(picks, key=lambda p: (p["r"], p["s"])):
            if p["r"] != cur:
                cur = p["r"]; rows += f'<tr class="rh"><td colspan="5">Round {cur}</td></tr>'
            v = V.get(f'{y}:{p["r"]}.{p["s"]:02d}') or {}
            au = grade_pick(y, p, L)
            g = v.get("grade") if v.get("grade") in GR else au["grade"]
            lab, cls = GR.get(g, ("Too early", "v-pend"))
            if g and not v.get("grade"): lab += " (final)" if au["final"] else " (so far)"
            trail = trail_html(p, au, su)
            t = tally.setdefault(p["m"], {"hit": 0, "mid": 0, "bust": 0})
            if g: t[g] += 1
            note = (f'<small>{esc(v["note"])}</small>' if v.get("note") else "") + (f'<small>{trail}</small>' if trail else "")
            auto = " <small>(auto-pick)</small>" if p.get("auto") else ""
            rows += (f'<tr class="pk {cls}" data-v="{cls}" data-r="{p["r"]}" data-m="{esc(p["m"].lower())}" data-p="{esc(p["name"].lower())}"><td>{p["r"]}.{p["s"]:02d}</td>'
                     f'<td><b>{esc(p["name"])}</b> <small>{esc(p["pos"])} &middot; {esc(p["team"])}{auto}</small></td>'
                     f'<td>{ml(p["m"])}</td><td><span class="dot {cls}"></span>{lab}</td><td>{note}</td></tr>')
        vol = ss.volume(y, reg) if y in reg else None
        if su:
            nxt = f"Volume {vol + 1}, Issue 1" if vol else "the next volume's Issue 1"
            ev = f"Startup draft: one season-long evaluation, made after the season ends and filed in {nxt}."
        else:
            ev = "Rookie draft: 1, 2 and 3 season evaluations, each made after that season ends. Each new volume's Issue 1 reviews the last three drafts."
        html += (f'<details class="yr dr-sec"{" open" if i == 0 else ""}><summary>{esc(label)} <small>{len(picks)} picks</small></summary><p class="lg-eval">{esc(ev)}</p>'
                 f'<div class="lg-wrap"><table class="lg-tbl"><thead><tr><th>Pick</th><th>Player</th><th>Drafted by</th><th>Verdict</th><th>Notes</th></tr></thead><tbody>{rows}</tbody></table></div></details>')
    graded = {m: t for m, t in tally.items() if sum(t.values())}
    board = ""
    if graded:
        r = sorted(graded.items(), key=lambda kv: (-kv[1]["hit"] / sum(kv[1].values()), kv[0]))
        board = ('<h3 class="sub">Hit rate by manager</h3><div class="lg-wrap"><table class="lg-tbl"><thead><tr><th>Manager</th><th>Hits</th><th>Mid</th><th>Busts</th><th>Hit rate</th></tr></thead><tbody>'
                 + "".join(f'<tr><td>{ml(m)}</td><td>{t["hit"]}</td><td>{t["mid"]}</td><td>{t["bust"]}</td><td>{100 * t["hit"] // sum(t.values())}%</td></tr>' for m, t in r) + '</tbody></table></div>')
    mgrs = sorted({p["m"] for _, _, ps in D for p in ps}, key=str.lower)
    opts = "".join(f'<option value="{esc(m.lower())}">{esc(m)}</option>' for m in mgrs)
    legend = ('<div class="lg-legend"><span><span class="dot v-hit"></span>Hit</span><span><span class="dot v-mid"></span>Mid-tier</span><span><span class="dot v-bust"></span>Bust</span>'
              '<span><span class="dot v-pend"></span>Too early to call</span></div>'
              '<div class="lg-filter" role="group" aria-label="Filter picks"><button data-f="all" aria-pressed="true">All</button><button data-f="v-hit" aria-pressed="false">Hits</button>'
              '<button data-f="v-mid" aria-pressed="false">Mid-tier</button><button data-f="v-bust" aria-pressed="false">Busts</button><button data-f="v-pend" aria-pressed="false">Ungraded</button></div>'
              f'<div class="lg-ctl"><select id="dgm" aria-label="Manager"><option value="">All managers</option>{opts}</select>'
              '<input id="dgq" type="search" placeholder="Search player" aria-label="Search player"></div><p id="dgn" class="meta"></p>')
    return legend + html + board

# ------------------------------------------------------------------ trades
def issue_takes():
    """{(frozenset(pair)): [(match, grade_a, grade_b, desk, a, b, issue_no)]} from every issue's wire.trades."""
    out = {}
    for y, n, f in bs.issue_files():
        d = bs.canon(json.load(open(f, encoding="utf-8")))
        for t in (d.get("wire") or {}).get("trades") or []:
            out.setdefault(frozenset((t["a"], t["b"])), []).append((t.get("match", ""), t, y, n))
    return out

def assets(side):
    a = [f'{p["name"]} ({p["pos"]}, {p["team"]})' for p in side.get("receives_players", [])]
    a += [f'{k["season"]} round {k["round"]} pick (from {k["original_owner"]})' for k in side.get("receives_picks", [])]
    if side.get("receives_faab"): a.append(f'${side["receives_faab"]} FAAB')
    return a

def score(tx, S):
    pv = S.get("pick_value", {}); n = 0
    for sd in tx["sides"]:
        n += len(sd.get("receives_players", [])) * S.get("player_value", 25)
        n += sum(pv.get(str(k["round"]), 0) for k in sd.get("receives_picks", []))
        n += (sd.get("receives_faab") or 0) // 10
    return n

def legend(S):
    pv = S.get("pick_value", {}); pl = S.get("player_value", 25)
    chips = [("1st-round pick", pv.get("1", 50)), ("2nd-round pick", pv.get("2", 30)), ("3rd-round pick", pv.get("3", 10)),
             ("Each player", pl), ("Each $10 FAAB", 1)]
    return ('<div class="lg-score"><div class="hd"><b>How the Blockbuster score works</b></div><div class="chips">'
            + "".join(f'<div class="chip"><strong>{v}</strong><small>{esc(k)}</small></div>' for k, v in chips) + '</div></div>')

def trade_panel(L):
    S, T, takes, reg = L.get("settings", {}), L.get("trades", {}), issue_takes(), ss.load()
    by = {}
    for y in sorted(reg):
        for tx in jload(f"data/{y}/transactions.json", []) or []:
            if tx.get("type") == "trade" and len(tx.get("sides", [])) == 2:
                c = bs.canon(tx); by.setdefault(y, []).append((score(c, S), c))
    if not by:
        return '<p class="lg-empty">No trades on record yet.</p>'
    def card_parts(sc, tx):
        a, b = tx["sides"]; meta = T.get(str(tx["id"])) or {}
        txt = " ".join(assets(a) + assets(b))
        take = next((t for m, t, ty, n in takes.get(frozenset((a["manager"], b["manager"])), []) if not m or m in txt), None)
        date = datetime.datetime.fromtimestamp(tx.get("created", 0) / 1000, datetime.timezone.utc).strftime("%b %d, %Y")
        big = sc >= S.get("blockbuster_min", 60); obit = ""
        if meta.get("status") == "deceased":
            obit = (f'<div class="obit"><small>In loving memory &middot; {esc(date)}</small><h3>{esc(meta.get("headline", "A trade that did not survive"))}</h3>'
                    f'<p>{ml(a["manager"])} and {ml(b["manager"])} announce the passing of this deal.</p>'
                    f'<p><b>Cause of death:</b> {esc(meta.get("cause", "Unspecified"))}</p><p>{esc(meta.get("obituary", ""))}</p>'
                    + (f'<p><b>Survived by:</b> {esc(meta["survived_by"])}</p>' if meta.get("survived_by") else "") + '</div>')
        grade, desk = "", ""
        if take:
            if take.get("ga") and take.get("gb"): grade = f' &middot; Grades: {esc(a["manager"])} {esc(take["ga"])}, {esc(b["manager"])} {esc(take["gb"])}'
            desk = f'<p class="desk">The desk: {esc(take["desk"])}</p>' if take.get("desk") else ""
        status = {"alive": "Still standing", "pending": "Verdict pending"}.get(meta.get("status"), "Verdict pending")
        side = lambda s, o: f'<div><b>{ml(s["manager"])} gets</b><p>{esc("; ".join(assets(s)) or "nothing")}</p></div>'
        card = (f'<article class="tx-card{" big" if big else ""}"><h3>{"<span class=\"tag\">Blockbuster</span>" if big else ""}{esc(a["manager"])} &harr; {esc(b["manager"])}</h3>'
                f'<p class="meta">{esc(date)} &middot; Week {tx.get("week", "?")} &middot; Blockbuster score {sc} &middot; {status}{grade}</p>'
                f'<div class="sides">{side(a, b)}{side(b, a)}</div>{desk}</article>')
        return card, obit
    def year_block(y, inner, n, noun, first):
        vol = ss.volume(y, reg)
        return f'<details class="yr"{" open" if first else ""}><summary>{"Volume " + str(vol) + " &middot; " if vol else ""}{esc(y)} <small>{n} {noun}</small></summary><div class="lg-cards">{inner}</div></details>'
    trades, obits, first_t, first_o = "", "", True, True
    for y in sorted(by, reverse=True):
        items = sorted(by[y], key=lambda i: (-i[0], i[1].get("created", 0)))
        cards, ob = [], []
        for sc, tx in items:
            c, o = card_parts(sc, tx); cards.append(c)
            if o: ob.append(o)
        trades += year_block(y, "".join(cards), len(cards), "trade" + ("" if len(cards) == 1 else "s"), first_t); first_t = False
        if ob:
            obits += year_block(y, "".join(ob), len(ob), "obituar" + ("y" if len(ob) == 1 else "ies"), first_o); first_o = False
    cem = obits or '<p class="lg-empty">The cemetery is empty. For now. Obituaries get filed once a trade has clearly gone wrong.</p>'
    return (legend(S) + '<h3 class="sub">Every trade, biggest first</h3>' + trades + '<h3 class="sub">Obituaries</h3>' + cem)

# ------------------------------------------------------------------ page
JS = '''<script>(function(){var t=document.querySelectorAll('.lg-tabs button'),p=document.querySelectorAll('.lg-panel');
function show(id){t.forEach(function(b){b.setAttribute('aria-selected',b.dataset.t===id)});p.forEach(function(x){x.hidden=x.id!==id})}
t.forEach(function(b){b.onclick=function(){show(b.dataset.t);history.replaceState(null,'','#'+b.dataset.t)}});
show(location.hash==='#drafts'?'drafts':'trades');
var K='all',R=[].slice.call(document.querySelectorAll('tr.pk')),m=document.getElementById('dgm'),q=document.getElementById('dgq'),n=document.getElementById('dgn');
function go(){if(!m)return;var s=q.value.toLowerCase().trim(),v=0,f=K!=='all'||m.value||s;
R.forEach(function(r){var ok=(K==='all'||r.dataset.v===K)&&(!m.value||r.dataset.m===m.value)&&(!s||r.dataset.p.indexOf(s)>-1);r.hidden=!ok;if(ok)v++});
document.querySelectorAll('tr.rh').forEach(function(h){var x=h.nextElementSibling,any=false;while(x&&!x.classList.contains('rh')){if(!x.hidden)any=true;x=x.nextElementSibling}h.hidden=!any});
document.querySelectorAll('.dr-sec').forEach(function(d){var c=d.querySelectorAll('tr.pk:not([hidden])').length;d.hidden=!c;if(f)d.open=!!c});
n.textContent=v+' of '+R.length+' picks'}
document.querySelectorAll('.lg-filter button').forEach(function(b){b.onclick=function(){K=b.dataset.f;document.querySelectorAll('.lg-filter button').forEach(function(x){x.setAttribute('aria-pressed',x===b)});go()}});
if(m){m.onchange=go;q.oninput=go}go()})();</script>'''

def shell(body):
    fonts = '<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Oswald:wght@500;600;700&display=swap" rel="stylesheet">'
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Draft &amp; Trade Ledger | Dynastree Chronicles</title><meta name="description" content="Every draft pick graded and every blockbuster trade on record in the Dynastree dynasty league."><meta name="robots" content="noindex">
{bs.og_block("Draft & Trade Ledger | Dynastree Chronicles", "Every draft pick graded and every blockbuster trade on record in the Dynastree dynasty league.", "ledger/")}
{fonts}<link rel="stylesheet" href="{R}css/dynastree.css"><link rel="stylesheet" href="{R}css/history.css"><link rel="stylesheet" href="{R}css/ledger.css">
<link rel="icon" type="image/png" sizes="32x32" href="{R}assets/favicon-32.png"><link rel="apple-touch-icon" href="{R}assets/apple-touch-icon.png"></head><body>
<a class="skip" href="#main">Skip to main content</a>
<header class="mast"><div class="wrap"><img src="{R}assets/crest-mark.webp" alt="Dynastree Chronicles crest" width="79" height="96"><div><h1><a href="{R}">Dynastree <span>Chronicles</span></a></h1><p>Draft &amp; Trade Ledger</p></div></div></header>
<nav class="sticky"><div class="wrap"><a href="{R}#archive">Issues</a><button class="ddb" type="button" aria-expanded="false" aria-controls="vault">The Vault <i>&#9662;</i></button><a href="{R}#standings">Standings</a><a href="{R}#transactions">Transactions</a><a href="{R}#market">The Market</a><a href="{R}#rules">Rules</a><a href="{R}#scoring">Scoring</a></div><div class="ddm" id="vault" hidden><a href="{R}managers/"><b>Managers</b><small>Meet the suspects</small></a><a href="{R}history/"><b>History</b><small>Hall of Fame &amp; records</small></a><a href="{R}ledger/"><b>Ledger</b><small>Drafts &amp; blockbusters</small></a><a href="{R}receipts/"><b>Receipts</b><small>Hot takes on file</small></a></div></nav>
<main class="wrap" id="main" tabindex="-1">{body}</main>
<footer><div class="wrap"><img class="tree wm" src="{R}assets/logo-dynastree-chronicles.webp" alt="Dynastree Chronicles" width="180" height="69" loading="lazy"><p>Time heals all wounds, but screenshots last forever.</p></div></footer>
<script src="{R}js/site.js"></script><script src="{R}js/nav.js"></script>{JS}</body></html>'''

def build():
    L = jload("data/ledger.json", {}) or {}
    for f in glob.glob(os.path.join(ROOT, "data", "stats", "*.json")):
        STATS[os.path.basename(f)[:-5]] = json.load(open(f, encoding="utf-8"))
    hero = ('<section class="hf-hero"><small>Receipts on file</small><h2>Draft <i>&amp;</i> Trade Ledger</h2>'
            '<p>In dynasty, draft capital is everything. See how every pick aged and which trades deserve a eulogy.</p></section>')
    body = (hero + '<div class="lg-tabs" role="tablist"><button data-t="trades" role="tab">The Blockbuster Registry</button><button data-t="drafts" role="tab">All-Time Draft History</button></div>'
            f'<section class="lg-panel" id="drafts" hidden>{draft_panel(L)}</section><section class="lg-panel" id="trades">{trade_panel(L)}</section>')
    p = os.path.join(ROOT, "ledger", "index.html"); os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, "w", encoding="utf-8").write(shell(body))
    print(f'built ledger page ({len(L.get("verdicts", {}))} verdicts, {len(L.get("trades", {}))} trade notes)')

if __name__ == "__main__":
    build()
