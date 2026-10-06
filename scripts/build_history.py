#!/usr/bin/env python3
"""Hall of Fame & League History: history/index.html. A permanent page that never resets.

Numbers: rebuilt from every season's data/<season>/ folder on each run (weekly, with the Action).
Hand-entered (data/history.json): champion, runner-up and final score per season, optional award overrides,
the volume story, and the result of each bold prediction. Everything else is derived.
Run after build_managers.py:  python scripts/build_history.py"""
import glob, json, os, re, sys
from collections import defaultdict
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import build_site as bs
import seasons as ss
from build_site import esc, av, jload, ROOT

R = "../"
NOTES = []
AWARDS = [("best_manager", "&#127941;", "Best Manager", "Highest lineup efficiency: points scored as a share of the best possible lineup."),
          ("biggest_tank", "&#128201;", "Biggest Tank", "Lowest MAXPF. The best possible lineup was the weakest, so the 1.01 is theirs."),
          ("waiver_mvp", "&#128142;", "Waiver Wire MVP", "Most weekly Waiver Wire MVP nods from the desk."),
          ("bold_hit", "&#127919;", "Bold Prediction Hit", "The desk's boldest call that came true.")]

def ml(m):
    return f'<a class="ml" href="{R}managers/{esc(m.lower())}/">{esc(m)}</a>'

def who(m, size=36):
    return f'<span class="hf-who">{av(m, size, R)}{ml(m)}</span>'

def fmt(v):
    return f"{v:,.2f}"

# ------------------------------------------------------------------ data
def load_settings():
    st = jload("data/settings.json", {}) or {}
    return int(st.get("playoff_start", 15)), int(st.get("playoff_teams", 6))

def load_seasons():
    """Every season with finished weeks: {year, vol, status, weeks, tx, table, rank}."""
    reg, out = ss.load(), []
    ps, _ = load_settings()
    for y in sorted(reg):
        wk = []
        for f in sorted(glob.glob(os.path.join(ROOT, "data", y, "weeks", "week-*.json"))):
            w = bs.canon(json.load(open(f, encoding="utf-8")))
            if w.get("final"):
                wk.append(w)
        if not wk:
            continue
        tab = defaultdict(lambda: {"w": 0, "l": 0, "t": 0, "pf": 0.0, "pa": 0.0, "maxpf": 0.0})
        for w in wk:
            if w["week"] >= ps:
                continue
            for x in w["teams"]:
                r = tab[x["manager"]]
                r[{"W": "w", "L": "l", "T": "t"}.get(x["result"], "t")] += 1
                r["pf"] += x["points"]; r["pa"] += x["opponent_points"]; r["maxpf"] += x["maxpf"]
        rank = sorted(tab, key=lambda m: (-tab[m]["w"], -tab[m]["pf"]))
        out.append({"year": y, "vol": ss.volume(y, reg), "closed": ss.is_closed(reg[y]), "weeks": wk, "thru": max(w["week"] for w in wk),
                    "tx": jload(f"data/{y}/transactions.json", []) or [], "table": dict(tab), "rank": rank})
    return out

def issue_rows():
    return bs.manifest()

def all_issue_data():
    return [(y, n, bs.canon(json.load(open(f, encoding="utf-8")))) for y, n, f in bs.issue_files()]

