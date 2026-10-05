#!/usr/bin/env python3
"""Manager pages: managers/index.html (the league hub) + managers/<handle>/index.html (one per manager).
Everything numeric comes from data/ (same sources as build_site.py); desk quotes are mined from data/issues/*.json.
Run after build_site.py:  python scripts/build_managers.py"""
import glob, json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import build_site as bs
from build_site import esc, av, jload, ROOT

slug = lambda m: m.lower()
FONTS = '<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Oswald:wght@500;600;700&display=swap" rel="stylesheet">'

def shell(title, desc, body, r, sub):
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)} | Dynastree Chronicles</title><meta name="description" content="{esc(desc)}"><meta name="robots" content="noindex">
{FONTS}<link rel="stylesheet" href="{r}css/dynastree.css"><link rel="stylesheet" href="{r}css/managers.css">
<link rel="icon" type="image/png" sizes="32x32" href="{r}assets/favicon-32.png"><link rel="apple-touch-icon" href="{r}assets/apple-touch-icon.png"></head><body>
<header class="mast"><div class="wrap"><img src="{r}assets/crest-mark.webp" alt="Dynastree Chronicles crest" width="79" height="96"><div><h1><a href="{r}">Dynastree <span>Chronicles</span></a></h1><p>{esc(sub)}</p></div></div></header>
<nav class="sticky"><div class="wrap"><a href="{r}#archive">Issues</a><a href="{r}#standings">Standings</a><a href="{r}managers/">Managers</a><a href="{r}#transactions">Transactions</a><a href="{r}#rules">Rules</a></div></nav>
<main class="wrap">{body}</main>
<footer><div class="wrap"><img class="tree" src="{r}assets/tree.webp" alt="" width="40"><p>Time heals all wounds, but screenshots last forever.</p></div></footer></body></html>'''

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

def season_line(m, row, eff, games, rank_pf, spent, ntx, ntr):
    best = max(games, key=lambda g: g["points"]); low = min(games, key=lambda g: g["points"])
    s = (f'{m} is {bs.ordinal(row["rank"])} at {row["record"]} with {row["pf"]:.1f} points, {bs.ordinal(rank_pf)} in the league in scoring. '
         f'The high was {best["points"]:.2f} in Week {best["week"]} and the low {low["points"]:.2f} in Week {low["week"]}. '
         f'{ntx} transactions so far ({ntr} trade{"" if ntr == 1 else "s"}), ${spent} spent on the wire, ${row["faab_remaining"]} left, and the rookie pick sits at 1.{row["draft_pick"]:02d}.')
    return s + (f' Lineup efficiency: {eff["efficiency"]}%.' if eff else "")

def takes_html(items, r):
    out = []
    for k, n, a, b in items:
        if k == "chat": out.append(f'<figure class="tk"><blockquote>&ldquo;{esc(a)}&rdquo;</blockquote><figcaption>Issue {n}: {esc(b)}</figcaption></figure>')
        else: out.append(f'<p class="call"><b>Issue {n} prediction.</b> {esc(a.rstrip("."))}: {esc(b)}</p>')
    return "".join(out)

def drama_html(items):
    return "".join(f'<article class="dm"><span class="hd" style="--c:hsl({max(0, 214 - int(h * 2.14))} 94% 56%)"><b>{h}</b>&deg;F</span><div><h4>{esc(t)}</h4><p>{esc(p)}</p>' + (f'<p class="desk">{esc(d)}</p>' if d else "") + f'<small>Issue {n}</small></div></article>' for n, h, t, p, d in items)

def manager_page(m, row, eff, games, names, years, thru, rows, season):
    r = "../../"; i = names.index(m); prev, nxt = names[i - 1], names[(i + 1) % len(names)]
    info = (bs.managers().get(m) or {}); team = info.get("team_name"); bio = jload(f"data/bios/{m}.json", {}) or {}
    former = ('<p class="key">Formerly ' + esc(", ".join(info["former_names"])) + "</p>") if info.get("former_names") else ""
    tx_html, ntx, spent = tx_block(m, thru); qs = desk_quotes(m, years); mined = mine(m, years, season)
    ntr = sum(1 for t in bs.txfeed() if t["type"] == "trade" and any(x["manager"] == m for x in t["sides"]))
    rank_pf = 1 + sum(1 for x in rows if x["pf"] > row["pf"])
    stats = [("Record", row["record"]), ("Rank", f'#{row["rank"]}'), ("Points for", f'{row["pf"]:.1f}'), ("Points against", f'{row["pa"]:.1f}'),
             ("MAXPF", f'{row["maxpf"]:.1f}'), ("Efficiency", f'{eff["efficiency"]}%' if eff else "n/a"), ("Draft slot", f'1.{row["draft_pick"]:02d}'),
             ("FAAB left", f'${row["faab_remaining"]}'), ("Moves", str(ntx))]
    tiles = "".join(f'<div><small>{a}</small><b>{b}</b></div>' for a, b in stats)
    qh = "".join(f'<figure class="dq"><blockquote class="desk">{esc(t)}</blockquote><figcaption>Issue {n}, <a href="{r}issues/{y}/issue-{n:02d}/#{anc}">{esc(sec)}</a></figcaption></figure>' for n, y, sec, anc, t in qs) or '<p class="key">The desk has not said anything about this manager yet. That is its own kind of insult.</p>'
    seasons = bio.get("seasons") or {}; ys = sorted({str(season), *map(str, seasons), *map(str, mined)}, reverse=True); blocks = []
    for y in ys:
        cur = y == str(season); bs_ = seasons.get(y, {}); mi = mined.get(int(y), {"takes": [], "drama": []}) if y.isdigit() else {"takes": [], "drama": []}
        paras = ([season_line(m, row, eff, games, rank_pf, spent, ntx, ntr)] if cur and games else []) + bs_.get("story", [])
        fin = bs_.get("final") or {}
        head = f'<h3 class="hl">{esc(bs_["headline"])}</h3>' if bs_.get("headline") else ""
        asof = f'<p class="key">Desk bio, written after {esc(bs_["asof"])}. The season line above updates itself.</p>' if bs_.get("asof") else ""
        fin_h = asof + (f'<p class="key">Final: {esc(fin.get("record", ""))}, finished {esc(str(fin.get("rank", "")))}. {esc(fin.get("note", ""))}</p>' if fin else "")
        story = head + "".join(f"<p>{bs.bold_handles(x)}</p>" for x in paras) + fin_h or '<p class="key">No story filed for this season yet.</p>'
        tk = takes_html(mi["takes"], r) + "".join(f'<figure class="tk"><blockquote>{esc(x)}</blockquote></figure>' for x in bs_.get("takes", []))
        dm = drama_html(mi["drama"]) + "".join(f'<article class="dm"><div><p>{esc(x)}</p></div></article>' for x in bs_.get("drama", []))
        extra = (f'<h3 class="sub" id="log">Game log</h3>{log_table(games)}<h3 class="sub" id="tx">Transactions</h3><div class="txl">{tx_html}</div>'
                 f'<h3 class="sub" id="desk">What the desk said</h3><div class="dqs">{qh}</div>') if cur else ""
        sm = f'{y} <small>{esc(row["record"]) if cur else esc(fin.get("record", "archived"))}</small>'
        blocks.append(f'<details class="ys"{" open" if cur else ""}><summary>{sm}</summary><div class="yb"><h3 class="sub">The season</h3><div class="story">{story}</div>'
                      f'<h3 class="sub">The takes</h3>{tk or "<p class=key>No takes on file.</p>"}<h3 class="sub">The drama</h3>{dm or "<p class=key>No drama on file. Suspiciously quiet.</p>"}{extra}</div></details>')
    best = max(games, key=lambda g: g["points"]) if games else None
    body = f'''<p class="crumb"><a href="../">All managers</a></p>
