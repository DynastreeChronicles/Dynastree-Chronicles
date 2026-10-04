#!/usr/bin/env python3
"""Bake data into the HTML so pages never depend on a fetch() succeeding.
  - index.html: renders standings etc. from data/standings.json (always the latest finished week)
  - issues/<year>/issue-NN/index.html: a frozen snapshot "as of" the issue's week. Every table and
    number (standings, FAAB, draft slots, scores, records, bench, MVPs, trade assets, waiver claims)
    is computed from data/weeks + data/transactions.json. data/issues/issue-NN.json holds PROSE ONLY.
Run after sleeper_pull.py (the GitHub Action does this)."""
import json, os, re, sys
from collections import defaultdict
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
import sleeper_pull as sp   # build_standings() is shared so the issue snapshot uses the exact homepage logic
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


def jload(rel, default=None):
    p = os.path.join(ROOT, rel)
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else default

def load_week(n):
    return jload(f"data/weeks/week-{n:02d}.json")

def final_weeks(thru):
    return [w for n in range(1, thru + 1) for w in [load_week(n)] if w and w["final"]]

def faab_by_week(thru):
    """Waiver balance after each week, rebuilt from the transaction feed (matches Sleeper's balance)."""
    budget = (jload("data/league.json", {}) or {}).get("waiver_budget", 500)
    names = [r["manager"] for r in jload("data/standings.json", [])]
    bal, out = {m: budget for m in names}, {0: {m: budget for m in names}}
    tx = sorted(txfeed(), key=lambda t: (t["week"], t.get("created") or 0))
    for wk in range(1, thru + 1):
        for t in (x for x in tx if x["week"] == wk):
            if t["type"] == "trade":
                for sd in t["sides"]:
                    n = sd.get("receives_faab") or 0
                    if n:
                        bal[sd["manager"]] += n
                        for o in t["sides"]:
                            if o is not sd:
                                bal[o["manager"]] -= n
            else:
                bal[t["manager"]] -= t.get("bid") or 0
        out[wk] = dict(bal)
    return out

def asof(week):
    """Standings rows as of the end of `week`, same logic the Action uses for data/standings.json."""
    cur = jload("data/standings.json", [])
    fb = faab_by_week(week)[week]
    info = {r["roster_id"]: {"manager": r["manager"], "faab_remaining": fb[r["manager"]]} for r in cur}
    return sp.build_standings(final_weeks(week), info)

def pname(p):
    """'Jaxon Smith-Njigba' -> 'J. Smith-Njigba'; team defenses keep the team name."""
    parts = p["name"].split()
    if p.get("pos") == "DEF" or len(parts) < 2:
        return parts[-1] if parts else p["name"]
    return f"{parts[0][0]}. {' '.join(parts[1:])}"

def pts(x):
    return f"{x:.1f}"

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


MAXPF_TEXT = "<b>Max PF.</b> The points of your best possible lineup each week, added up (the same number as Sleeper's Max PF). The lowest total gets pick 1.01."
MAXPF_LONG = ("MAXPF (Max PF) is the points your best possible lineup would have scored each week, added up across the season. "
              "It is the same figure Sleeper shows as Max PF, not starters plus bench. Lowest MAXPF gets the 1st overall pick; highest picks 12th. "
              "The draft is linear, so the lowest MAXPF also picks first every round. Payouts still go to the playoff winner.")

def legend():
    """Collapsed 'how to read this' glossary shared by the home and issue standings."""
    up, dn = '<span class="up">&#9650;</span>', '<span class="dn">&#9660;</span>'
    items = [("W-L", "<b>Record</b> through the latest finished week."),
             ("MOV", f"<b>Movement</b> since last week. {up} 2 = climbed two spots, {dn} 2 = dropped two, &mdash; = no change. In Draft order it is the pick: {up} = earlier (closer to 1.01), {dn} = later."),
             ("PF", "<b>Points for.</b> Total points your team has scored this season."),
             ("Pick", "<b>2027 rookie draft slot.</b> 1.01 is the first overall pick."),
             ("MAXPF", MAXPF_TEXT),
             ("FUT CAP", "<b>Future capital.</b> Points for owned picks: Early 1st 100, Mid-Late 1st 75, 2nd-year 1st 60, 3rd-year 1st 50, any 2nd 30, any 3rd 10."),
             ("FAAB", "<b>Waiver budget</b> left, out of $500.")]
    out = "".join(f"<div><dt>{t}</dt><dd>{d}</dd></div>" for t, d in items)
    return f'<details class="legend"><summary>How to read this table</summary><dl>{out}</dl></details>'