# ------------------------------------------------------------------ records
def records(S, ps):
    best, worst, blow, mxp, faab, streak = [], [], [], [], [], []
    seq = defaultdict(list)
    for s in S:
        for w in s["weeks"]:
            for t in w["teams"]:
                loc = f'{s["year"]} &middot; Week {w["week"]}'
                opp = f'vs {esc(t["opponent"])} ({fmt(t["opponent_points"])})'
                best.append((t["points"], t["manager"], loc, opp))
                if w["week"] < ps:
                    worst.append((t["points"], t["manager"], loc, opp))
                if t["result"] == "W":
                    blow.append((t["points"] - t["opponent_points"], t["manager"], loc, f'{fmt(t["points"])} to {fmt(t["opponent_points"])} over {esc(t["opponent"])}'))
                seq[t["manager"]].append((s["year"], w["week"], t["result"]))
        for m, r in s["table"].items():
            tail = f'{s["year"]} season' if s["closed"] else f'{s["year"]} &middot; through Week {s["thru"]}'
            mxp.append((r["maxpf"], m, tail, "Best possible lineup, added up"))
        for x in s["tx"]:
            if x.get("type") == "waiver" and x.get("bid"):
                faab.append((x["bid"], x["manager"], f'{s["year"]} &middot; Week {x["week"]}', esc(x["added"]["name"])))
    latest = max((s["year"], s["thru"]) for s in S)
    for m, g in seq.items():
        g.sort(); run, start, top = 0, None, None
        for i, (y, wk, res) in enumerate(g):
            if res == "W":
                run += 1; start = start or (y, wk)
                if not top or run > top[0]:
                    live = (y, wk) == latest
                    top = (run, start, (y, wk), live)
            else:
                run, start = 0, None
        if top:
            a, b = top[1], top[2]
            span = f'{a[0]} Wk {a[1]}' + (f' to {b[0]} Wk {b[1]}' if a != b else "")
            streak.append((top[0], m, span, "Still active" if top[3] else "Snapped"))
    return best, worst, blow, mxp, streak, faab

def record_tiles(S, ps):
    best, worst, blow, mxp, streak, faab = records(S, ps)
    spec = [("Best single week", "&#128293;", sorted(best, key=lambda x: -x[0]), fmt),
            ("Worst week", "&#129398;", sorted(worst, key=lambda x: x[0]), fmt),
            ("Biggest blowout", "&#128165;", sorted(blow, key=lambda x: -x[0]), lambda v: "+" + fmt(v)),
            ("Best MAXPF season", "&#128208;", sorted(mxp, key=lambda x: -x[0]), fmt),
            ("Longest win streak", "&#9889;", sorted(streak, key=lambda x: -x[0]), lambda v: f"{v} wins"),
            ("Most FAAB on one player", "&#128176;", sorted(faab, key=lambda x: -x[0]), lambda v: f"${v}")]
    out = []
    for label, ico, rows, f in spec:
        if not rows:
            continue
        v, m, loc, ctx = rows[0]
        nxt = next((r for r in rows[1:] if r[1] != m), None)
        chase = f'<p class="hf-next">Next: {esc(nxt[1])} &middot; {f(nxt[0])}</p>' if nxt else ""
        out.append(f'<div class="hf-rec"><small><i aria-hidden="true">{ico}</i>{label}</small><b>{f(v)}</b>{who(m)}<p>{ctx}</p><p class="hf-loc">{loc}</p>{chase}</div>')
    return '<div class="hf-recs">' + "".join(out) + "</div>"

# ------------------------------------------------------------------ champions
def hist_season(H, y):
    return (H.get("seasons") or {}).get(y) or {}

