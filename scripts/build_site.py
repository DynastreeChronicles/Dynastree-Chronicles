#!/usr/bin/env python3
"""Bake data into the HTML so pages never depend on a fetch() succeeding.
  - index.html: renders standings etc. from data/standings.json (always the latest finished week)
  - issues/<year>/issue-NN/index.html: a frozen snapshot "as of" the issue's week. Every table and
    number (standings, FAAB, draft slots, scores, records, bench, MVPs, trade assets, waiver claims)
    is computed from data/weeks + data/transactions.json. data/issues/issue-NN.json holds PROSE ONLY.
    The page shell is rendered from scripts/templates/issue.html, so a new issue needs only its JSON
    and its entry in data/issues.json: no hand-made HTML.
Every season lives in its own folder (data/2026/, data/2027/, ...); see scripts/seasons.py. Each issue page is built from
the data of ITS season, so a new season never overwrites an old issue. Run after sleeper_pull.py (the GitHub Action does this)."""
import glob, json, os, re, sys
from collections import defaultdict
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
import seasons as ss
import sleeper_pull as sp   # build_standings() is shared so the issue snapshot uses the exact homepage logic

SEASON = None
_TX = None

def use(season):
    """Point every data loader at one season's folder (data/<season>/). Resets the transaction cache."""
    global SEASON, _TX
    SEASON, _TX = str(season), None

def S(rel):
    return ss.srel(SEASON, rel)

def display_season():
    """Season shown on the home page standings and leaderboard: the newest one that has finished weeks."""
    return ss.latest_with_standings() or ss.active() or "2026"

use(display_season())

def draft_year(season=None):
    """The rookie draft a season's MAXPF order decides: the season after it (2026 -> 2027)."""
    return int(season or SEASON) + 1

def attr(x):
    """Escape text for use inside a double-quoted HTML attribute."""
    return esc(x).replace('"', "&quot;")
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


def alias():
    """Old handle -> current handle, from "former_names" in data/managers.json (history keeps working after a rename)."""
    return {o: n for n, m in managers().items() for o in m.get("former_names", [])}

def canon(x):
    """Rename old handles everywhere in loaded data: dict keys and exact-match string values."""
    a = alias()
    if not a: return x
    if isinstance(x, dict): return {a.get(k, k): canon(v) for k, v in x.items()}
    if isinstance(x, list): return [canon(v) for v in x]
    return a.get(x, x) if isinstance(x, str) else x

def jload(rel, default=None):
    p = os.path.join(ROOT, rel)
    return canon(json.load(open(p, encoding="utf-8"))) if os.path.exists(p) else default

def load_week(n):
    return jload(S(f"weeks/week-{n:02d}.json"))

def final_weeks(thru):
    return [w for n in range(1, thru + 1) for w in [load_week(n)] if w and w["final"]]

def faab_by_week(thru):
    """Waiver balance after each week, rebuilt from the transaction feed (matches Sleeper's balance)."""
    budget = (jload(S("league.json"), {}) or {}).get("waiver_budget", 500)
    names = [r["manager"] for r in jload(S("standings.json"), [])]
    bal, out = {m: budget for m in names}, {0: {m: budget for m in names}}
    tx = sorted(txfeed(), key=lambda t: (t["week"], t.get("created") or 0))
    for wk in range(0, thru + 1):   # week 0 = offseason moves carried in from the previous volume
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
    cur = jload(S("standings.json"), [])
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
        p = os.path.join(ROOT, S(f"weeks/week-{w:02d}.json"))
        if not os.path.exists(p):
            return {}
        for t in canon(json.load(open(p, encoding="utf-8")))["teams"]:
            tot[t["roster_id"]] = tot.get(t["roster_id"], 0) + t["maxpf"]
    return {r: i + 1 for i, r in enumerate(sorted(tot, key=lambda r: tot[r]))}

def mv(m):
    return f'<span class="up">&#9650; {m}</span>' if m > 0 else f'<span class="dn">&#9660; {-m}</span>' if m < 0 else '<span class="flat">&mdash;</span>'