def standings(rows=None, fin=None, root=""):
    """The standings block (Standings order / Draft order). Used by the home page (live data)
    and by each issue page (snapshot rows), so both always look and read the same."""
    if rows is None:
        rows = json.load(open(os.path.join(ROOT, "data/standings.json")))
    fin = fin or (rows and max(r["wins"] + r["losses"] + r["ties"] for r in rows))
    pp = prev_picks(fin)
    fc = jload("data/fut_cap.json", {})
    team = lambda r: f'<td>{av(r["manager"], 24, root)}<b>{esc(r["manager"])}</b></td>'
    n = len(rows)
    def rank_cell(r):
        k = r["rank"]
        if k <= 3:
            name = ["gold", "silver", "bronze"][k - 1]
            return f'<img class="rkt" src="{root}assets/trophy-{name}-sm.webp" alt="#{k}" width="24" height="44">'
        if k >= n - 1:
            return f'<img class="rkt" src="{root}assets/trophy-trash-sm.webp" alt="#{k}" width="26" height="44">'
        return str(k)
    rk = "".join(f'<tr><td class="n rkc">{rank_cell(r)}</td>{team(r)}<td class="n">{esc(r["record"])}</td><td class="n mv">{mv(r.get("move", 0))}</td><td class="n">{r["pf"]:.2f}</td><td class="n">${r["faab_remaining"]}</td></tr>' for r in rows)
    dr = ""
    for r in sorted(rows, key=lambda r: r["draft_pick"]):
        f = fc.get(r["manager"])
        dr += (f'<tr><td class="n pick">1.{r["draft_pick"]:02d}</td>{team(r)}<td class="n">{"&mdash;" if f is None else f}</td>'
               f'<td class="n">{r["maxpf"]:.2f}</td><td class="n mv">{mv(pp.get(r["roster_id"], r["draft_pick"]) - r["draft_pick"])}</td><td class="n">${r["faab_remaining"]}</td></tr>')
    h = lambda cols: "<tr>" + "".join(f'<th{" class=\"n\"" if i else ""}>{c}</th>' if c != "Team" else "<th>Team</th>" for i, c in enumerate(cols)) + "</tr>"
    return (f'<div class="sortbar" role="group" aria-label="Standings view"><button class="chip on" data-view="rank">Standings order</button><button class="chip" data-view="draft">Draft order</button></div>'
            f'<div class="sc" id="v-rank"><table id="standtable"><thead>{h(["#", "Team", "W-L", "MOV", "PF", "FAAB"])}</thead><tbody>{rk}</tbody></table>'
            f'{legend()}</div>'
            f'<div class="sc" id="v-draft" hidden><table id="drafttable"><thead>{h(["Pick", "Team", "FUT CAP", "MAXPF", "MOV", "FAAB"])}</thead><tbody>{dr}</tbody></table>'
            f'{legend()}</div>')

# ---------------------------------------------------------------- issue pages
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

POS_ORDER = {"QB": 0, "RB": 1, "WR": 2, "TE": 3}

def asset_list(side, other):
    """What `side` receives, as the strings the issue page turns into chips."""
    out = [f'{p["name"]} ({p["pos"]}, {p["team"]})' for p in sorted(side["receives_players"], key=lambda p: (POS_ORDER.get(p["pos"], 9), p["name"]))]
    for k in sorted(side["receives_picks"], key=lambda k: (k["season"], int(k["round"]))):
        frm = "" if k["original_owner"] in (other["manager"], side["manager"]) else f' (from {k["original_owner"]})'
        out.append(f'{k["season"]} {ordinal(int(k["round"]))}-round pick{frm}')
    if side.get("receives_faab"):
        out.append(f'${side["receives_faab"]} FAAB')
    return out