def champion_wall(S, H, ps, pt):
    cards = []
    for s in sorted(S, key=lambda s: s["year"], reverse=True):
        y, hs = s["year"], hist_season(H, s["year"])
        label = f'Volume {s["vol"]} &middot; {y}'
        if hs.get("champion"):
            c, r = hs["champion"], hs.get("runner_up")
            fs = hs.get("final_score") or [None, None]
            score = f'<div class="hf-fs"><b>{fmt(fs[0])}</b><span>&ndash;</span><b class="lo">{fmt(fs[1])}</b></div>' if fs[0] is not None and fs[1] is not None else ""
            tn = (bs.managers().get(c) or {}).get("team_name")
            tn_html = '<p class="hf-tn">' + esc(tn) + "</p>" if tn else ""
            ru_html = "<p>Defeated " + ml(r) + " in the final.</p>" if r else ""
            note_html = '<p class="hf-note">' + esc(hs["note"]) + "</p>" if hs.get("note") else ""
            cards.append(f'<article class="hf-champ"><img class="tro" src="{R}assets/trophy-gold.webp" alt="Champion trophy" width="132" height="240" loading="lazy">'
                         f'<div class="hf-cmain"><small>{label} champion</small><h3>{who(c, 56)}</h3>{tn_html}{ru_html}{note_html}</div>{score}</article>')
        elif s["closed"]:
            NOTES.append(f"history: {y} is closed but data/history.json has no champion for it")
            cards.append(f'<article class="hf-race"><small>{label}</small><h3>Champion not recorded yet</h3><p>Add the champion, runner-up and final score for {y} to data/history.json.</p></article>')
        else:
            top = s["rank"][:3]
            chips = "".join(f'<div class="hf-lead"><em>{i + 1}</em>{who(m, 40)}<span>{s["table"][m]["w"]}-{s["table"][m]["l"]}{"-" + str(s["table"][m]["t"]) if s["table"][m]["t"] else ""} &middot; {s["table"][m]["pf"]:.1f} PF</span></div>' for i, m in enumerate(top))
            reg_total = ps - 1
            done = min(s["thru"], reg_total)
            cards.append(f'<article class="hf-race"><small>{label} &middot; in progress</small><h3>The crown is still up for grabs</h3>'
                         f'<div class="hf-prog" role="img" aria-label="Week {done} of {reg_total}"><i style="width:{done / reg_total * 100:.0f}%"></i></div>'
                         f'<p class="hf-pt">Regular season: Week {done} of {reg_total}. Top {pt} make the playoffs, which start Week {ps}.</p><div class="hf-leads">{chips}</div></article>')
    return "".join(cards)

# ------------------------------------------------------------------ careers
def careers(S, H, ps, pt):
    t = defaultdict(lambda: {"w": 0, "l": 0, "t": 0, "pf": 0.0, "titles": 0, "po": 0, "seasons": 0, "pace": None})
    for s in S:
        hs = hist_season(H, s["year"])
        po = hs.get("playoffs") or (s["rank"][:pt] if s["closed"] else [])
        for m, r in s["table"].items():
            c = t[m]; c["w"] += r["w"]; c["l"] += r["l"]; c["t"] += r["t"]; c["pf"] += r["pf"]; c["seasons"] += 1
            c["po"] += m in po
            if hs.get("champion") == m: c["titles"] += 1
            if not s["closed"]: c["pace"] = m in s["rank"][:pt]
    mg = bs.managers()
    order = sorted(t, key=lambda m: (-t[m]["titles"], -t[m]["po"], -(t[m]["w"] / max(1, t[m]["w"] + t[m]["l"] + t[m]["t"])), -t[m]["pf"]))
    rows = []
    for i, m in enumerate(order, 1):
        c = t[m]; g = c["w"] + c["l"] + c["t"]
        rec = f'{c["w"]}-{c["l"]}' + (f'-{c["t"]}' if c["t"] else "")
        pace = "" if c["pace"] is None else ('<span class="hf-in">In</span>' if c["pace"] else '<span class="hf-out">Out</span>')
        alum = "" if mg.get(m, {}).get("active", True) else '<small class="hf-alum">Alumni</small>'
        rows.append(f'<tr><td class="n">{i}</td><td>{who(m, 28)}{alum}</td><td class="n hf-ti">{c["titles"] or "&ndash;"}</td><td class="n">{c["po"]}</td><td class="n">{pace}</td>'
                    f'<td class="n">{rec}</td><td class="n">{c["w"] / g * 100:.1f}%</td><td class="n">{fmt(c["pf"])}</td><td class="n">{c["seasons"]}</td></tr>')
    heads = ["#", "Manager", "Titles", "Playoffs", "Pace", "Record", "Win %", "PF", "Seasons"]
    head = "".join("<th" + ("" if i == 1 else ' class="n"') + ">" + h + "</th>" for i, h in enumerate(heads))
    return (f'<div class="sc"><table class="hf-tbl"><thead><tr>{head}</tr></thead><tbody>{"".join(rows)}</tbody></table></div>'
            f'<p class="key">Regular-season record and PF across every volume (weeks before {ps}). Playoffs counts finished seasons; Pace shows who sits in a playoff spot right now. Sorted by titles, playoff trips, then win rate.</p>')