# Issues that carry the "How MAXPF works" explainer. Every other issue gets the desk closer card in its place. Bold predictions show in every issue.
EXPLAIN = {(2026, 4)}

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
             ("Pick", f"<b>{draft_year()} rookie draft slot.</b> 1.01 is the first overall pick."),
             ("MAXPF", MAXPF_TEXT),
             ("FUT CAP", "<b>Future capital.</b> Points for owned picks: Early 1st 100, Mid-Late 1st 75, 2nd-year 1st 60, 3rd-year 1st 50, any 2nd 30, any 3rd 10."),
             ("FAAB", "<b>Waiver budget</b> left, out of $500.")]
    out = "".join(f"<div><dt>{t}</dt><dd>{d}</dd></div>" for t, d in items)
    return f'<details class="legend"><summary>How to read this table</summary><dl>{out}</dl></details>'

def standings(rows=None, fin=None, root=""):
    """The standings block (Standings order / Draft order). Used by the home page (live data)
    and by each issue page (snapshot rows), so both always look and read the same."""
    if rows is None:
        rows = jload(S("standings.json"))
    fin = fin or (rows and max(r["wins"] + r["losses"] + r["ties"] for r in rows))
    pp = prev_picks(fin)
    fc = jload(S("fut_cap.json"), {})
    team = lambda r: f'<td><a class="ml" href="{root}managers/{r["manager"].lower()}/">{av(r["manager"], 24, root)}<b>{esc(r["manager"])}</b></a></td>'
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

def txfeed():
    global _TX
    if _TX is None:
        _TX = jload(S("transactions.json"), [])
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
        has = lambda t: not h.get("match") or any(h["match"].lower() in q["name"].lower() for sd in t["sides"] for q in sd["receives_players"])   # optional "match": a player name, to tell two trades between the same pair apart
        hit = next((t for t in sorted(feed, key=lambda t: -(t.get("created") or 0)) if {x["manager"] for x in t["sides"]} == pair and id(t) not in used and has(t)), None)
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

def wire_waivers(notes, week, rep=None, keep=None):
    """Every claim that week comes from the feed; the desk's flags and one-liners (notes) are keyed by manager + player."""
    ann = {(n["mgr"], _k(n["player"])): n for n in notes}
    used, out = set(), []
    for t in sorted((x for x in txfeed() if x["week"] == week and x["type"] != "trade" and (keep is None or keep(x))), key=lambda x: x.get("created") or 0):
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

def art(name):
    """True when assets/<name>.webp exists, so pages fall back cleanly for issues that have no artwork yet."""
    return os.path.exists(os.path.join(ROOT, "assets", name + ".webp"))

# On-deck issue cards: assets/cards/<style>-NN.webp, made ahead of the issue they belong to. Nothing shows until that issue
# exists in data/issues.json. Finished art (assets/issue-card-NN.webp, assets/archive-issue-NN.webp) always wins over them.
# To swap which style goes where, change the two words below ("logo" = The Archive card with the crest, "plain" = number only).
CARD_STYLE = {"hero": "logo", "tile": "plain"}

def issue_art(slot, no):
    """Art for one issue. slot is "hero" (the card beside the issue title) or "tile" (the home page archive list).
    no is the two-digit issue number as text. Returns (name under assets/, width, height) or None."""
    for name in ({"hero": f"issue-card-{no}", "tile": f"archive-issue-{no}"}[slot], f"cards/{CARD_STYLE[slot]}-{int(no)}"):
        if art(name):
            try:
                from PIL import Image
                with Image.open(os.path.join(ROOT, "assets", name + ".webp")) as im:
                    return name, im.width, im.height
            except Exception:
                return name, None, None
    return None

def issue_img(slot, no, alt, root, cls="", lazy=False):
    """The <img> for an issue's hero card or archive tile, or "" when that issue has no art yet."""
    a = issue_art(slot, no)
    if not a:
        return ""
    name, w, h = a
    size = f' width="{w}" height="{h}"' if w and h else ""
    c = f' class="{cls}"' if cls else ""
    lz = ' loading="lazy"' if lazy else ""
    return f'<img{c} src="{root}assets/{name}.webp" alt="{alt}"{size}{lz}>'