def wire_trades(hand, week, rep):
    """Hand-written trade prose + assets taken from the Sleeper feed."""
    feed = [t for t in txfeed() if t["type"] == "trade" and t["week"] <= week]
    used, out = set(), []
    for h in hand:
        pair = {h["a"], h["b"]}
        hit = next((t for t in sorted(feed, key=lambda t: -(t.get("created") or 0)) if {x["manager"] for x in t["sides"]} == pair and id(t) not in used), None)
        if not hit:
            rep.append(f'trade {h["a"]}/{h["b"]}: no matching trade in transactions.json, assets omitted')
            out.append({**h, "ar": [], "br": []})
            continue
        used.add(id(hit))
        sa = next(x for x in hit["sides"] if x["manager"] == h["a"]); sb = next(x for x in hit["sides"] if x["manager"] == h["b"])
        if hit["week"] != week:
            rep.append(f'trade {h["a"]}/{h["b"]}: Sleeper logs it in Week {hit["week"]}, the issue covers Week {week}')
        out.append({**h, "ar": asset_list(sa, sb), "br": asset_list(sb, sa)})
    for t in feed:
        if t["week"] == week and id(t) not in used:
            rep.append("trade in Week %d not covered by the issue: %s" % (week, " / ".join(x["manager"] for x in t["sides"])))
    return out

def wire_waivers(notes, week, rep=None):
    """Every claim that week comes from the feed; the desk's flags and one-liners (notes) are keyed by manager + player."""
    ann = {(n["mgr"], _k(n["player"])): n for n in notes}
    used, out = set(), []
    for t in sorted((x for x in txfeed() if x["week"] == week and x["type"] != "trade"), key=lambda x: x.get("created") or 0):
        key = (t["manager"], _k(t["added"]["name"], t["added"].get("pos", "")))
        n = ann.get(key)
        if n:
            used.add(key)
        out.append([t["manager"], t["added"]["name"], t.get("bid") or 0, ", ".join(t.get("dropped") or []), n["flag"] if n else "", n.get("note", "") if n else "", t["added"].get("pos", "")])
    if rep is not None:
        for k, n in ann.items():
            if k not in used:
                rep.append(f'waiver note for {n["mgr"]} / {n["player"]} has no matching claim in Week {week}')
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

def final_banner(week):
    """Biggest margin of the week, straight from the week file."""
    w = load_week(week)
    best = max((t for t in w["teams"] if t["result"] == "W"), key=lambda t: t["points"] - t["opponent_points"])
    gap = best["points"] - best["opponent_points"]
    return (f'<section class="final" aria-label="Week {week} final score">\n'
            f'<div class="side w"><small>Week {week} final</small><span>{esc(best["manager"])}</span><b>{best["points"]:.2f}</b></div>\n'
            f'<div class="gap"><b>&minus;{gap:.2f}</b><small>Blowout of the week</small></div>\n'
            f'<div class="side l"><small>Week {week} final</small><span>{esc(best["opponent"])}</span><b>{best["opponent_points"]:.2f}</b></div>\n</section>')

def motw_banner(week, pm, rep):
    """Result card for the Match of the Week picked in the previous issue, scores straight from the week file."""
    wkd = {t["manager"]: t for t in load_week(week)["teams"]}
    a, b = wkd[pm["a"]], wkd[pm["b"]]
    if a["opponent"] != pm["b"]:
        rep.append(f'prev_motw {pm["a"]} vs {pm["b"]}: Sleeper says {pm["a"]} played {a["opponent"]}')
    win, lose = (a, b) if a["points"] >= b["points"] else (b, a)
    gap = win["points"] - lose["points"]
    return (f'<section class="final motw" aria-label="Match of the Week from Issue {pm["issue"]}: final score">\n'
            f'<div class="mtop"><img src="../../../assets/badge-motw.webp" alt="Match of the Week" width="49" height="60"><div><b>Game of the week</b><small>Picked in Issue {pm["issue"]} &middot; Week {week} final</small></div></div>\n'
            f'<div class="side w"><small>Winner</small><span>{esc(win["manager"])}</span><b>{win["points"]:.2f}</b></div>\n'
            f'<div class="gap"><b>&minus;{gap:.2f}</b><small>Decided by</small></div>\n'
            f'<div class="side l"><small>Loser</small><span>{esc(lose["manager"])}</span><b>{lose["points"]:.2f}</b></div>\n'
            f'<p class="mnote">{esc(pm.get("note", ""))}</p>\n</section>')

