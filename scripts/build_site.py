#!/usr/bin/env python3
"""Bake data into the HTML so pages never depend on a fetch() succeeding.
  - index.html: renders the standings table from data/standings.json
  - issues/2026/issue-04/index.html: embeds data/issues/issue-04.json
Run after sleeper_pull.py (the GitHub Action does this)."""
import json, os, re
ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
esc = lambda s: str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def inject(path, tag, html):
    p = os.path.join(ROOT, path)
    s = open(p, encoding="utf-8").read()
    pat = re.compile(rf"<!--{tag}-->.*?<!--/{tag}-->", re.S)
    assert pat.search(s), f"markers {tag} missing in {path}"
    open(p, "w", encoding="utf-8").write(pat.sub(lambda m: f"<!--{tag}-->\n{html}\n<!--/{tag}-->", s))

_MG = None

def managers():
    global _MG
    if _MG is None:
        p = os.path.join(ROOT, "data/managers.json")
        _MG = json.load(open(p, encoding="utf-8")) if os.path.exists(p) else {}
    return _MG

def initials(name):
    p = re.findall(r"[A-Z][a-z]+|[A-Z]+(?![a-z])|[a-z]+", name)
    return (p[0][0] + p[1][0] if len(p) > 1 else name[:2]).upper()

def av(name, size=28, root=""):
    """Avatar circle: the manager's image if we have one, otherwise coloured initials."""
    m = managers().get(name, {})
    h = sum(map(ord, name)) % 360
    inner = f'<img src="{root}{m["avatar"]}" alt="" loading="lazy" width="{size}" height="{size}">' if m.get("avatar") else esc(initials(name))
    return f'<span class="av" style="--s:{size}px;--h:{h}">{inner}</span>'

def prev_picks(fin):
    """Draft slot as of the previous final week (lowest MAXPF = 1.01), from data/weeks."""
    tot = {}
    for w in range(1, fin):
        p = os.path.join(ROOT, f"data/weeks/week-{w:02d}.json")
        if not os.path.exists(p):
            return {}
        for t in json.load(open(p, encoding="utf-8"))["teams"]:
            tot[t["roster_id"]] = tot.get(t["roster_id"], 0) + t["maxpf"]
    return {r: i + 1 for i, r in enumerate(sorted(tot, key=lambda r: tot[r]))}

def mv(m):
    return f'<span class="up">&#9650; {m}</span>' if m > 0 else f'<span class="dn">&#9660; {-m}</span>' if m < 0 else '<span class="flat">&mdash;</span>'


def legend(kind):
    """Collapsed 'how to read this' glossary shared by the home and issue standings."""
    up, dn = '<span class="up">&#9650;</span>', '<span class="dn">&#9660;</span>'
    rows = {
        "rank": [("Table", [("W-L", "<b>Record</b> through the latest finished week."),
                            ("MOV", f"<b>Movement</b> in the standings since last week. {up} 2 = climbed two spots, {dn} 2 = dropped two, &mdash; = no change."),
                            ("PF", "<b>Points for.</b> Total points your team has scored this season."),
                            ("FAAB", "<b>Waiver budget</b> left, out of $500.")])],
        "draft": [("Table", [("Pick", "<b>2027 rookie draft slot.</b> 1.01 is the first overall pick."),
                             ("FUT CAP", "<b>Future capital.</b> Points for owned picks: Early 1st 100, Mid-Late 1st 75, 2nd-year 1st 60, 3rd-year 1st 50, any 2nd 30, any 3rd 10."),
                             ("MAXPF", "<b>Total roster points</b> (starters and bench). The lowest total gets pick 1.01."),
                             ("MOV", f"<b>Pick movement</b> since last week. {up} = pick moved earlier (closer to 1.01), {dn} = moved later."),
                             ("FAAB", "<b>Waiver budget</b> left, out of $500.")])],
    }
    if kind == "issue":
        rows = {"issue": [("Standings", [("W-L", "<b>Record</b> through Week 3."),
                                         ("MOV", f"<b>Movement</b> in the standings since last week. {up} 2 = climbed two spots, {dn} 2 = dropped two, &mdash; = no change."),
                                         ("PF / PA", "<b>Points for / against.</b> Scored by you / scored on you."),
                                         ("FAAB", "<b>Waiver budget</b> left, out of $500."),
                                         ("PRI", "<b>Waiver priority.</b> Lower number claims first."),
                                         ("MAXPF", "<b>Total roster points</b> (starters and bench). Lowest gets 1.01."),
                                         ("DRFT", "<b>2027 draft slot</b> from MAXPF.")])]}
    items = [it for v in rows.values() for _, g in v for it in g]
    out = "".join(f"<div><dt>{t}</dt><dd>{d}</dd></div>" for t, d in items)
    return f'<details class="legend"><summary>How to read this table</summary><dl>{out}</dl></details>'