# ------------------------------------------------------------------ predictions and awards
def predictions(H):
    res, out = H.get("predictions") or {}, []
    for y, n, d in sorted(all_issue_data(), key=lambda x: (x[0], x[1])):
        for i, b in enumerate(d.get("bold") or []):
            k = f"{y}-{n}-{i}"
            r = res.get(k) or {}
            out.append({"key": k, "year": str(y), "no": n, "head": b[0], "result": r.get("result", "pending"), "note": r.get("note", ""), "star": bool(r.get("star"))})
    return out

def award_values(S, H, preds):
    mvp = defaultdict(lambda: defaultdict(list))
    for y, n, d in all_issue_data():
        for x in (d.get("wire") or {}).get("waivers", []):
            if isinstance(x, dict) and x.get("flag") == "mvp":
                mvp[str(y)][x["mgr"]].append(x["player"])
    out = {}
    for s in S:
        y, a = s["year"], {}
        eff = {m: (r["pf"] / r["maxpf"] * 100) if r["maxpf"] else 0 for m, r in s["table"].items()}
        bm = max(eff, key=eff.get); a["best_manager"] = (bm, f"{eff[bm]:.1f}% efficiency")
        tk = min(s["table"], key=lambda m: s["table"][m]["maxpf"]); a["biggest_tank"] = (tk, f'{fmt(s["table"][tk]["maxpf"])} MAXPF')
        mv = mvp.get(y) or {}
        if mv:
            top = max(len(v) for v in mv.values()); lead = [m for m, v in mv.items() if len(v) == top]
            a["waiver_mvp"] = (lead[0], f'{top} MVP nod{"s" if top > 1 else ""}: ' + ", ".join(mv[lead[0]]) + (" (tied with " + ", ".join(lead[1:]) + ")" if len(lead) > 1 else ""))
        hits = [p for p in preds if p["year"] == y and p["result"] == "hit"]
        pick = next((p for p in hits if p["star"]), hits[-1] if hits else None)
        if pick:
            a["bold_hit"] = (None, pick["head"] + f' (Issue {pick["no"]})')
        for k, v in (hist_season(H, y).get("awards") or {}).items():
            a[k] = (v.get("winner"), v.get("note") or (a.get(k) or ("", ""))[1])
        out[y] = a
    return out

def award_shelf(S, H, preds):
    vals, out = award_values(S, H, preds), []
    for s in sorted(S, key=lambda s: s["year"], reverse=True):
        y, cards = s["year"], []
        live = "" if s["closed"] else f'<em class="hf-live">Live &middot; Week {s["thru"]}</em>'
        for key, ico, title, rule in AWARDS:
            v = vals[y].get(key)
            body = (who(v[0], 40) if v[0] else '<span class="hf-who hf-desk">The Desk</span>') + '<p class="hf-av">' + esc(v[1]) + "</p>" if v else '<p class="hf-av">No winner yet.</p>'
            cards.append(f'<div class="hf-aw"><small><i aria-hidden="true">{ico}</i>{title}</small>{body}<p class="hf-rule">{rule}</p></div>')
        out.append(f'<h3 class="sub">Volume {s["vol"]} &middot; {y} {live}</h3><div class="hf-aws">{"".join(cards)}</div>')
    return "".join(out)