def issue(n="04", y=2026):
    man = next(x for x in manifest() if x["no"] == int(n))
    wk = man.get("wire_week") or man.get("standings_week")
    assert wk, f"issues.json needs wire_week for issue {n}"
    d = json.load(open(os.path.join(ROOT, f"data/issues/issue-{n}.json"), encoding="utf-8"))
    rep = []
    rows = asof(wk)
    by = {r["manager"]: r for r in rows}
    wkd = {t["manager"]: t for t in load_week(wk)["teams"]}
    fb = faab_by_week(wk)
    rank_pf = {r["manager"]: i + 1 for i, r in enumerate(sorted(rows, key=lambda r: -r["pf"]))}
    history = final_weeks(wk)

    def need(m):
        if m not in by:
            raise SystemExit(f"issue-{n}.json names {m!r}, who is not in the league data")
        return by[m]

    # standings (same block as the home page)
    inject(f"issues/{y}/issue-{n}/index.html", "STAND", standings(rows, wk, "../../../"))
    pm = d.get("prev_motw")
    inject(f"issues/{y}/issue-{n}/index.html", "FINAL", (motw_banner(wk, pm, rep) + "\n" if pm else "") + final_banner(wk))

    # bankroll: balances and weekly change from the feed, notes stay hand-written
    notes = d["bank"]["notes"]
    d["bank"] = [[m, f"${fb[wk][m]}", (lambda dl: "0" if not dl else f"+${dl}" if dl > 0 else f"-${-dl}")(fb[wk][m] - fb[wk - 1][m]), notes.get(m, "")] for m in sorted(fb[wk], key=lambda m: (fb[wk][m], list(notes).index(m) if m in notes else 99))]
    d["standings"] = {"bank": d.pop("bank")}

    # wire
    d["wire"]["trades"] = wire_trades(d["wire"]["trades"], wk, rep)
    d["wire"]["waivers"] = wire_waivers(d["wire"]["waivers"], wk, rep)
    for m in dict.fromkeys(x[0] for x in d["wire"]["waivers"]):
        if not d["wire"].get("desk", {}).get(m):
            rep.append(f"no desk aside for {m} in wire.desk (their transaction list will show none)")

    # post-game: scores, records, bench points and MVPs
    for m in d["post"]:
        a, b = wkd[m["a"]], wkd[m["b"]]
        if a["opponent"] != m["b"]:
            rep.append(f'post-game card {m["a"]} vs {m["b"]}: Sleeper says {m["a"]} played {a["opponent"]}')
        m.update(ar=need(m["a"])["record"], br=need(m["b"])["record"], sa=a["points"], sb=b["points"],
                 ba=a["bench_points"], bb=b["bench_points"], la=a["left_on_bench"], lb=b["left_on_bench"],
                 ma=f'{pname(a["mvp"])} {pts(a["mvp"]["pts"])}', mb=f'{pname(b["mvp"])} {pts(b["mvp"]["pts"])}')

    # pre-game and match of the week: records from the snapshot
    for m in d["pre"] + [d["motw"]]:
        m["ar"], m["br"] = need(m["a"])["record"], need(m["b"])["record"]
    mo = d["motw"]
    best = lambda mg: max(t["points"] for w in history for t in w["teams"] if t["manager"] == mg)
    avg = lambda mg: need(mg)["pf"] / (need(mg)["wins"] + need(mg)["losses"] + need(mg)["ties"])
    mo["stats"] = [["Record", mo["ar"], mo["br"]],
                   ["PF Rank", ordinal(rank_pf[mo["a"]]), ordinal(rank_pf[mo["b"]])],
                   ["Best Week", f"{best(mo['a']):.2f}", f"{best(mo['b']):.2f}"],
                   ["AVG PF", f"{avg(mo['a']):.1f}", f"{avg(mo['b']):.1f}"]]

    d["meta"] = {"week": wk, "maxpf": MAXPF_LONG}
    path = f"issues/{y}/issue-{n}/index.html"
    blob = json.dumps(d, ensure_ascii=False).replace("</", "<\\/")
    inject(path, "ISSUE-DATA", f'<script id="issue-data" type="application/json">{blob}</script>')
    inject(path, "MANAGERS", '<script id="managers-data" type="application/json">' + json.dumps(managers(), ensure_ascii=False).replace("</", "<\\/") + "</script>")
    for line in rep:
        print(f"  note (issue {n}): {line}")