def standings():
    rows = json.load(open(os.path.join(ROOT, "data/standings.json")))
    fin = rows and max(r["wins"] + r["losses"] + r["ties"] for r in rows)
    pp = prev_picks(fin)
    p = os.path.join(ROOT, "data/fut_cap.json")
    fc = json.load(open(p, encoding="utf-8")) if os.path.exists(p) else {}
    team = lambda r: f'<td>{av(r["manager"], 24)}<b>{esc(r["manager"])}</b></td>'
    troph = lambda r: (f'<img class="rkt" src="assets/trophy-{["gold", "silver", "bronze"][r["rank"] - 1]}-sm.webp" alt="" width="24" height="44">' if r["rank"] <= 3 else '<img class="rkt" src="assets/trophy-trash-sm.webp" alt="" width="26" height="44">' if r["rank"] == len(rows) else "")
    rk = "".join(f'<tr><td class="n">{troph(r)}{r["rank"]}</td>{team(r)}<td class="n">{esc(r["record"])}</td><td class="n mv">{mv(r.get("move", 0))}</td><td class="n">{r["pf"]:.2f}</td><td class="n">${r["faab_remaining"]}</td></tr>' for r in rows)
    dr = ""
    for r in sorted(rows, key=lambda r: r["draft_pick"]):
        f = fc.get(r["manager"])
        dr += (f'<tr><td class="n pick">1.{r["draft_pick"]:02d}</td>{team(r)}<td class="n">{"&mdash;" if f is None else f}</td>'
               f'<td class="n">{r["maxpf"]:.2f}</td><td class="n mv">{mv(pp.get(r["roster_id"], r["draft_pick"]) - r["draft_pick"])}</td><td class="n">${r["faab_remaining"]}</td></tr>')
    h = lambda cols: "<tr>" + "".join(f'<th{" class=\"n\"" if i else ""}>{c}</th>' if c != "Team" else "<th>Team</th>" for i, c in enumerate(cols)) + "</tr>"
    return (f'<div class="sortbar" role="group" aria-label="Standings view"><button class="chip on" data-view="rank">Standings order</button><button class="chip" data-view="draft">Draft order</button></div>'
            f'<div class="sc" id="v-rank"><table id="standtable"><thead>{h(["#", "Team", "W-L", "MOV", "PF", "FAAB"])}</thead><tbody>{rk}</tbody></table>'
            f'<p class="key">Through Week {fin} finals. MOV = change in standings spots since the previous week. FAAB is the current balance.</p>{legend("rank")}</div>'
            f'<div class="sc" id="v-draft" hidden><table id="drafttable"><thead>{h(["Pick", "Team", "FUT CAP", "MAXPF", "MOV", "FAAB"])}</thead><tbody>{dr}</tbody></table>'
            f'<p class="key">2027 rookie draft order: lowest MAXPF picks 1.01. MOV = spots gained or lost in the pick since the previous week. '
            f'FUT CAP is future capital as scored in the Issue 4 power rankings: Early 1st 100, Mid-Late 1st 75, 2nd-year 1st 60, 3rd-year 1st 50, any 2nd 30, any 3rd 10.</p>{legend("draft")}</div>')

def issue(n="04", y=2026):
    d = open(os.path.join(ROOT, f"data/issues/issue-{n}.json"), encoding="utf-8").read()
    d = json.loads(d)
    wk = next((x.get("wire_week") for x in manifest() if x["no"] == int(n)), None)
    if wk:
        d["wire"]["waivers"] = enrich(d["wire"]["waivers"], wk)
    d = json.dumps(d, ensure_ascii=False).replace("</", "<\\/")
    inject(f"issues/{y}/issue-{n}/index.html", "ISSUE-DATA", f'<script id="issue-data" type="application/json">{d}</script>')
    inject(f"issues/{y}/issue-{n}/index.html", "MANAGERS", '<script id="managers-data" type="application/json">' + json.dumps(managers(), ensure_ascii=False).replace("</", "<\\/") + "</script>")