def ledger(preds):
    if not preds:
        return ""
    done = [p for p in preds if p["result"] in ("hit", "miss")]
    hits = sum(p["result"] == "hit" for p in done)
    pill = {"hit": "Hit", "miss": "Miss", "pending": "Pending"}
    def row(p):
        star = ' <span class="hf-star">&#9733; Hit of the year</span>' if p["star"] else ""
        note = "<small>" + esc(p["note"]) + "</small>" if p["note"] else ""
        return (f'<tr><td class="n">{p["year"]} &middot; Issue {p["no"]}</td><td>{esc(p["head"])}{star}{note}</td>'
                f'<td><span class="hf-pill {p["result"]}">{pill[p["result"]]}</span></td></tr>')
    rows = "".join(row(p) for p in preds)
    rate = f'{hits} of {len(done)} called ({hits / len(done) * 100:.0f}%)' if done else "No calls scored yet"
    return (f'<details class="hf-led"><summary>Prediction ledger<span>{rate}</span></summary><div class="sc"><table class="hf-tbl"><thead><tr><th>Issue</th><th>Call</th><th>Result</th></tr></thead><tbody>{rows}</tbody></table></div>'
            f'<p class="key">Every bold prediction the desk makes lands here automatically as Pending. Results are entered in data/history.json.</p></details>')

# ------------------------------------------------------------------ timeline
NOTRADES = '<p class="key">No trades yet.</p>'

def gets(sd):
    items = [p["name"] for p in sd["receives_players"]] + [f'{p["season"]} round {p["round"]} pick' for p in sd["receives_picks"]] + ([f'${sd["receives_faab"]} FAAB'] if sd.get("receives_faab") else [])
    return f'{esc(sd["manager"])} gets {esc(", ".join(items) or "nothing")}'