def final_banner(week):
    """Biggest margin of the week, straight from the week file."""
    w = load_week(week)
    best = max((t for t in w["teams"] if t["result"] == "W"), key=lambda t: t["points"] - t["opponent_points"])
    gap = best["points"] - best["opponent_points"]
    return (f'<section class="final" aria-label="Week {week} final score">\n'
            f'<div class="side w"><small>Week {week} final</small><span>{esc(best["manager"])}</span><b>{best["points"]:.2f}</b></div>\n'
            f'<div class="gap"><img class="bo" src="../../../assets/badge-blowout-of-the-week.webp" alt="" width="90" height="96"><b>&minus;{gap:.2f}</b><small>Blowout of the week</small></div>\n'
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

def bold_handles(text):
    """Escape a paragraph and bold every manager handle (house style: handles bold, NFL players never)."""
    out = esc(text)
    for h in sorted(managers(), key=len, reverse=True):
        out = re.sub(rf"(?<![\w>]){re.escape(h)}(?![\w])", f"<strong>{h}</strong>", out)
    return out

def hz_block(kind, spec, week, root):
    """Hero / Zero card. Score and perfect-lineup flag come from the week file; the words come from the issue JSON."""
    teams = load_week(week)["teams"]
    perfects = [t for t in teams if t.get("optimal") and abs(t["points"] - t["optimal"]) < 0.005]
    pool = perfects if (kind == "hero" and perfects) else teams   # default hero: a perfect lineup first, else the top score
    pick = (max if kind == "hero" else min)(pool, key=lambda t: t["points"])
    mg = (spec or {}).get("manager") or pick["manager"]
    t = next((x for x in teams if x["manager"] == mg), pick)
    perfect = kind == "hero" and t.get("optimal") and abs(t["points"] - t["optimal"]) < 0.005
    head = f'{"Hero" if kind == "hero" else "Zero"}: {mg}, ' + ("perfect lineup" if perfect else f'{t["points"]:.2f}')
    text = esc((spec or {}).get("text") or f'{t["points"]:.2f} points in Week {week}.')
    desk = f'<p class="desk">{esc(spec["desk"])}</p>' if (spec or {}).get("desk") else ""
    return (f'<div><img class="hz-b" src="{root}assets/badge-{kind}.webp" alt="{kind.title()}"><h3>{esc(head)}</h3><p>{text}</p>{desk}</div>')

def render_page(man, d, y):
    """Write issues/<y>/issue-NN/index.html from scripts/templates/issue.html (markers left empty for the injectors)."""
    pre_s = bool(man.get("preseason"))   # issue 1 style: post-draft, no finished weeks yet
    n, wk = f'{man["no"]:02d}', 0 if pre_s else (man.get("wire_week") or man.get("standings_week"))
    tpl = open(os.path.join(HERE, "templates", "issue.html"), encoding="utf-8").read()
    root = "../../../"
    desk = d.get("desk") or []
    if not desk:
        print(f"  WARNING (issue {n}): issue JSON has no 'desk' paragraphs")
    pull = d.get("pull") or (re.split(r"(?<=[.!?])\s", desk[0])[0] if desk else man.get("banner", ""))
    vals = {"NO": str(man["no"]), "TITLE": esc(man.get("title", "")), "WEEKS": esc(man.get("weeks", f"Week {wk} post-game and Week {wk + 1} pre-game")),
            "MONTH": esc(man.get("month", "")), "BANNER": esc(man.get("banner", man.get("dek", ""))), "PULL": esc(pull),
            "WK": str(wk), "PRE": str(wk + 1), "VOL": f"Volume {vol(y)}, " if vol(y) else "",
            "DESK": "\n".join(f"<p>{bold_handles(x)}</p>" for x in desk),
            "HEROZERO": (hz_pre("hero", d["hero"]) + "\n" + hz_pre("zero", d["zero"])) if pre_s else (hz_block("hero", d.get("hero"), wk, root) + "\n" + hz_block("zero", d.get("zero"), wk, root)),
            "NAV_POST": "Draft Grades" if pre_s else "Post-Game",
            "NAV_POLL": "" if (pre_s or not d.get("poll")) else '<a href="#poll-sec">Poll</a>',
            "T_HZ": "Draft hero and draft zero" if pre_s else "Hero and zero of the week",
            "T_STAND": "The post-draft ledger" if pre_s else f"Standings: Week {wk}",
            "T_POST": "Draft grades and power rankings" if pre_s else f"Week {wk} post-game",
            "T_DRAMA": "Drama of the draft" if pre_s else "Drama of the week",
            "POLL_SEC": "" if (pre_s or not d.get("poll")) else '<h2 class="sec" id="poll-sec">Weekly poll</h2>\n<div id="poll"></div>',
            "PDF_NAV": "",
            "CARD": issue_img("hero", n, f"Issue {man['no']}", root, cls="icard"),
            "BADGE_POST": "" if pre_s else f'<img class="sbadge" src="{root}assets/badge-post-game.webp" alt="Post-Game" loading="lazy">',
            "PRINT": f'<p class="key"><a class="btn o" href="{root}">Back to the archive</a></p>\n'}
    for k, v in vals.items():
        tpl = tpl.replace("{{" + k + "}}", v)
    left = re.findall(r"\{\{[A-Z_]+\}\}", tpl)
    assert not left, f"unfilled template tokens: {left}"
    out = os.path.join(ROOT, f"issues/{y}/issue-{n}/index.html")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    open(out, "w", encoding="utf-8").write(tpl)

# ---------------------------------------------------------------- pre-season issue (Issue 1: post-draft, nothing played yet)
def draft_info():
    """Per-manager draft facts from data/draft.json (one row per pick: r, s, m, name, pos, team, auto)."""
    out = {}
    for p in jload(S("draft.json"), []):
        o = out.setdefault(p["m"], {"picks": [], "auto": 0, "pos": {"QB": 0, "RB": 0, "WR": 0, "TE": 0}, "slot": None})
        o["picks"].append(p)
        o["auto"] += 1 if p["auto"] else 0
        if p["pos"] in o["pos"]:
            o["pos"][p["pos"]] += 1
        if p["r"] == 1:
            o["slot"] = p["s"]
    for o in out.values():
        o["last_manual"] = max((p["r"] for p in o["picks"] if not p["auto"]), default=0)
    return out

def hz_pre(kind, spec):
    """Draft hero / zero card: the autopick count comes from data/draft.json, the words from the issue JSON."""
    a = draft_info()[spec["manager"]]["auto"]
    head = f'{"Hero" if kind == "hero" else "Zero"}: {spec["manager"]}, {a} autopick' + ("" if a == 1 else "s")
    desk = f'<p class="desk">{esc(spec["desk"])}</p>' if spec.get("desk") else ""
    return f'<div><img class="hz-b" src="../../../assets/badge-{kind}.webp" alt="{kind.title()}"><h3>{esc(head)}</h3><p>{esc(spec["text"])}</p>{desk}</div>'

def pre_banner(di):
    """Banner in the final-score layout: the two heaviest autopick users."""
    items = sorted(di.items(), key=lambda kv: kv[0], reverse=True)
    (a, ra), (b, rb) = sorted(items, key=lambda kv: -kv[1]["auto"])[:2]
    gap = ra["auto"] - rb["auto"]
    mid = "TIE" if gap == 0 else f"&minus;{gap}"
    return (f'<section class="final" aria-label="Draft day: autopick leaders">\n'
            f'<div class="side w"><small>Autopicks</small><span>{esc(a)}</span><b>{ra["auto"]}</b></div>\n'
            f'<div class="gap"><b>{mid}</b><small>Autopick Bowl</small></div>\n'
            f'<div class="side l"><small>Autopicks</small><span>{esc(b)}</span><b>{rb["auto"]}</b></div>\n</section>')

def ledger(d, bal):
    """Stand-in for the standings table before Week 1: draft slot, positions drafted, CPU picks, desk rank, FAAB."""
    di = draft_info()
    rank = {x["m"]: x["rank"] for x in d["draft"]}
    team = lambda m: f'<td>{av(m, 24, "../../../")}<b>{esc(m)}</b></td>'
    body = "".join(f'<tr><td class="n pick">1.{o["slot"]:02d}</td>{team(m)}<td class="n">{o["pos"]["QB"]}-{o["pos"]["RB"]}-{o["pos"]["WR"]}-{o["pos"]["TE"]}</td><td class="n">{o["auto"]}</td><td class="n">{rank.get(m, "")}</td><td class="n">${bal[m]}</td></tr>'
                   for m, o in sorted(di.items(), key=lambda kv: kv[1]["slot"]))
    head = '<tr><th class="n">Slot</th><th>Team</th><th class="n">QB-RB-WR-TE</th><th class="n">CPU picks</th><th class="n">Desk rank</th><th class="n">FAAB</th></tr>'
    key = ('<p class="key">Everyone is 0-0. Slot is the round-1 draft position (rounds 2 and 3 ran in reverse, then it snaked). '
           'QB-RB-WR-TE counts the players drafted at each position. CPU picks are the autopicker\'s. FAAB is the $500 budget after the claims processed so far.</p>')
    return f'<div class="sc"><table id="standtable"><thead>{head}</thead><tbody>{body}</tbody></table>{key}</div>'

def issue_pre(man, d, y, n):
    render_page(man, d, y)
    rep = []
    path = f"issues/{y}/issue-{n}/index.html"
    cut = man.get("tx_cutoff") or {}
    keep = lambda x: (x.get("created") or 0) <= cut.get(x["type"], 0)
    budget = (jload(S("league.json"), {}) or {}).get("waiver_budget", 500)
    names = [r["manager"] for r in jload(S("standings.json"), [])]
    bal = {m: budget for m in names}
    for t in txfeed():
        if t["week"] == 1 and t["type"] == "waiver" and keep(t):
            bal[t["manager"]] -= t.get("bid") or 0
    di = draft_info()
    if set(di) != set(names) or set(x["m"] for x in d["draft"]) != set(names):
        raise SystemExit(f"handles differ. standings: {sorted(names)} | draft.json: {sorted(di)} | issue-01 cards: {sorted(x['m'] for x in d['draft'])}")
    # draft cards: chips come from the draft file
    for x in d["draft"]:
        o = di[x["m"]]
        qbs = [p["name"].split()[-1] for p in o["picks"] if p["pos"] == "QB"][:3]
        x["chips"] = [f'{p["name"]} ({p["pos"]}, {p["team"]})' for p in o["picks"][:5]] + [f'QB room ({", ".join(qbs)})', f'Autopicks ({o["auto"]} of {len(o["picks"])})']
    d["draft"].sort(key=lambda x: x["rank"])
    inject(path, "STAND", ledger(d, bal))
    inject(path, "FINAL", pre_banner(di))
    # bankroll from the feed (claims processed so far)
    notes = d["bank"]["notes"]
    d["standings"] = {"bank": [[m, f"${bal[m]}", (lambda dl: "0" if not dl else f"-${-dl}")(bal[m] - budget), notes.get(m, "")]
                              for m in sorted(bal, key=lambda m: (bal[m], list(notes).index(m) if m in notes else 99))]}
    d.pop("bank")
    d["wire"]["trades"] = []
    d["wire"]["waivers"] = wire_waivers(d["wire"]["waivers"], 1, rep, keep)
    for m in dict.fromkeys(x[0] for x in d["wire"]["waivers"]):
        if not d["wire"].get("desk", {}).get(m):
            rep.append(f"no desk aside for {m} in wire.desk (their transaction list will show none)")
    # pre-game and match of the week: everyone is 0-0
    for m in d["pre"] + [d["motw"]]:
        for k in ("a", "b"):
            if m[k] not in di:
                raise SystemExit(f"issue-{n}.json names {m[k]!r}, who is not in the league data")
        m["ar"] = m["br"] = "0-0"
    sched = (jload(S("schedule.json"), {}) or {}).get("1")
    if sched:
        want = {frozenset(g) for g in sched}
        got = [frozenset((m["a"], m["b"])) for m in d["pre"] + [d["motw"]]]
        for m in d["pre"] + [d["motw"]]:
            if frozenset((m["a"], m["b"])) not in want:
                rep.append(f'pre-game card {m["a"]} vs {m["b"]}: not a Week 1 matchup in this season schedule.json')
        for g in want - set(got):
            rep.append(f'Week 1 game with no pre-game card: {" vs ".join(sorted(g))}')
        if len(set(got)) != len(got):
            rep.append("pre-game cards repeat a matchup (the Match of the Week must not also be in 'pre')")
    else:
        rep.append("schedule.json has no Week 1 matchups, so pre-game cards were not checked")
    mo = d["motw"]
    f = lambda mg: (f'1.{di[mg]["slot"]:02d}', str(di[mg]["auto"]), str(di[mg]["pos"]["QB"]))
    mo["stats"] = [["Record", "0-0", "0-0"], ["Round 1 pick", f(mo["a"])[0], f(mo["b"])[0]],
                   ["Autopicks", f(mo["a"])[1], f(mo["b"])[1]], ["QBs drafted", f(mo["a"])[2], f(mo["b"])[2]]]
    d["meta"] = {"week": 0, "maxpf": ""}
    blob = json.dumps(d, ensure_ascii=False).replace("</", "<\\/")
    inject(path, "ISSUE-DATA", f'<script id="issue-data" type="application/json">{blob}</script>')
    inject(path, "MANAGERS", '<script id="managers-data" type="application/json">' + json.dumps(managers(), ensure_ascii=False).replace("</", "<\\/") + "</script>")
    for line in rep:
        print(f"  note (issue {n}): {line}")

def ipath(y, n):
    """Issue prose file: data/issues/<season>/issue-NN.json (the old flat data/issues/issue-NN.json still works until migrated)."""
    new = os.path.join(ROOT, f"data/issues/{y}/issue-{int(n):02d}.json")
    old = os.path.join(ROOT, f"data/issues/issue-{int(n):02d}.json")
    return new if os.path.exists(new) or not os.path.exists(old) else old

def issue_files():
    """Every issue prose file as (season, issue no, path), newest first. Also covers the old flat layout."""
    man = {i["no"]: int(i.get("year", 2026)) for i in manifest() if "year" in i}
    out = []
    for f in glob.glob(os.path.join(ROOT, "data/issues/*/issue-*.json")):
        m = re.search(r"issue-(\d+)\.json$", f)
        if m: out.append((int(os.path.basename(os.path.dirname(f))), int(m.group(1)), f))
    for f in glob.glob(os.path.join(ROOT, "data/issues/issue-*.json")):
        m = re.search(r"issue-(\d+)\.json$", f)
        if m and man.get(int(m.group(1))): out.append((man[int(m.group(1))], int(m.group(1)), f))
    return sorted(out, reverse=True)

def vol(season):
    """Volume number for a season (Volume 1 = the first season)."""
    return ss.volume(season)

def issue(n="04", y=2026):
    use(y)
    man = next(x for x in manifest() if x["no"] == int(n) and int(x["year"]) == int(y))
    if man.get("preseason"):
        return issue_pre(man, canon(json.load(open(ipath(y, n), encoding="utf-8"))), y, n)
    wk = man.get("wire_week") or man.get("standings_week")
    assert wk, f"issues.json needs wire_week for issue {n}"
    d = canon(json.load(open(ipath(y, n), encoding="utf-8")))
    render_page(man, d, y)
    rep = []
    win = man.get("tx_from")   # optional: only claims created AFTER these timestamps belong to this issue (retro issues)
    keep = (lambda x: (x.get("created") or 0) > win.get(x["type"], 0)) if win else None
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
    spent = defaultdict(int)
    if win:
        for t in txfeed():
            if t["week"] == wk and t["type"] != "trade" and keep(t):
                spent[t["manager"]] += t.get("bid") or 0
    chg = (lambda m: -spent[m]) if win else (lambda m: fb[wk][m] - fb[wk - 1][m])
    d["bank"] = [[m, f"${fb[wk][m]}", (lambda dl: "0" if not dl else f"+${dl}" if dl > 0 else f"-${-dl}")(chg(m)), notes.get(m, "")] for m in sorted(fb[wk], key=lambda m: (fb[wk][m], list(notes).index(m) if m in notes else 99))]
    d["standings"] = {"bank": d.pop("bank")}

    # wire
    d["wire"]["trades"] = wire_trades(d["wire"]["trades"], wk, rep)
    d["wire"]["waivers"] = wire_waivers(d["wire"]["waivers"], wk, rep, keep)
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
    sched = (jload(S("schedule.json"), {}) or {}).get(str(wk + 1))
    if sched:
        want = {frozenset(g) for g in sched}
        got = [frozenset((m["a"], m["b"])) for m in d["pre"] + [d["motw"]]]
        for m in d["pre"] + [d["motw"]]:
            if frozenset((m["a"], m["b"])) not in want:
                rep.append(f'pre-game card {m["a"]} vs {m["b"]}: not a Week {wk + 1} matchup in this season schedule.json')
        for g in want - set(got):
            rep.append(f'Week {wk + 1} game with no pre-game card: {" vs ".join(sorted(g))}')
        if len(set(got)) != len(got):
            rep.append("pre-game cards repeat a matchup (the Match of the Week must not also be in 'pre')")
    else:
        rep.append(f"schedule.json has no Week {wk + 1} matchups, so pre-game cards were not checked")
    mo = d["motw"]
    best = lambda mg: max(t["points"] for w in history for t in w["teams"] if t["manager"] == mg)
    avg = lambda mg: need(mg)["pf"] / (need(mg)["wins"] + need(mg)["losses"] + need(mg)["ties"])
    mo["stats"] = [["Record", mo["ar"], mo["br"]],
                   ["PF Rank", ordinal(rank_pf[mo["a"]]), ordinal(rank_pf[mo["b"]])],
                   ["Best Week", f"{best(mo['a']):.2f}", f"{best(mo['b']):.2f}"],
                   ["AVG PF", f"{avg(mo['a']):.1f}", f"{avg(mo['b']):.1f}"]]

    d["meta"] = {"week": wk, "maxpf": MAXPF_LONG if (int(y), int(n)) in EXPLAIN else ""}
    path = f"issues/{y}/issue-{n}/index.html"
    blob = json.dumps(d, ensure_ascii=False).replace("</", "<\\/")
    inject(path, "ISSUE-DATA", f'<script id="issue-data" type="application/json">{blob}</script>')
    inject(path, "MANAGERS", '<script id="managers-data" type="application/json">' + json.dumps(managers(), ensure_ascii=False).replace("</", "<\\/") + "</script>")
    for line in rep:
        print(f"  note (issue {n}): {line}")

def leaderboard():
    """Home-page leaderboard: a podium for the top three (the trophy is the rank, no '#1' text) and a danger zone for the bottom two."""
    rows = jload(S("standings.json"), [])
    def pod(r, cls, k, label):
        return (f'<div class="pd {cls}"><img class="tro" src="assets/trophy-{k}.webp" alt="{label}" width="132" height="240" loading="lazy">'
                f'<div class="pi">{av(r["manager"], 44)}<h3><a class="ml" href="managers/{r["manager"].lower()}/">{esc(r["manager"])}</a></h3><p>{esc(r["record"])} &middot; {r["pf"]:.1f} PF</p></div></div>')
    top = "".join(pod(r, c, k, l) for r, c, k, l in zip(rows[:3], ("p1", "p2", "p3"), ("gold", "silver", "bronze"), ("1st place", "2nd place", "3rd place")))
    low = "".join(f'<div class="lo"><img class="tro tt" src="assets/trophy-trash.webp" alt="Last place" width="132" height="240" loading="lazy">{av(r["manager"], 40)}<div><h3><a class="ml" href="managers/{r["manager"].lower()}/">{esc(r["manager"])}</a></h3><p>{esc(r["record"])} &middot; {r["pf"]:.1f} PF</p></div></div>' for r in rows[-2:])
    return f'<div class="lbx"><div class="podium">{top}</div><div class="dz"><h3 class="dzh">The Danger Zone</h3><div class="dzg">{low}</div></div></div>'

def transactions(m):
    i = next((x for x in m if x.get("web")), None)
    if not i:
        return ""
    fin = i.get("wire_week") or 1
    use(i["year"])
    d = canon(json.load(open(ipath(i["year"], i["no"]), encoding="utf-8")))
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

def settings():
    return jload("data/settings.json", {}) or {}

def _pt(v):
    """Point pill: green for +, red for -, grey for 0."""
    v = str(v); cls = "neg" if v[:1] in "-\u2212" else "zero" if v == "0" else "pos"
    return f'<span class="pt {cls}">{esc(v.replace("-", "\u2212"))}</span>'

def rules():
    """Rules & settings: league-specific rules, the at-a-glance tiles and the lineup, all from data + data/settings.json."""
    from collections import Counter
    st = settings()
    c = Counter((jload(S("league.json"), {}) or {}).get("roster_positions", []))
    nm = {"SUPER_FLEX": "SFLEX", "BN": "Bench"}
    cards = [("Rookie draft", f"{draft_year()} order by MAXPF (the best possible lineup each week, added up; Sleeper's Max PF), linear. Lowest MAXPF picks 1.01."), ("Trades", "Vetoes are on. The deadline is Week 13."), ("Payouts", "The playoff winner collects.")]
    out = '<div class="rl">' + "".join(f"<div><h3>{a}</h3><p>{b}</p></div>" for a, b in cards) + "</div>"
    if st.get("glance"):
        out += '<div class="setg">' + "".join(f'<div class="set-tile"><b>{esc(a)}</b><span>{esc(b)}</span><small>{esc(d)}</small></div>' for a, b, d in st["glance"]) + "</div>"
    if c:
        lab = lambda p, n: f'<span class="slot {"bn" if p == "BN" else "sf" if p == "SUPER_FLEX" else ""}"><b>{n if n > 1 else ""}{"&times;" if n > 1 else ""}</b>{nm.get(p, p)}</span>'
        out += '<div class="lineup"><h3 class="sub">Starting lineup</h3><div class="slots">' + "".join(lab(p, n) for p, n in c.items()) + "</div></div>"
    return out

def scoring():
    """Scoring section: category cards, the points-allowed ladder and the defense / special-teams lists."""
    st = settings()
    if not st.get("scoring"):
        return ""
    row = lambda r: f'<li><span>{esc(r[0])}{f"<small>{esc(r[2])}</small>" if len(r) > 2 and r[2] else ""}</span>{_pt(r[1])}</li>'
    cards = "".join(f'<div class="scc"><h3><i aria-hidden="true">{c["icon"]}</i>{esc(c["name"])}</h3><ul>{"".join(row(r) for r in c["rows"])}</ul></div>' for c in st["scoring"])
    df = st.get("defense", {})
    cls = lambda v: "n2" if v[:1] in "-\u2212" and "4" in v else "n1" if v[:1] in "-\u2212" else "z" if v == "0" else "p1" if v == "+1" else "p2" if v in ("+4", "+7") else "p3"
    lad = "".join(f'<div class="rung {cls(v)}"><small>{esc(a)}</small><b>{esc(v.replace("-", "\u2212"))}</b></div>' for a, v in df.get("ladder", []))
    d = ('<div class="scd"><div class="scd-h"><h3><i aria-hidden="true">&#128737;</i>Team defense</h3><p>Points allowed sets the floor. Every defense starts the week on the ladder.</p></div>'
         f'<div class="ladder" role="img" aria-label="Points allowed ladder">{lad}</div>'
         f'<div class="scd-g"><div><h4>Plays</h4><ul>{"".join(row(r) for r in df.get("plays", []))}</ul></div>'
         f'<div><h4>Special teams</h4><ul>{"".join(row(r) for r in df.get("special", []))}</ul></div></div></div>') if df else ""
    note = ""   # the kicker note is intentionally not shown on the home page
    return f'<div class="scg">{cards}</div>{d}{note}'

def manifest():
    return sorted(json.load(open(os.path.join(ROOT, "data/issues.json"), encoding="utf-8")), key=lambda i: (-int(i["year"]), -i["no"]))

def link(i):
    return f'issues/{i["year"]}/issue-{i["no"]:02d}/'

def home_blocks(m):
    i = m[0]
    p = os.path.join(ROOT, "index.html"); h = open(p, encoding="utf-8").read()
    pre = f"Volume {vol(i['year'])}, " if vol(i["year"]) else ""
    og = '<meta property="og:description" content="' + attr(f"{pre}Issue {i['no']}: {i.get('title', '')}. Out now.") + '">'
    h2, n = re.subn(r'<meta property="og:description" content="[^"]*">', lambda _: og, h, count=1)
    assert n == 1, "og:description tag missing in index.html"
    open(p, "w", encoding="utf-8").write(h2)
    inject("index.html", "TICKER", "".join(f"<span>{esc(x)}</span>" for x in i.get("ticker", [])))
    inject("index.html", "BANNER", f'<a class="banner" href="{link(i)}"><small>Latest &middot; Issue {i["no"]}</small><h2>{esc(i.get("banner", i.get("title", "")))}</h2><span class="btn">Read Issue {i["no"]}</span></a>')
    top, out = max(x["year"] for x in m), []
    for y in sorted({x["year"] for x in m}, reverse=True):
        its = [x for x in m if x["year"] == y]
        def tile(x):
            no = f"{x['no']:02d}"
            im = issue_img("tile", no, f"Issue {x['no']}", "", lazy=True)
            return f'<span class="no t">{im}</span>' if im else f'<span class="no">{x["no"]}</span>'
        rows = "".join(f'<div class="r">{tile(x)}<div><h3>Issue {x["no"]}</h3><p>{esc(x["weeks"])}</p></div><span class="go"><a href="{link(x)}">Read</a></span></div>' for x in its)
        out.append(f'<details class="yr"{" open" if y == top else ""}><summary>{f"Volume {vol(y)} &middot; " if vol(y) else ""}{y} <small>{len(its)} issues</small></summary>{rows}</details>')
    inject("index.html", "ARCHIVE", "\n".join(out))

if __name__ == "__main__":
    m = manifest()
    use(display_season())                      # standings and leaderboard: newest season with finished weeks
    inject("index.html", "LEADERBOARD", leaderboard())
    inject("index.html", "STANDINGS", standings())
    inject("index.html", "RULES", rules())
    inject("index.html", "SCORING", scoring())
    inject("index.html", "TX", transactions(m))   # highlights come from the newest issue's own season
    home_blocks(m)
    [issue(f'{x["no"]:02d}', x["year"]) for x in m]
    print("site built")