def leaderboard():
    rows = json.load(open(os.path.join(ROOT, "data/standings.json")))
    img = lambda k, c: f'<img class="tro {c}" src="assets/trophy-{k}.webp" alt="" width="132" height="240" loading="lazy">'
    card = lambda r, c, tag, k: f'<div class="{c}">{img(k, "t" + c[-1] if c[0] == "p" else "tt")}<div class="ti"><small>{tag}</small><b class="rk">#{r["rank"]}</b><h3>{av(r["manager"], 32)}{esc(r["manager"])}</h3><p>{esc(r["record"])} &middot; {r["pf"]:.1f} PF</p></div></div>'
    top = "".join(card(r, f"p{i}", t, k) for i, (r, t, k) in enumerate(zip(rows[:3], ("Gold", "Silver", "Bronze"), ("gold", "silver", "bronze")), 1))
    low = "".join(card(r, "lo", "Bottom", "trash") for r in rows[-2:])
    return (f'<div class="lbx"><div class="podium">{top}</div><div class="dz"><h3 class="dzh">The Danger Zone</h3><div class="dzg">{low}</div></div></div>'
            '<p class="key"><a href="#standings">Full standings below</a></p>')

def ordinal(n):
    return {1: "1st", 2: "2nd", 3: "3rd"}.get(n, f"{n}th")

_TX = None

def txfeed():
    global _TX
    if _TX is None:
        _TX = json.load(open(os.path.join(ROOT, "data/transactions.json"), encoding="utf-8"))
    return _TX

def _k(name, pos=""):
    """Match key so 'Bengals D/ST' and 'Cincinnati Bengals' (DEF) line up."""
    if name.endswith("D/ST"):
        return "DEF:" + name.replace("D/ST", "").split()[-1].lower()
    return ("DEF:" + name.split()[-1].lower()) if pos == "DEF" else name.lower()

def enrich(waivers, week):
    """Fill position and FAAB bid from the Sleeper feed where the hand-written issue data lacks them."""
    feed = {(t["manager"], _k(t["added"]["name"], t["added"].get("pos", ""))): t for t in txfeed() if t["week"] == week and t["type"] != "trade"}
    out = []
    for x in waivers:
        x = list(x) + [""] * (6 - len(x))
        t = feed.get((x[0], _k(x[1])))
        x.append(t["added"].get("pos", "") if t else "")
        if t and not x[2]:
            x[2] = t.get("bid") or 0
        out.append(x)
    return out

LABEL = {"mvp": "Waiver Wire MVP", "fav": "Desk Favorite", "note": "Desk note"}

def move_html(x, root=""):
    """One waiver claim (add + optional drop), highlighted when the desk flagged it."""
    pos = f'<em>{esc(x[6])}</em>' if len(x) > 6 and x[6] else ""
    bid = f'<small>${x[2]}</small>' if x[2] else "<span></span>"
    rows = f'<div class="txr"><span class="tg add">+ ADD</span><span class="pn">{esc(x[1])}{pos}</span>{bid}</div>'
    if x[3]:
        rows += f'<div class="txr"><span class="tg drop">&minus; DROP</span><span class="pn">{esc(x[3])}</span><span></span></div>'
    if x[4] not in LABEL:
        return rows
    badge = f'<img src="{root}assets/badge-{"mvp" if x[4] == "mvp" else "desk"}.webp" alt="" width="34" height="34">' if x[4] != "note" else ""
    note = f'<p>{esc(x[5])}</p>' if x[5] else ""
    return f'<div class="hlw {x[4]}">{rows}<div class="txn">{badge}<div><b class="lab">{LABEL[x[4]]}</b>{note}</div></div></div>'

