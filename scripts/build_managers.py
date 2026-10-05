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
    for f in sorted(glob.glob(os.path.join(ROOT, "data/issues/issue-*.json")), reverse=True):
        n = int(re.search(r"issue-(\d+)", f).group(1)); d = bs.canon(json.load(open(f, encoding="utf-8")))
        add = lambda sec, anc, t: t and out.append((n, years.get(n, 2026), sec, anc, t))
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

def manager_page(m, row, eff, games, names, years, thru):
    r = "../../"; i = names.index(m); prev, nxt = names[i - 1], names[(i + 1) % len(names)]
    info = (bs.managers().get(m) or {}); team = info.get("team_name")
    former = ('<p class="key">Formerly ' + esc(", ".join(info["former_names"])) + "</p>") if info.get("former_names") else ""
    tx_html, ntx, spent = tx_block(m, thru); qs = desk_quotes(m, years)
    best = max(games, key=lambda g: g["points"]) if games else None
    stats = [("Record", row["record"]), ("Rank", f'#{row["rank"]}'), ("Points for", f'{row["pf"]:.1f}'), ("Points against", f'{row["pa"]:.1f}'),
             ("MAXPF", f'{row["maxpf"]:.1f}'), ("Efficiency", f'{eff["efficiency"]}%' if eff else "n/a"), ("Draft slot", f'1.{row["draft_pick"]:02d}'),
             ("FAAB left", f'${row["faab_remaining"]}'), ("Moves", str(ntx))]
    tiles = "".join(f'<div><small>{a}</small><b>{b}</b></div>' for a, b in stats)
    qh = "".join(f'<figure class="dq"><blockquote class="desk">{esc(t)}</blockquote><figcaption>Issue {n}, <a href="{r}issues/{y}/issue-{n:02d}/#{anc}">{esc(sec)}</a></figcaption></figure>' for n, y, sec, anc, t in qs) or '<p class="key">The desk has not said anything about this manager yet. That is its own kind of insult.</p>'
    body = f'''<p class="crumb"><a href="../">All managers</a></p>
<section class="mhero"><div class="mid">{av(m, 120, r)}<div><h2>{esc(m)}</h2><p class="tn">{esc(team) if team else "Team name pending. The desk has questions."}</p>{former}</div></div>
{form_strip(games)}<div class="mstats">{tiles}</div>
{f'<p class="key">Best week: {best["points"]:.2f} in Week {best["week"]}. Spent ${spent} on the wire.</p>' if best else ""}</section>
<h2 class="sec" id="log">Game log</h2>{log_table(games)}
<h2 class="sec" id="tx">Transactions</h2><div class="txl">{tx_html}</div>
<h2 class="sec" id="desk">What the desk said</h2><div class="dqs">{qh}</div>
<p class="mnav"><a class="btn o" href="{r}managers/{slug(prev)}/">&larr; {esc(prev)}</a><a class="btn o" href="{r}managers/{slug(nxt)}/">{esc(nxt)} &rarr;</a></p>'''
    return shell(m, f"{m}'s record, transactions and desk quotes.", body, r, f"Manager file: {m}")

def hub(rows, quotes):
    cards = "".join(f'<a class="mc2" href="{slug(r["manager"])}/">{av(r["manager"], 64, "../")}<div><h3>{esc(r["manager"])}</h3><p>#{r["rank"]} &middot; {esc(r["record"])} &middot; {r["pf"]:.1f} PF</p>'
                    f'{f"<q>{esc(quotes[r["manager"]][:110].rstrip())}...</q>" if quotes.get(r["manager"]) else ""}</div></a>' for r in rows)
    return shell("Managers", "Every manager in the Dynastree league.", f'<h2 class="sec">The managers</h2><p class="key">Sorted by current standings. Every file has the record, the receipts and what the desk had to say.</p><div class="mgrid">{cards}</div>', "../", "The league files")

if __name__ == "__main__":
    rows = jload("data/standings.json", []); eff = {e["manager"]: e for e in jload("data/efficiency.json", [])}
    thru = max((jload("data/league.json", {}) or {}).get("weeks_with_scores", [1])); names = sorted((r["manager"] for r in rows), key=str.lower)
    years = {i["no"]: i["year"] for i in bs.manifest()}; top = {}
    def write(p, html):
        p = os.path.join(ROOT, p); os.makedirs(os.path.dirname(p), exist_ok=True); open(p, "w", encoding="utf-8").write(html)
    for r in rows:
        m = r["manager"]; q = desk_quotes(m, years); top[m] = q[0][4] if q else ""
        write(f"managers/{slug(m)}/index.html", manager_page(m, r, eff.get(m), games_for(m, thru), names, years, thru))
    for old, new in bs.alias().items():   # old links keep working after a rename
        write(f"managers/{slug(old)}/index.html", f'<!doctype html><meta charset="utf-8"><meta http-equiv="refresh" content="0;url=../{slug(new)}/"><link rel="canonical" href="../{slug(new)}/"><a href="../{slug(new)}/">Moved to {esc(new)}</a>')
    write("managers/index.html", hub(rows, top)); print(f"built {len(rows)} manager pages")