def timeline(S, H, ps):
    issues, out = issue_rows(), []
    for i, s in enumerate(sorted(S, key=lambda s: s["year"], reverse=True)):
        y, hs = s["year"], hist_season(H, s["year"])
        games = [t for w in s["weeks"] for t in w["teams"]]
        trades = [x for x in s["tx"] if x.get("type") == "trade"]
        faab = sum(x.get("bid") or 0 for x in s["tx"] if x.get("type") == "waiver")
        tiles = [("Games", str(len(games) // 2)), ("Avg score", f'{sum(t["points"] for t in games) / len(games):.1f}'), ("High", fmt(max(t["points"] for t in games))),
                 ("Low", fmt(min(t["points"] for t in games))), ("Trades", str(len(trades))), ("FAAB spent", f"${faab}")]
        stats = '<div class="hf-vs">' + "".join(f"<div><small>{a}</small><b>{b}</b></div>" for a, b in tiles) + "</div>"
        lead = s["rank"][0]; r = s["table"][lead]
        auto = f'{"Final" if s["closed"] else "Through Week " + str(s["thru"]) + ","} standings leader: {lead} at {r["w"]}-{r["l"]}.'
        story = f'<p class="hf-story">{esc(hs.get("story") or "")}</p><p class="hf-auto">{esc(auto)}</p>'
        tr = "".join(f'<div class="tx trade"><span class="tg trade">&#129309; TRADE &middot; WEEK {x["week"]}</span><div class="tb"><b>{" &harr; ".join(esc(sd["manager"]) for sd in x["sides"])}</b><small>{" &middot; ".join(gets(sd) for sd in x["sides"])}</small></div></div>' for x in sorted(trades, key=lambda x: x["created"]))
        its = [x for x in issues if str(x["year"]) == y]
        rows = "".join(f'<div class="r"><span class="no">{x["no"]}</span><div><h3>{esc(x.get("title", "Issue " + str(x["no"])))}</h3><p>{esc(x.get("weeks", ""))}</p></div><span class="go"><a href="{R}issues/{y}/issue-{x["no"]:02d}/">Read</a></span></div>' for x in its)
        status = "Complete" if s["closed"] else "In progress"
        out.append(f'<details class="yr hf-vol"{" open" if i == 0 else ""}><summary>Volume {s["vol"]} &middot; {y} <small>{status} &middot; {len(its)} issues</small></summary>'
                   f'{story}{stats}<h3 class="sub">Key trades</h3><div class="txl">{tr or NOTRADES}</div><h3 class="sub">Issue index</h3><div class="arch">{rows}</div></details>')
    return "".join(out)

# ------------------------------------------------------------------ page
def shell(body, sub):
    fonts = '<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Oswald:wght@500;600;700&display=swap" rel="stylesheet">'
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Hall of Fame &amp; League History | Dynastree Chronicles</title><meta name="description" content="Champions, records, careers, awards and every volume of the Dynastree dynasty league. It never resets."><meta name="robots" content="noindex">
{fonts}<link rel="stylesheet" href="{R}css/dynastree.css"><link rel="stylesheet" href="{R}css/history.css">
<link rel="icon" type="image/png" sizes="32x32" href="{R}assets/favicon-32.png"><link rel="apple-touch-icon" href="{R}assets/apple-touch-icon.png"></head><body>
<header class="mast"><div class="wrap"><img src="{R}assets/crest-mark.webp" alt="Dynastree Chronicles crest" width="79" height="96"><div><h1><a href="{R}">Dynastree <span>Chronicles</span></a></h1><p>{esc(sub)}</p></div></div></header>
<nav class="sticky"><div class="wrap"><a href="{R}#archive">Issues</a><a href="{R}#standings">Standings</a><a href="{R}managers/">Managers</a><a href="{R}history/">History</a><a href="{R}ledger/">Ledger</a><a href="{R}#transactions">Transactions</a><a href="{R}#rules">Rules</a><a href="{R}#scoring">Scoring</a></div></nav>
<main class="wrap">{body}</main>
<footer><div class="wrap"><img class="tree" src="{R}assets/tree.webp" alt="" width="40"><p>Time heals all wounds, but screenshots last forever.</p></div></footer>
<script src="{R}js/site.js"></script></body></html>'''

def build():
    H = jload("data/history.json", {}) or {}
    ps, pt = load_settings()
    S = load_seasons()
    if not S:
        print("history: no finished weeks yet, page not built"); return
    preds = predictions(H)
    games = sum(len(w["teams"]) // 2 for s in S for w in s["weeks"])
    trades = sum(1 for s in S for x in s["tx"] if x.get("type") == "trade")
    faab = sum(x.get("bid") or 0 for s in S for x in s["tx"] if x.get("type") == "waiver")
    titles = sum(1 for s in S if hist_season(H, s["year"]).get("champion"))
    chips = [(str(len(S)), "Volumes"), (str(len(issue_rows())), "Issues"), (str(games), "Games played"), (str(trades), "Trades"), (f"${faab}", "FAAB spent"), (str(titles), "Titles awarded")]
    hero = ('<section class="hf-hero"><small>The permanent record</small><h2>Hall of Fame <i>&amp;</i> League History</h2>'
            '<p>This page never resets. Every volume stays on the wall, every record keeps counting, and each offseason adds a new crown.</p>'
            '<div class="hf-stats">' + "".join(f"<div><b>{a}</b><small>{b}</small></div>" for a, b in chips) + '</div>'
            '<p class="hf-jump"><a href="#champions">Champions</a><a href="#records">Records</a><a href="#careers">Careers</a><a href="#awards">Awards</a><a href="#timeline">Timeline</a></p></section>')
    body = (hero +
            '<h2 class="sec" id="champions">Champions wall</h2><div class="hf-wall">' + champion_wall(S, H, ps, pt) + "</div>"
            '<h2 class="sec" id="records">All-time records</h2>' + record_tiles(S, ps) +
            '<h2 class="sec" id="careers">Manager careers</h2>' + careers(S, H, ps, pt) +
            '<h2 class="sec" id="awards">Award shelf</h2>' + award_shelf(S, H, preds) + ledger(preds) +
            '<h2 class="sec" id="timeline">Season by season</h2>' + timeline(S, H, ps))
    p = os.path.join(ROOT, "history", "index.html"); os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, "w", encoding="utf-8").write(shell(body, "Hall of Fame & League History"))
    for n in NOTES: print("  note (" + n + ")")
    print(f"built history page ({len(S)} volume{'s' if len(S) != 1 else ''}, {len(preds)} predictions tracked)")

if __name__ == "__main__":
    build()