def transactions(m):
    i = next((x for x in m if x.get("web")), None)
    if not i:
        return ""
    fin = i.get("wire_week") or 1
    d = json.load(open(os.path.join(ROOT, f"data/issues/issue-{i['no']:02d}.json"), encoding="utf-8"))
    ws = enrich(d["wire"]["waivers"], fin)
    notable = lambda x: x[4] in ("mvp", "fav") or x[2] >= 50
    out = [f'<h3 class="wk">Week {fin} highlights</h3>']
    for t in (x for x in txfeed() if x["week"] == fin and x["type"] == "trade"):
        def gets(s):
            items = [p["name"] for p in s["receives_players"]] + [f'{p["season"]} {ordinal(int(p["round"]))}' for p in s["receives_picks"]] + ([f'${s["receives_faab"]} FAAB'] if s.get("receives_faab") else [])
            return f'{esc(s["manager"])} gets {esc(", ".join(items) or "nothing")}'
        out.append('<div class="tx trade"><span class="tg trade">&#129309; TRADE</span><div class="tb"><b>' + " &harr; ".join(esc(s["manager"]) for s in t["sides"]) + "</b><small>" + " &middot; ".join(gets(s) for s in t["sides"]) + "</small></div></div>")
    order = []
    for x in ws:
        if x[0] not in order:
            order.append(x[0])
    rank = lambda mg: min((0 if x[4] == "mvp" else 1 if x[4] == "fav" else 2 for x in ws if x[0] == mg and notable(x)), default=9)
    cards = []
    for mg in sorted((o for o in order if rank(o) < 9), key=rank):
        allm = [x for x in ws if x[0] == mg]
        keep = [x for x in allm if notable(x)]
        cards.append(f'<div class="txg"><div class="txh">{av(mg, 28)}<b>{esc(mg)}</b><small>{len(keep)} of {len(allm)} moves</small></div>' + "".join(move_html(x) for x in keep) + "</div>")
    out.append('<div class="txgrid">' + "".join(cards) + "</div>")
    link = f'issues/{i["year"]}/issue-{i["no"]:02d}/#wire'
    return '<div class="txl">' + "".join(out) + f'</div><p class="key">Showing the desk\'s picks and big FAAB spends. <a class="btn o" href="{link}">See all {len(ws)} waiver moves and trade grades in Issue {i["no"]}</a></p>'

def rules():
    from collections import Counter
    c = Counter(json.load(open(os.path.join(ROOT, "data/league.json")))["roster_positions"])
    nm = {"SUPER_FLEX": "SFLEX", "BN": "Bench"}
    lineup = ", ".join((f"{n}&times;" if n > 1 else "") + nm.get(p, p) for p, n in c.items())
    cards = [("Roster", lineup), ("Rookie draft", "2027 order by MAXPF, linear. Lowest MAXPF picks 1.01."), ("Trades", "Vetoes are on."), ("Payouts", "The playoff winner collects.")]
    return '<div class="rl">' + "".join(f"<div><h3>{a}</h3><p>{b}</p></div>" for a, b in cards) + "</div>"

def manifest():
    return sorted(json.load(open(os.path.join(ROOT, "data/issues.json"), encoding="utf-8")), key=lambda i: -i["no"])

def link(i):
    return f'issues/{i["year"]}/issue-{i["no"]:02d}/' if i.get("web") else i["pdf"]

def home_blocks(m):
    i = m[0]
    inject("index.html", "TICKER", "".join(f"<span>{esc(x)}</span>" for x in i.get("ticker", [])))
    inject("index.html", "BANNER", f'<a class="banner" href="{link(i)}"><small>Latest &middot; Issue {i["no"]}</small><h2>{esc(i.get("banner", i.get("title", "")))}</h2><span class="btn">{"Read" if i.get("web") else "Download"} Issue {i["no"]}</span></a>')
    read = f'<a class="btn" href="{link(i)}">Read Issue {i["no"]}</a>' if i.get("web") else ""
    inject("index.html", "HERO", f'<h2><span class="iss">Issue {i["no"]}:</span> {esc(i.get("title", ""))}</h2>\n<p class="dek">{esc(i.get("dek", ""))}</p>\n<a class="btn" href="{i["pdf"]}">Download PDF</a>')
    top, out = max(x["year"] for x in m), []
    for y in sorted({x["year"] for x in m}, reverse=True):
        its = [x for x in m if x["year"] == y]
        rows = "".join(f'<div class="r"><span class="no">{x["no"]}</span><div><h3>Issue {x["no"]}' + ('' if x.get("web") else '<span class="pdfonly">PDF only</span>') + f'</h3><p>{esc(x["weeks"])}</p></div><span class="go">' + (f'<a href="{link(x)}">Read</a>' if x.get("web") else "") + f'<a href="{x["pdf"]}">PDF</a></span></div>' for x in its)
        out.append(f'<details class="yr"{" open" if y == top else ""}><summary>{y} <small>{len(its)} issues</small></summary>{rows}</details>')
    note = '<p class="key">Web editions start with Issue 4. Earlier issues are PDF only.</p>' if any(not x.get("web") for x in m) else ""
    inject("index.html", "ARCHIVE", "\n".join(out) + note)

if __name__ == "__main__":
    inject("index.html", "LEADERBOARD", leaderboard())
    m = manifest()
    inject("index.html", "TX", transactions(m))
    inject("index.html", "RULES", rules())
    inject("index.html", "STANDINGS", standings())
    home_blocks(m)
    [issue(f'{x["no"]:02d}', x["year"]) for x in m if x.get("web")]
    print("site built")