<section class="mhero"><div class="mid">{av(m, 120, r)}<div><h2>{esc(m)}</h2><p class="tn">{esc(team) if team else "Team name pending. The desk has questions."}</p>{former}{f'<p class="tag">{esc(bio["tagline"])}</p>' if bio.get("tagline") else ""}</div></div>
{form_strip(games)}<div class="mstats">{tiles}</div>
{f'<p class="key">Best week: {best["points"]:.2f} in Week {best["week"]}. Spent ${spent} on the wire.</p>' if best else ""}</section>
<h2 class="sec" id="archive">The season archive</h2><p class="key">One folder per season. New years appear here automatically.</p><div class="yrs">{"".join(blocks)}</div>
<p class="mnav"><a class="btn o" href="{r}managers/{slug(prev)}/">&larr; {esc(prev)}</a><a class="btn o" href="{r}managers/{slug(nxt)}/">{esc(nxt)} &rarr;</a></p>'''
    return shell(m, f"{m}: biography, record, transactions and desk quotes.", body, r, f"Manager file: {m}")

def blurb(t, n=120):
    t = t.strip()
    if len(t) <= n: return t
    return t[:n].rsplit(" ", 1)[0].rstrip(",;: ") + "..."

def hub(rows, quotes, moves):
    total = len(rows); teams = lambda m: (bs.managers().get(m) or {}).get("team_name")
    def card(r):
        m, k = r["manager"], r["rank"]
        badge = (f'<img src="../assets/trophy-{["gold", "silver", "bronze"][k - 1]}-sm.webp" alt="#{k}" width="24" height="44">' if k <= 3
                 else '<img src="../assets/trophy-trash-sm.webp" alt="#%d" width="26" height="44">' % k if k >= total - 1 else f'<b>#{k}</b>')
        tl = (jload(f'data/bios/{m}.json', {}) or {}).get('tagline'); q = f'<q>{esc(tl)}</q>' if tl else f'<q>{esc(blurb(quotes[m]))}</q>' if quotes.get(m) else '<q class="none">The desk has nothing on file yet.</q>'
        stat = lambda a, b: f'<span><small>{a}</small><b>{b}</b></span>'
        return (f'<a class="mc2" href="{slug(m)}/"><div class="mtop">{av(m, 72, "../")}<div class="mn"><h3>{esc(m)}</h3><p class="mt">{esc(teams(m)) if teams(m) else "Team name pending"}</p></div><span class="rk">{badge}</span></div>'
                f'<div class="mrow">{stat("Record", esc(r["record"]))}{stat("PF", f"{r[chr(112)+chr(102)]:.1f}")}{stat("FAAB", "$" + str(r["faab_remaining"]))}{stat("Moves", moves.get(m, 0))}</div>{q}<span class="open">Open file</span></a>')
    groups = [("The podium", "Top three right now.", rows[:3]), ("The middle", "Everyone still arguing about the playoffs.", rows[3:-2]), ("The danger zone", "Bottom two. Draft position is the consolation.", rows[-2:])]
    body = '<p class="key">Click a manager for their record, game log, every transaction and everything the desk has said about them.</p>' + "".join(
        f'<h2 class="sec">{t}</h2><p class="key">{d}</p><div class="mgrid">{"".join(card(r) for r in g)}</div>' for t, d, g in groups if g)
    return shell("Managers", "Every manager in the Dynastree league.", body, "../", "The league files")

if __name__ == "__main__":
    season = bs.display_season(); bs.use(season)   # the manager pages show the newest season with finished weeks
    rows = jload(bs.S("standings.json"), []); eff = {e["manager"]: e for e in jload(bs.S("efficiency.json"), [])}
    thru = max((jload(bs.S("league.json"), {}) or {}).get("weeks_with_scores", [1])); names = sorted((r["manager"] for r in rows), key=str.lower)
    years = {i["no"]: i["year"] for i in bs.manifest()}; top = {}
    moves = {}
    for t in bs.txfeed():
        for who in ([x["manager"] for x in t["sides"]] if t["type"] == "trade" else [t.get("manager")]):
            moves[who] = moves.get(who, 0) + 1
    def write(p, html):
        p = os.path.join(ROOT, p); os.makedirs(os.path.dirname(p), exist_ok=True); open(p, "w", encoding="utf-8").write(html)
    for r in rows:
        m = r["manager"]; q = desk_quotes(m, years); top[m] = q[0][4] if q else ""
        write(f"managers/{slug(m)}/index.html", manager_page(m, r, eff.get(m), games_for(m, thru), names, years, thru, rows, season))
    for old, new in bs.alias().items():   # old links keep working after a rename
        write(f"managers/{slug(old)}/index.html", f'<!doctype html><meta charset="utf-8"><meta http-equiv="refresh" content="0;url=../{slug(new)}/"><link rel="canonical" href="../{slug(new)}/"><a href="../{slug(new)}/">Moved to {esc(new)}</a>')
    write("managers/index.html", hub(rows, top, moves)); print(f"built {len(rows)} manager pages")
