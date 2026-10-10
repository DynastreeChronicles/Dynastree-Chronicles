#!/usr/bin/env python3
"""Manager pages: managers/index.html (the league hub) + managers/<handle>/index.html (one per manager).
Everything numeric comes from data/ (same sources as build_site.py); desk quotes are mined from data/issues/*.json.
Run after build_site.py:  python scripts/build_managers.py"""
import glob, json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import build_site as bs
import seasons as ss
import trophies as tr
from build_site import esc, av, jload, ROOT

slug = lambda m: m.lower()
FONTS = '<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Oswald:wght@500;600;700&display=swap" rel="stylesheet">'

def shell(title, desc, body, r, sub, path=""):
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)} | Dynastree Chronicles</title><meta name="description" content="{esc(desc)}"><meta name="robots" content="noindex">
{bs.og_block(title + " | Dynastree Chronicles", desc, path)}
{FONTS}<link rel="stylesheet" href="{r}css/dynastree.css"><link rel="stylesheet" href="{r}css/managers.css">
<link rel="icon" type="image/png" sizes="32x32" href="{r}assets/favicon-32.png"><link rel="apple-touch-icon" href="{r}assets/apple-touch-icon.png"></head><body>
<a class="skip" href="#main">Skip to main content</a>
<header class="mast"><div class="wrap"><img src="{r}assets/crest-mark.webp" alt="Dynastree Chronicles crest" width="79" height="96"><div><h1><a href="{r}">Dynastree <span>Chronicles</span></a></h1><p>{esc(sub)}</p></div></div></header>
<nav class="sticky"><div class="wrap"><button class="ddb" type="button" aria-expanded="false" aria-controls="vault">The Vault <i>&#9662;</i></button><a href="{r}#standings">Standings</a><a href="{r}#transactions">Transactions</a><a href="{r}#market">The Market</a><a href="{r}#archive">Issues</a><a href="{r}#rules">Rules</a><a href="{r}#scoring">Scoring</a></div><div class="ddm" id="vault" hidden><a href="{r}managers/"><b>Managers</b><small>Meet the suspects</small></a><a href="{r}history/"><b>History</b><small>Hall of Fame &amp; records</small></a><a href="{r}ledger/"><b>Ledger</b><small>Drafts &amp; blockbusters</small></a><a href="{r}receipts/"><b>Receipts</b><small>Hot takes on file</small></a></div></nav>
<main class="wrap" id="main" tabindex="-1">{body}</main>
<footer><div class="wrap"><img class="tree wm" src="{r}assets/logo-dynastree-chronicles.webp" alt="Dynastree Chronicles" width="180" height="69" loading="lazy"><p>Time heals all wounds, but screenshots last forever.</p></div></footer><script src="{r}js/nav.js"></script></body></html>'''

def desk_quotes(m, years):
    """Every desk aside that names this manager, newest issue first: (issue_no, year, section, anchor, text)."""
    out = []
    for y, n, f in bs.issue_files():   # every season's issues, newest first; (season, no) keeps volumes apart
        d = bs.canon(json.load(open(f, encoding="utf-8")))
        add = lambda sec, anc, t, n=n, y=y: t and out.append((n, y, sec, anc, t))
        for para in d.get("desk") or []:   # the lead column: pull just the sentences that name them
            for sent in re.split(r"(?<=[.!?])\s+", para):
                if re.search(rf"\b{re.escape(m)}\b", sent): add("From the desk", "desk", sent)
        w = d.get("wire", {})
        add("Transaction wire", "wire", (w.get("desk") or {}).get(m))
        for t in w.get("trades", []):
            if m in (t.get("a"), t.get("b")): add("Trade wire", "wire", t.get("desk"))
        for key, sec, anc in (("post", "Post-game", "post"), ("pre", "Pre-game", "pregame"), ("draft", "Draft grades", "post")):
            for x in d.get(key, []):
                if m in (x.get("a"), x.get("b"), x.get("m")): add(sec, anc, x.get("desk"))
        mo = d.get("motw") or {}
        if m in (mo.get("a"), mo.get("b")): add("Match of the Week", "pregame", mo.get("desk"))
        for x in (d.get("trades") or {}).get("items", []):
            if m in (x.get("a"), x.get("b")): add("Trade machine", "trades", x.get("desk"))
        for x in d.get("drama", []):
            if re.search(rf"\b{re.escape(m)}\b", x.get("h", "") + x.get("p", "")): add("Drama", "drama", x.get("desk"))
        q = d.get("quote") or {}
        if m in q.get("by", ""): add("Quote of the week", "drama", q.get("desk"))
        for k in ("hero", "zero"):
            if (d.get(k) or {}).get("manager") == m: add(k.title(), "desk", d[k].get("desk"))
        add("Bankroll watch", "bankroll", (d.get("bank") or {}).get("notes", {}).get(m) if isinstance(d.get("bank"), dict) else None)
    seen = set(); return [q for q in out if not (q[4] in seen or seen.add(q[4]))]

def form_strip(games):
    mx = max([g["points"] for g in games] + [1])
    return '<div class="form" role="img" aria-label="Weekly scores">' + "".join(
        f'<div class="fw {g["result"].lower()}"><b>{g["points"]:.0f}</b><i style="height:{max(8, g["points"] / mx * 100):.0f}%"></i><small>Wk {g["week"]}</small></div>' for g in games) + '</div>'

def games_for(m, thru):
    return [{**t, "week": w["week"]} for w in bs.final_weeks(thru) for t in w["teams"] if t["manager"] == m]

def log_table(games):
    rows = "".join(f'<tr><td class="n">{g["week"]}</td><td>vs {av(g["opponent"], 20, "../../")}{esc(g["opponent"])}</td><td class="n res {g["result"].lower()}">{g["result"]}</td>'
                   f'<td class="n">{g["points"]:.2f}</td><td class="n">{g["opponent_points"]:.2f}</td><td class="n">{g["left_on_bench"]:.1f}</td><td>{esc(bs.pname(g["mvp"]))} {g["mvp"]["pts"]:.1f}</td></tr>' for g in games)
    return f'<div class="sc"><table><thead><tr><th class="n">Wk</th><th>Opponent</th><th class="n">Res</th><th class="n">PF</th><th class="n">PA</th><th class="n">Bench left</th><th>MVP</th></tr></thead><tbody>{rows}</tbody></table></div>'

def tx_block(m, thru):
    tx = sorted((t for t in bs.txfeed() if t["week"] <= thru + 1), key=lambda t: -(t.get("created") or 0))
    mine = [t for t in tx if (t["type"] == "trade" and any(s["manager"] == m for s in t["sides"])) or t.get("manager") == m]
    if not mine: return '<p class="key">No transactions yet. The desk is suspicious of this much patience.</p>', 0, 0
    spent = sum(t.get("bid") or 0 for t in mine if t["type"] != "trade"); out = []
    for wk in sorted({t["week"] for t in mine}, reverse=True):
        out.append(f'<h3 class="wk">Week {wk}</h3><div class="txg">')
        for t in (x for x in mine if x["week"] == wk):
            if t["type"] == "trade":
                me = next(s for s in t["sides"] if s["manager"] == m); other = next(s for s in t["sides"] if s is not me)
                out.append(f'<div class="txr tr"><span class="tg trade">&#129309; TRADE</span><span class="pn">with {esc(other["manager"])}</span><span></span></div>'
                           f'<div class="mtr"><div><small>Got</small><ul class="assets">{"".join(f"<li class=bd>{esc(a)}</li>" for a in bs.asset_list(me, other)) or "<li class=bd>nothing</li>"}</ul></div>'
                           f'<div><small>Sent</small><ul class="assets">{"".join(f"<li class=bd>{esc(a)}</li>" for a in bs.asset_list(other, me)) or "<li class=bd>nothing</li>"}</ul></div></div>')
            else:
                a = t["added"]; out.append(bs.move_html([m, a["name"], t.get("bid") or 0, ", ".join(t.get("dropped") or []), "", "", a.get("pos", "")]))
        out.append('</div>')
    return "".join(out), len(mine), spent

def mine(m, years, season):
    """Takes and drama that name this manager, bucketed by year: {year: {"takes": [...], "drama": [...]}}"""
    out = {}; nm = re.compile(rf"\b{re.escape(m)}\b")
    for y, n, f in bs.issue_files():
        d = bs.canon(json.load(open(f, encoding="utf-8"))); b = out.setdefault(y, {"takes": [], "drama": []})
        for x in d.get("drama", []):
            if nm.search(x.get("h", "") + x.get("p", "")): b["drama"].append((n, x.get("heat") or 0, x.get("h", ""), x.get("p", ""), x.get("desk", "")))
        q = d.get("quote") or {}
        if nm.search(q.get("by", "")) and q.get("text"): b["takes"].append(("chat", n, q["text"], q["by"]))
        for h in d.get("hits", []):
            if len(h) > 1 and h[0] and nm.search(h[1]): b["takes"].append(("chat", n, h[0], h[1]))
        for c in d.get("bold", []):
            if len(c) > 1 and nm.search(c[0] + " " + c[1]): b["takes"].append(("call", n, c[0], c[1]))
    return out

def season_line(m, row, eff, games, rank_pf, spent, ntx, ntr, closed=False):
    best = max(games, key=lambda g: g["points"]); low = min(games, key=lambda g: g["points"])
    verb = "finished" if closed else "is"
    s = (f'{m} {verb} {bs.ordinal(row["rank"])} at {row["record"]} with {row["pf"]:.1f} points, {bs.ordinal(rank_pf)} in the league in scoring. '
         f'The high was {best["points"]:.2f} in Week {best["week"]} and the low {low["points"]:.2f} in Week {low["week"]}. '
         f'{ntx} transactions{"" if closed else " so far"} ({ntr} trade{"" if ntr == 1 else "s"}), ${spent} spent on the wire, ${row["faab_remaining"]} left, and the rookie pick {"landed at" if closed else "sits at"} 1.{row["draft_pick"]:02d}.')
    return s + (f' Lineup efficiency: {eff["efficiency"]}%.' if eff else "")

def takes_html(items, r):
    out = []
    for k, n, a, b in items:
        if k == "chat": out.append(f'<figure class="tk"><blockquote>&ldquo;{esc(a)}&rdquo;</blockquote><figcaption>Issue {n}: {esc(b)}</figcaption></figure>')
        else: out.append(f'<p class="call"><b>Issue {n} prediction.</b> {esc(a.rstrip("."))}: {esc(b)}</p>')
    return "".join(out)

def drama_html(items):
    return "".join(f'<article class="dm"><span class="hd" style="--c:hsl({max(0, 214 - int(h * 2.14))} 94% 56%)"><b>{h}</b>&deg;F</span><div><h4>{esc(t)}</h4><p>{esc(p)}</p>' + (f'<p class="desk">{esc(d)}</p>' if d else "") + f'<small>Issue {n}</small></div></article>' for n, h, t, p, d in items)

REG = ss.load()
_SD = {}

def sdata(m, y):
    """Everything about manager m in season y, read from data/<y>/ only (None if they were not in that season)."""
    k = (m, str(y))
    if k in _SD: return _SD[k]
    bs.use(y)
    rows = jload(bs.S("standings.json"), []) or []
    row = next((r for r in rows if r["manager"] == m), None)
    out = None
    if row:
        thru = max((jload(bs.S("league.json"), {}) or {}).get("weeks_with_scores") or [1])
        eff = next((e for e in (jload(bs.S("efficiency.json"), []) or []) if e["manager"] == m), None)
        games = games_for(m, thru); tx_html, ntx, spent = tx_block(m, thru)
        ntr = sum(1 for t in bs.txfeed() if t["type"] == "trade" and any(x["manager"] == m for x in t["sides"]))
        out = dict(season=str(y), row=row, rows=rows, eff=eff, games=games, thru=thru, tx_html=tx_html, ntx=ntx, spent=spent, ntr=ntr,
                   rank_pf=1 + sum(1 for x in rows if x["pf"] > row["pf"]), closed=ss.is_closed(REG.get(str(y))))
    _SD[k] = out
    return out

HI = ("Best week", "FAAB spent")   # the two extra tiles that get the green value

def stat_tiles(d):
    row, eff = d["row"], d["eff"]
    stats = [("Record", row["record"]), ("Rank", f'#{row["rank"]}'), ("Points for", f'{row["pf"]:.1f}'), ("Points against", f'{row["pa"]:.1f}'),
             ("MAXPF", f'{row["maxpf"]:.1f}'), ("Efficiency", f'{eff["efficiency"]}%' if eff else "n/a"), ("Draft slot", f'1.{row["draft_pick"]:02d}'),
             ("FAAB left", f'${row["faab_remaining"]}'), ("Moves", str(d["ntx"]))]
    best = max(d["games"], key=lambda g: g["points"]) if d.get("games") else None
    if best:
        stats += [("Best week", f'{best["points"]:.2f}', f'Week {best["week"]}'), ("FAAB spent", f'${d["spent"]}', "")]
    return "".join(f'<div{" class=hi" if t[0] in HI else ""}><small>{t[0]}</small><b>{t[1]}</b>{f"<i>{t[2]}</i>" if len(t) > 2 and t[2] else ""}</div>' for t in stats)

def seasons_of(m):
    """Seasons (oldest to newest) in which this manager has a row in that season's own standings."""
    return [s_ for s_ in sorted(REG) if sdata(m, s_)]

def is_active(m, display_names):
    e = bs.managers().get(m) or {}
    return bool(e["active"]) if "active" in e else m in display_names

TROPHY_CASE = {}   # {manager: [{"key", "year", "note"}]}, filled once in main from build_history.trophy_wins()

def load_trophy_case():
    """Decided trophies by manager. Never lets a problem here stop the manager pages from building."""
    try:
        import build_history as bh
        return bh.trophy_wins()
    except Exception as e:
        print(f"  note (trophy case skipped: {e})")
        return {}

PORTFOLIO = {}   # data/<display season>/portfolio.json, filled once in main (empty = no portfolio block anywhere)

STATUS_RULE = ("Market crash: the 30-day market move is -5% or worse, or 25% or more of the value is on IR or out. Correction: down 2.5% or more. "
               "Bull run: up 5% or more. Stable: anything else.")
STATUS = {   # status -> (badge, headline). {m} is the manager handle; swap the wording freely, the logic lives in pull_values.py
    "crash": ("Market crash", "Market Crash: {m} is bleeding capital."),
    "correction": ("Correction", "Correction: {m}'s portfolio is down. Nobody has panicked yet."),
    "bull": ("Bull run", "Bull Run: {m}'s portfolio is printing."),
    "stable": ("Stable", "Stable: {m}'s portfolio is holding. Boring, but solvent."),
}
POS_COLOR = {"QB": "#ff6b6b", "RB": "#45e03a", "WR": "#2f6df0", "TE": "#f0b429", "PICK": "#8fb4ff"}

def history_chart(m):
    """Inline SVG line chart of this manager's portfolio value, one point per pull. Needs two points to draw a line."""
    pts = [(h["date"], h["totals"][m]) for h in PORTFOLIO.get("history", []) if m in h.get("totals", {})]
    if len(pts) < 2:
        return ""   # the line appears once there are two snapshots
    W, H, P = 640, 150, 14
    lo, hi = min(v for _, v in pts), max(v for _, v in pts); span = (hi - lo) or 1
    xy = [(P + i * (W - 2 * P) / (len(pts) - 1), H - P - (v - lo) * (H - 2 * P) / span) for i, (_, v) in enumerate(pts)]
    path = " ".join(f"{'M' if i == 0 else 'L'}{x:.1f},{y:.1f}" for i, (x, y) in enumerate(xy))
    return (f'<svg class="pchart" viewBox="0 0 {W} {H}" role="img" aria-label="Portfolio value from {esc(pts[0][0])} to {esc(pts[-1][0])}: {pts[0][1]:,} to {pts[-1][1]:,}">'
            f'<path d="{path}" fill="none" stroke="currentColor" stroke-width="3" stroke-linejoin="round"/>'
            f'<circle cx="{xy[-1][0]:.1f}" cy="{xy[-1][1]:.1f}" r="5" fill="currentColor"/></svg>'
            f'<p class="key">{esc(pts[0][0])} to {esc(pts[-1][0])}. Low {lo:,}, high {hi:,}.</p>')

def portfolio_block(m, r):
    t = (PORTFOLIO.get("teams") or {}).get(m)
    if not t:
        return ""
    badge, head = STATUS[t["status"]]
    sign = lambda n: f"+{n:,}" if n > 0 else f"{n:,}"
    tiles = "".join(f'<div><small>{a}</small><b>{b}</b></div>' for a, b in (
        ("Portfolio value", f'{t["total"]:,}'), ("League rank", f'#{t["rank"]} of {len(PORTFOLIO["teams"])}'),
        ("30-day market move", f'{sign(t["move30"])} ({t["move30_pct"]:+.1f}%)'), ("On IR or out", f'{t["sidelined"]:,} ({t["sidelined_pct"]:.0f}%)'),
        ("Draft capital", f'{t["picks"]:,}'), ("League average", f'{PORTFOLIO["league_avg"]:,}')))
    tot = sum(t["by_pos"].values()) or 1
    bar = "".join(f'<i style="width:{100 * v / tot:.2f}%;background:{POS_COLOR.get(k, "#9fb0d6")}" title="{k} {v:,}"></i>' for k, v in sorted(t["by_pos"].items(), key=lambda kv: -kv[1]))
    key = " ".join(f'<span><i style="background:{POS_COLOR.get(k, "#9fb0d6")}"></i>{k} {100 * v / tot:.0f}%</span>' for k, v in sorted(t["by_pos"].items(), key=lambda kv: -kv[1]))
    def row(a):
        tag = f' <em class="out">{esc(a["status"] or "OUT")}</em>' if a["sidelined"] else ""
        return f'<tr><td>{esc(a["name"])}{tag}</td><td>{esc(a["pos"])}</td><td>{a["value"]:,}</td><td class="{"dn" if a["trend30"] < 0 else "up"}">{a["trend30"]:+,}</td></tr>'
    allp = t.get("assets") or t["top"]          # full roster once the new data is on file, else the old top six
    TOPN = 6
    first = "".join(row(a) for a in allp[:TOPN]); rest_a = "".join(row(a) for a in allp[TOPN:])
    pl = t.get("pick_list", [])
    valued = [x for x in pl if x["value"] > 0]
    PN = 8
    def prow_one(x):
        via = f' <em class="via">via {esc(x["via"])}</em>' if x.get("via") else ""
        return (f'<tr><td>{esc(x["label"])}{via}</td><td>{x["value"]:,}</td>'
                f'<td class="{"dn" if x["trend30"] < 0 else "up"}">{x["trend30"]:+,}</td></tr>')
    pfirst = "".join(prow_one(x) for x in valued[:PN]); prest = "".join(prow_one(x) for x in valued[PN:] + [x for x in pl if x["value"] <= 0])
    def more_btn(tid, n, noun):
        return f'<button type="button" class="showmore" aria-expanded="false" data-t="{tid}" data-more="Show all {n} {noun}" data-less="Show fewer {noun}">Show all {n} {noun}</button>' if n else ""
    picks_tab = (f'<table class="ptab"><caption>Draft picks owned</caption><thead><tr><th>Pick</th><th>Value</th><th>30d</th></tr></thead><tbody>{pfirst}</tbody>'
                 f'<tbody id="pk-more" hidden>{prest}</tbody></table>{more_btn("pk-more", len(valued[PN:]) + len([x for x in pl if x["value"] <= 0]), "picks")}' if pl else "")
    return (f'<h2 class="sec" id="portfolio">Portfolio value</h2><section class="port {t["status"]}"><p class="pflag"><b>{badge}</b> {esc(head.format(m=m))}</p>'
            f'<div class="mstats">{tiles}</div>{history_chart(m)}<div class="pbar">{bar}</div><p class="pkey">{key}</p>'
            f'<table class="ptab"><caption>Biggest holdings</caption><thead><tr><th>Asset</th><th>Pos</th><th>Value</th><th>30d</th></tr></thead><tbody>{first}</tbody><tbody id="as-more" hidden>{rest_a}</tbody></table>{more_btn("as-more", len(allp[TOPN:]), "players")}{picks_tab}'
            f'<details class="legend wide"><summary>Legend: what these numbers mean</summary>'
            f'<p>Values: <a href="https://www.fantasycalc.com">FantasyCalc</a> dynasty trade values, superflex, 12 teams, full PPR.</p><dl>'
            f'<div><dt>Portfolio value</dt><dd>The combined FantasyCalc value of every player on the roster plus every future pick owned. Players outside FantasyCalc\'s top 1,000 count as zero.</dd></div>'
            f'<div><dt>League rank</dt><dd>Where this portfolio sits among all 12, highest value first.</dd></div>'
            f'<div><dt>30-day market move</dt><dd>How much the market moved the value of the players and picks held right now over the last 30 days, in points and percent. Trades do not change it.</dd></div>'
            f'<div><dt>On IR or out</dt><dd>Value sitting on players who are on IR or listed Out, PUP, Doubtful or Suspended, and the share of the portfolio that is.</dd></div>'
            f'<div><dt>Draft capital</dt><dd>The combined value of the future picks this manager owns after trades. Picks use FantasyCalc\'s own pick values. For the next draft the tier (early, mid or late) comes from the original owner\'s current draft slot.</dd></div>'
            f'<div><dt>League average</dt><dd>The average portfolio value across all 12 managers.</dd></div>'
            f'<div><dt>Status flag</dt><dd>{STATUS_RULE}</dd></div></dl></details></section>')

def trophy_case(m, r):
    """A manager's trophy case: only trophies they have actually won. Empty (no section at all) until the first one lands."""
    wins = TROPHY_CASE.get(m) or []
    if not wins:
        return ""
    cards = []
    for key in tr.CASE_ORDER:
        mine = sorted((w for w in wins if w["key"] == key), key=lambda w: w["year"])
        if not mine:
            continue
        times = f'<em>{len(mine)}&times;</em>' if len(mine) > 1 else ""
        lines = "".join(f'<li><b>{esc(w["year"])}</b>{" &middot; " + esc(w["note"]) if w["note"] else ""}</li>' for w in mine)
        cards.append(f'<li class="tc">{tr.img(key, r, cls="tc-img", small=True)}<div><small>{esc(tr.label(key))}{times}</small><ul>{lines}</ul></div></li>')
    return f'<h2 class="sec" id="trophies">Trophy case</h2><ul class="tcase">{"".join(cards)}</ul>'

def manager_page(m, names, years, display, active):
    r = "../../"
    info = (bs.managers().get(m) or {}); team = info.get("team_name"); bio = jload(f"data/bios/{m}.json", {}) or {}
    former = ('<p class="key">Formerly ' + esc(", ".join(info["former_names"])) + "</p>") if info.get("former_names") else ""
    mine_seasons = seasons_of(m); last = mine_seasons[-1] if mine_seasons else None; hd = sdata(m, last) if last else None
    qs = desk_quotes(m, years); mined = mine(m, years, display)
    ring = names.index(m) if m in names else None
    status = "" if active or not last else f'<p class="key">Alumni. Last played in {esc(last)}.</p>'
    seasons = bio.get("seasons") or {}; ys = sorted({*mine_seasons, *map(str, seasons), *(str(k) for k, v in mined.items() if v["takes"] or v["drama"])}, reverse=True); blocks = []
    for y in ys:
        sd = sdata(m, y); hero_season = bool(hd) and y == last
        bs_ = seasons.get(y, {}); mi = mined.get(int(y), {"takes": [], "drama": []}) if y.isdigit() else {"takes": [], "drama": []}
        paras = ([season_line(m, sd["row"], sd["eff"], sd["games"], sd["rank_pf"], sd["spent"], sd["ntx"], sd["ntr"], sd["closed"])] if sd and sd["games"] else []) + bs_.get("story", [])
        head = f'<h3 class="hl">{esc(bs_["headline"])}</h3>' if bs_.get("headline") else ""
        asof = f'<p class="key">Desk bio, written after {esc(bs_["asof"])}. The season line above updates itself.</p>' if bs_.get("asof") else ""
        story = head + "".join(f"<p>{bs.bold_handles(x)}</p>" for x in paras) + asof or '<p class="key">No story filed for this season yet.</p>'
        tk = takes_html(mi["takes"], r) + "".join(f'<figure class="tk"><blockquote>{esc(x)}</blockquote></figure>' for x in bs_.get("takes", []))
        dm = drama_html(mi["drama"]) + "".join(f'<article class="dm"><div><p>{esc(x)}</p></div></article>' for x in bs_.get("drama", []))
        extra = ""
        if sd:
            qh = "".join(f'<figure class="dq"><blockquote class="desk">{esc(t)}</blockquote><figcaption>Issue {n}, <a href="{r}issues/{yy}/issue-{n:02d}/#{anc}">{esc(sec)}</a></figcaption></figure>' for n, yy, sec, anc, t in qs if str(yy) == y) or '<p class="key">The desk has not said anything about this manager yet. That is its own kind of insult.</p>'
            lead = "" if hero_season else f'<h3 class="sub">{"Final standing" if sd["closed"] else "Standing so far"}</h3><div class="mstats">{stat_tiles(sd)}</div>'
            extra = (f'{lead}<h3 class="sub" id="log{"" if hero_season else "-" + y}">Game log</h3>{log_table(sd["games"])}<h3 class="sub" id="tx{"" if hero_season else "-" + y}">Transactions</h3><div class="txl">{sd["tx_html"]}</div>'
                     f'<h3 class="sub" id="desk{"" if hero_season else "-" + y}">What the desk said</h3><div class="dqs">{qh}</div>')
        sm = f'{y} <small>{esc(sd["row"]["record"]) if sd else "archived"}</small>'
        blocks.append(f'<details class="ys"{" open" if y == ys[0] else ""}><summary>{sm}</summary><div class="yb"><h3 class="sub">The season</h3><div class="story">{story}</div>'
                      f'<h3 class="sub">The takes</h3>{tk or "<p class=key>No takes on file.</p>"}<h3 class="sub">The drama</h3>{dm or "<p class=key>No drama on file. Suspiciously quiet.</p>"}{extra}</div></details>')
    if hd:
        best = max(hd["games"], key=lambda g: g["points"]) if hd["games"] else None
        cap = f'<p class="key">{esc(last)} season{" (final)" if hd["closed"] else ""}.</p>' if (not active or len(mine_seasons) > 1 or hd["closed"]) else ""
        hero_stats = f'{form_strip(hd["games"])}{cap}<div class="mstats">{stat_tiles(hd)}</div>'
    else:
        hero_stats = '<p class="key">No finished games on file for this manager yet.</p>'
    nav = (f'<p class="mnav"><a class="btn o" href="{r}managers/{slug(names[ring - 1])}/">&larr; {esc(names[ring - 1])}</a><a class="btn o" href="{r}managers/{slug(names[(ring + 1) % len(names)])}/">{esc(names[(ring + 1) % len(names)])} &rarr;</a></p>'
           if ring is not None else "")
    df = bio.get("file") or []
    deskfile = ('<h2 class="sec" id="deskfile">The desk file</h2><div class="dfile">' + "".join(f'<div><small>{esc(a)}</small><p>{bs.bold_handles(b)}</p></div>' for a, b in df) + '</div>'
                ) if df else ""
    body = f'''<p class="crumb"><a href="../">All managers</a></p>