def leaderboard():
    """Home-page leaderboard: a podium for the top three (the trophy is the rank, no '#1' text) and a danger zone for the bottom two."""
    rows = json.load(open(os.path.join(ROOT, "data/standings.json")))
    def pod(r, cls, k, label):
        return (f'<div class="pd {cls}"><img class="tro" src="assets/trophy-{k}.webp" alt="{label}" width="132" height="240" loading="lazy">'
                f'<div class="pi">{av(r["manager"], 44)}<h3>{esc(r["manager"])}</h3><p>{esc(r["record"])} &middot; {r["pf"]:.1f} PF</p></div></div>')
    top = "".join(pod(r, c, k, l) for r, c, k, l in zip(rows[:3], ("p1", "p2", "p3"), ("gold", "silver", "bronze"), ("1st place", "2nd place", "3rd place")))
    low = "".join(f'<div class="lo"><img class="tro tt" src="assets/trophy-trash.webp" alt="Last place" width="132" height="240" loading="lazy">{av(r["manager"], 40)}<div><h3>{esc(r["manager"])}</h3><p>{esc(r["record"])} &middot; {r["pf"]:.1f} PF</p></div></div>' for r in rows[-2:])
    return (f'<div class="lbx"><div class="podium">{top}</div><div class="dz"><h3 class="dzh">The Danger Zone</h3><div class="dzg">{low}</div></div></div>'
            '<p class="key"><a href="#standings">Full standings below</a></p>')

def transactions(m):
    i = next((x for x in m if x.get("web")), None)
    if not i:
        return ""
    fin = i.get("wire_week") or 1
    d = json.load(open(os.path.join(ROOT, f"data/issues/issue-{i['no']:02d}.json"), encoding="utf-8"))
    ws = wire_waivers(d["wire"]["waivers"], fin)
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
    desk = d["wire"].get("desk", {})
    cards = []
    for mg in sorted((o for o in order if rank(o) < 9), key=rank):
        allm = [x for x in ws if x[0] == mg]
        keep = [x for x in allm if notable(x)]
        cards.append(f'<div class="txg"><div class="txh">{av(mg, 28)}<b>{esc(mg)}</b><small>{len(keep)} of {len(allm)} moves</small></div>' + "".join(move_html(x) for x in keep) + (f'<p class="desk mdesk">{esc(desk[mg])}</p>' if desk.get(mg) else "") + "</div>")
    out.append('<div class="txgrid">' + "".join(cards) + "</div>")
    link = f'issues/{i["year"]}/issue-{i["no"]:02d}/#wire'
    return '<div class="txl">' + "".join(out) + f'</div><p class="key"><a class="btn o" href="{link}">See all {len(ws)} waiver moves and trade grades in Issue {i["no"]}</a></p>'

def rules():
    from collections import Counter
    c = Counter(json.load(open(os.path.join(ROOT, "data/league.json")))["roster_positions"])
    nm = {"SUPER_FLEX": "SFLEX", "BN": "Bench"}
    lineup = ", ".join((f"{n}&times;" if n > 1 else "") + nm.get(p, p) for p, n in c.items())
    cards = [("Roster", lineup), ("Rookie draft", "2027 order by MAXPF (the best possible lineup each week, added up; Sleeper's Max PF), linear. Lowest MAXPF picks 1.01."), ("Trades", "Vetoes are on."), ("Payouts", "The playoff winner collects.")]
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