<section class="mhero"><div class="mid">{av(m, 120, r)}<div><h2>{esc(m)}</h2>{f'<p class="tn">{esc(team)}</p>' if team else ""}{former}{status}{f'<p class="tag">{esc(bio["tagline"])}</p>' if bio.get("tagline") else ""}</div></div>
{hero_stats}</section>
{trophy_case(m, r)}{deskfile}{portfolio_block(m, r)}<h2 class="sec" id="archive">The season archive</h2><div class="yrs">{"".join(blocks)}</div>
{nav}'''
    return shell(m, f"{m}: biography, record, transactions and desk quotes.", body, r, f"Manager file: {m}", f"managers/{slug(m)}/")

def blurb(t, n=120):
    t = t.strip()
    if len(t) <= n: return t
    return t[:n].rsplit(" ", 1)[0].rstrip(",;: ") + "..."

def market_board(prefix=""):
    """"The market" table for the home page: every portfolio ranked, with a collapsible legend. `prefix` is the path back to the site root."""
    teams = PORTFOLIO.get("teams")
    if not teams:
        return '<p class="key">Market values appear after the next data update.</p>'
    th = PORTFOLIO.get("thresholds") or {}
    ranked = sorted(teams, key=lambda m: teams[m]["rank"])
    hi = max(t["total"] for t in teams.values()); lo = min(t["total"] for t in teams.values()); span = (hi - lo) or 1
    rows = []
    for m in ranked:
        t = teams[m]; badge = STATUS[t["status"]][0]; w = 14 + 86 * (t["total"] - lo) / span
        rows.append(f'<tr><td class="rk">{t["rank"]}</td><td><a class="mn" href="{prefix}managers/{slug(m)}/#portfolio">{esc(m)}</a></td>'
                    f'<td><div class="vcell"><b>{t["total"]:,}</b><span class="vtrack"><i class="{t["status"]}" style="width:{w:.1f}%"></i></span></div></td>'
                    f'<td class="{"dn" if t["move30"] < 0 else "up"}">{t["move30_pct"]:+.1f}%</td><td>{t["sidelined_pct"]:.0f}%</td>'
                    f'<td><em class="st {t["status"]}">{badge}</em></td></tr>')
    crash, corr, bull = th.get("crash_move_pct", -5.0), th.get("correction_move_pct", -2.5), th.get("bull_move_pct", 5.0)
    side = th.get("crash_sidelined_pct", 25.0)
    def it(t, d): return f'<div><dt>{t}</dt><dd>{d}</dd></div>'
    legend = (f'<details class="legend wide"><summary>Legend: what the columns mean</summary>'
              f'<p>Every roster and pick, valued by <a href="https://www.fantasycalc.com">FantasyCalc</a> dynasty trade values. Updated {esc((PORTFOLIO.get("generated_at") or "")[:10])}.</p><dl>'
              + it("#", "Rank by portfolio value, highest first.")
              + it("Manager", "Click a name for that manager\'s portfolio.")
              + it("Portfolio value", "The combined value of every player and future pick the manager owns. The bar compares managers with each other (shortest to longest), not against zero.")
              + it("30d move", "How much the market moved the value of the players and picks held right now over the last 30 days. Trades do not change it.")
              + it("On IR", "The share of the portfolio value sitting on players who are on IR or listed Out, PUP, Doubtful or Suspended.")
              + it("Status", f'<b>Market crash</b>: the 30-day move is {crash:+g}% or worse, or {side:g}% or more of the value is on IR or out. <b>Correction</b>: down {abs(corr):g}% or more. <b>Bull run</b>: up {bull:g}% or more. <b>Stable</b>: anything else.')
              + '</dl></details>')
    return (f'<div class="tw2"><table class="mkt"><thead><tr><th>#</th><th>Manager</th><th>Portfolio value</th><th>30d move</th><th>On IR</th><th>Status</th></tr></thead>'
            f'<tbody>{"".join(rows)}</tbody></table></div>{legend}')

def hub(rows, quotes, moves, active, alumni):
    """rows: the display season's standings. alumni: [(manager, last season)] for people with no row in it."""
    total = len(rows); teams = lambda m: (bs.managers().get(m) or {}).get("team_name")
    def card(r, badge=None, year=None):
        m, k = r["manager"], r["rank"]
        badge = badge or (f'<img src="../assets/trophy-{["gold", "silver", "bronze"][k - 1]}-sm.webp" alt="#{k}" width="24" height="44">' if k <= 3
                 else '<img src="../assets/trophy-trash-sm.webp" alt="#%d" width="26" height="44">' % k if k >= total - 1 else f'<b>#{k}</b>')
        tl = (jload(f'data/bios/{m}.json', {}) or {}).get('tagline'); q = f'<q>{esc(tl)}</q>' if tl else f'<q>{esc(blurb(quotes[m]))}</q>' if quotes.get(m) else '<q class="none">The desk has nothing on file yet.</q>'
        stat = lambda a, b: f'<span><small>{a}</small><b>{b}</b></span>'
        tn = " &middot; ".join(p for p in (esc(teams(m)) if teams(m) else "", ("Alumni" + (f" ({year})" if year else "")) if not active.get(m, True) else "") if p)
        return (f'<a class="mc2" href="{slug(m)}/"><div class="mtop">{av(m, 72, "../")}<div class="mn"><h3>{esc(m)}</h3><p class="mt">{tn}</p></div><span class="rk">{badge}</span></div>'
                f'<div class="mrow">{stat("Record", esc(r["record"]))}{stat("PF", format(r["pf"], ".1f"))}{stat("FAAB", "$" + str(r["faab_remaining"]))}{stat("Moves", moves.get(m, 0))}</div>{q}<span class="open">Open file</span></a>')
    groups = [("The podium", "Top three right now.", [card(r) for r in rows[:3]]), ("The middle", "Everyone still arguing about the playoffs.", [card(r) for r in rows[3:-2]]), ("The danger zone", "Bottom two. Draft position is the consolation.", [card(r) for r in rows[-2:]])]
    if alumni:
        groups.append(("Alumni", "No longer in the league. The files stay.", [card(r, f"<b>{y}</b>", y) for r, y in alumni]))
    body = "".join(
        f'<h2 class="sec">{t}</h2><p class="key">{d}</p><div class="mgrid">{"".join(g)}</div>' for t, d, g in groups if g)
    return shell("Managers", "Every manager in the Dynastree league.", body, "../", "The league files", "managers/")

if __name__ == "__main__":
    display = bs.display_season(); bs.use(display)
    TROPHY_CASE.update(load_trophy_case()); bs.use(display)
    PORTFOLIO.update(jload(f"data/{display}/portfolio.json", {}) or {})
    bs.inject("index.html", "MARKET", market_board())   # home page section between Transactions and Rules
    rows = jload(bs.S("standings.json"), []) or []
    years = {i["no"]: i["year"] for i in bs.manifest()}
    everyone = sorted({*bs.managers(), *(r["manager"] for r in rows)}, key=str.lower)
    # anyone who appears in ANY season's standings also gets a page, even if managers.json never knew them
    for s_ in sorted(REG):
        bs.use(s_)
        everyone = sorted({*everyone, *(r["manager"] for r in (jload(bs.S("standings.json"), []) or []))}, key=str.lower)
    bs.use(display)
    dnames = {r["manager"] for r in rows}
    active = {m: is_active(m, dnames) for m in everyone}
    ring = [m for m in everyone if active[m]]
    top, moves = {}, {}
    def write(p, html):
        p = os.path.join(ROOT, p); os.makedirs(os.path.dirname(p), exist_ok=True); open(p, "w", encoding="utf-8").write(html)
    for m in everyone:
        q = desk_quotes(m, years); top[m] = q[0][4] if q else ""
        write(f"managers/{slug(m)}/index.html", manager_page(m, ring, years, display, active[m]))
        d = sdata(m, display)
        if d: moves[m] = d["ntx"]
    bs.use(display)
    alumni = []
    for m in everyone:
        if m in dnames: continue
        ms = seasons_of(m)
        if ms: alumni.append((sdata(m, ms[-1])["row"], ms[-1]))
    for old, new in bs.alias().items():   # old links keep working after a rename
        write(f"managers/{slug(old)}/index.html", f'<!doctype html><meta charset="utf-8"><meta http-equiv="refresh" content="0;url=../{slug(new)}/"><link rel="canonical" href="../{slug(new)}/"><a href="../{slug(new)}/">Moved to {esc(new)}</a>')
    bs.use(display)
    write("managers/index.html", hub(rows, top, moves, active, alumni)); print(f"built {len(everyone)} manager pages ({len(ring)} active)")
