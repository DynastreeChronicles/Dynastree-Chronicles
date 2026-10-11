#!/usr/bin/env python3
"""Trade suggestions for the Hypothetical Trade Machine. A Python port of js/finder.js (same lineup, window and value logic), run league-wide:
every team offers its surplus (bench players and picks) and the best deals with the other eleven are kept. make_brief.py puts the result in
brief.json > trade_finder so the hypothetical trades in an issue are realistic (a real need on one side, a sensible window for both, values within 10%)
instead of invented. Pure functions over a data dict; build_data() reads the repo. No network."""
import itertools, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import market as mk

POS = ["QB", "RB", "WR", "TE"]
LAB = {"contend": "contender", "retool": "retooling", "rebuild": "rebuilder"}
W = {"contend": (.30, .10), "retool": (.20, .20), "rebuild": (.10, .30)}


def build_data(jload, season):
    """The same shape js/finder.js uses: managers -> assets, picks, standing; plus the lineup slots."""
    P = jload(f"data/{season}/portfolio.json", {}) or {}
    idx = (jload("data/market/fantasycalc.json", {}) or {}).get("values") or []
    age_of, byname = {}, {}
    for v in idx:
        if v.get("pos") != "PICK" and v.get("age"):
            age_of[mk.vkey(v["name"], v["pos"])] = v["age"]; byname.setdefault(mk.norm(v["name"]), v["age"])
    stand = {r["manager"]: r["rank"] for r in (jload(f"data/{season}/standings.json", []) or [])}
    from collections import Counter
    pos = Counter((jload(f"data/{season}/league.json", {}) or {}).get("roster_positions", []))
    out = {}
    for m, t in (P.get("teams") or {}).items():
        items = [dict(k="p:" + mk.vkey(a["name"], a["pos"]), n=a["name"], p=a["pos"], v=a["value"], d=a["trend30"], out=bool(a.get("sidelined")),
                      age=age_of.get(mk.vkey(a["name"], a["pos"])) or byname.get(mk.norm(a["name"])) or 0, via="")
                 for a in (t.get("assets") or t.get("top") or [])]
        items += [dict(k="k:" + x["label"], n=x["label"], p="PICK", v=x["value"], d=x["trend30"], out=False, age=0, via=x.get("via") or "") for x in t.get("pick_list", [])]
        out[m] = {"items": sorted(items, key=lambda i: -i["v"]), "standing": stand.get(m)}
    return {"managers": out, "lineup": {k: pos.get(k, 0) for k in ("QB", "RB", "WR", "TE", "FLEX", "SUPER_FLEX")}}


def lineup(D, lst):
    L = D["lineup"]; avail = sorted((x for x in lst if x["p"] != "PICK" and not x["out"]), key=lambda x: -x["v"]); used = set(); starters = []
    def take(elig):
        for a in avail:
            if a["k"] not in used and a["p"] in elig:
                used.add(a["k"]); starters.append(a); return
    for p in POS:
        for _ in range(L.get(p, 0)): take([p])
    for _ in range(L.get("FLEX", 0)): take(["RB", "WR", "TE"])
    for _ in range(L.get("SUPER_FLEX", 0)): take(POS)
    return {"starters": starters, "total": sum(x["v"] for x in starters), "keys": used}


def modes(D):
    ms = list(D["managers"]); info = {}
    for m in ms:
        l = lineup(D, D["managers"][m]["items"]); w = sum(x["v"] for x in l["starters"]) or 1
        info[m] = {"lineup": l["total"], "age": sum((x["age"] or 26) * x["v"] for x in l["starters"]) / w}
    by = sorted(ms, key=lambda m: -info[m]["lineup"]); n = max(len(ms) - 1, 1)
    for m in ms:
        i = info[m]; lr = by.index(m) + 1; st = D["managers"][m]["standing"] or round((len(ms) + 1) / 2)
        s = .5 * ((len(ms) - lr) / n) + .3 * ((len(ms) - st) / n) + .2 * max(0, min((i["age"] - 24) / 6, 1))
        i.update(lineupRank=lr, standing=st, score=s, mode="contend" if s >= .6 else "rebuild" if s <= .4 else "retool")
    return info


def factor(mode, x):
    if x["p"] == "PICK":
        return 1.12 if mode == "rebuild" else .9 if mode == "contend" else 1
    a = x["age"] or 26
    if mode == "rebuild":
        return 1.15 if a <= 22 else 1.08 if a <= 24 else 1 if a <= 26 else .95 if a <= 27 else .88 if a <= 28 else .8 if a <= 29 else .7
    if mode == "contend":
        return .9 if a <= 22 else .96 if a <= 24 else 1 if a <= 27 else 1.04 if a <= 29 else 1.02
    return 1


def perceived(lst, mode):
    return sum(x["v"] * factor(mode, x) for x in lst)


def packages(pool):
    top = sorted(pool, key=lambda x: -x["v"]); out = [[x] for x in top]; t = top[:9]
    out += [[a, b] for a, b in itertools.combinations(t, 2)]
    if 3 <= len(top) <= 4: out.append(top[:])
    return out[:70]


def combos(pool, vO, tol):
    out = []
    for i, a in enumerate(pool):
        if abs(a["v"] - vO) / max(a["v"], vO) <= tol: out.append([a])
        for b in pool[i + 1:]:
            s = a["v"] + b["v"]
            if abs(s - vO) / max(s, vO) <= tol: out.append([a, b])
    return sorted(((c, sum(x["v"] for x in c)) for c in out), key=lambda cv: abs(cv[1] - vO))[:14]


def find(D, me, offer, tol=.10, want=(), picks=True, mode="auto", M=None):
    M = M or modes(D); want = set(want); mine = D["managers"][me]["items"]; base = lineup(D, mine); res = []
    me_mode = M[me]["mode"] if mode == "auto" else mode; picks_only = all(x["p"] == "PICK" for x in offer)
    pk = packages(offer)
    for T in D["managers"]:
        if T == me: continue
        theirs = D["managers"][T]["items"]; tb = lineup(D, theirs); tm = M[T]["mode"]
        returnable = [x for x in theirs if x["v"] > 0 and not x["out"] and (picks if x["p"] == "PICK" else (not want or x["p"] in want))]
        for O in pk:
            vO = sum(x["v"] for x in O)
            if vO <= 0: continue
            ok = {x["k"] for x in O}
            if tm == "contend" and lineup(D, theirs + O)["total"] - tb["total"] <= 0: continue
            for c, vR in combos(returnable, vO, tol):
                rk = {x["k"] for x in c}; t_after = lineup(D, [x for x in theirs if x["k"] not in rk] + O); net_t = t_after["total"] - tb["total"]
                perc_t = perceived(O, tm) - perceived(c, tm); perc_u = perceived(c, me_mode) - perceived(O, me_mode)
                if not (net_t > 0 or (tm != "contend" and perc_t >= .04 * vO)) or perc_t < -.03 * vO: continue
                u_after = lineup(D, [x for x in mine if x["k"] not in ok] + c); net_u = u_after["total"] - base["total"]
                if picks_only and me_mode == "contend" and net_u <= 0: continue
                fair = 1 - abs(vR - vO) / max(vR, vO) / tol; need_t = max(0, min(net_t / vO, .6)) / .6
                p_t = (max(-.1, min(perc_t / vO, .25)) + .1) / .35; u_s = max(-.5, min(net_u / vO, .5)) + .5; u_p = (max(-.1, min(perc_u / vO, .25)) + .1) / .35
                bonus = .08 if want and any(x["p"] in want for x in c) else 0; wn, wp = W[tm]
                res.append(dict(team=T, tm=tm, send=O, get=c, vO=vO, vR=vR, net_t=net_t, net_u=net_u, perc_t=perc_t,
                                t_enter=[x for x in t_after["starters"] if x["k"] not in tb["keys"]], t_out=[x for x in tb["starters"] if x["k"] not in t_after["keys"]],
                                score=.25 * fair + wn * need_t + wp * p_t + .15 * u_s + .10 * u_p + bonus))
    res.sort(key=lambda r: -r["score"]); out, per, seen = [], {}, set()
    for r in res:
        i = (r["team"], tuple(sorted(x["k"] for x in r["send"])), tuple(sorted(x["k"] for x in r["get"])))
        if i in seen or per.get(r["team"], 0) >= 2: continue
        if any(o["team"] == r["team"] and {s["k"] for s in o["send"]} & {s["k"] for s in r["send"]} for o in out): continue
        seen.add(i); per[r["team"]] = per.get(r["team"], 0) + 1; out.append(r)
        if len(out) >= 5: break
    return out


def issue_text(x):
    """An asset the way an issue file writes it: a player name, or "2027 1st-round pick" (plus "(from Name)" when the pick came from another team)."""
    if x["p"] != "PICK":
        return x["n"]
    k = mk.parse_pick(x["n"])
    base = f'{k[0]} {mk.ordinal(k[1])}-round pick' if k else x["n"]
    return base + (f' (from {x["via"]})' if x.get("via") else "")


def league_suggestions(D, limit=8):
    """Every team offers its bench players (value 1,500 or more, top 4) and picks (top 2); keep the best deal per pair of teams."""
    M = modes(D); cand = []
    for me, t in D["managers"].items():
        st = lineup(D, t["items"])["keys"]
        bench = [x for x in t["items"] if x["p"] != "PICK" and x["k"] not in st and x["v"] >= 1500 and not x["out"]][:4]
        pk = [x for x in t["items"] if x["p"] == "PICK" and x["v"] > 0][:2]
        if not bench and not pk: continue
        for r in find(D, me, bench + pk, M=M):
            cand.append((r["score"], me, r))
    cand.sort(key=lambda z: -z[0]); out, used, pairs = [], {}, set()
    for score, me, r in cand:
        pair = frozenset((me, r["team"]))
        if pair in pairs or used.get(me, 0) >= 2 or used.get(r["team"], 0) >= 2: continue
        pairs.add(pair); used[me] = used.get(me, 0) + 1; used[r["team"]] = used.get(r["team"], 0) + 1
        t = M[r["team"]]; u = M[me]
        why = []
        enter = [x for x in r["t_enter"] if any(s["k"] == x["k"] for s in r["send"])]
        if enter: why.append(f'{r["team"]} ({LAB[r["tm"]]}) would start {", ".join(x["n"] for x in enter)}, a {round(r["net_t"]):,} upgrade to their starting lineup.')
        else: why.append(f'{r["team"]} is a {LAB[r["tm"]]}: the deal fits their timeline, not their lineup.')
        why.append(f'{me} ({LAB[u["mode"]]}) {"gains" if r["net_u"] > 0 else "gives up"} {abs(round(r["net_u"])):,} in starting lineup value.')
        out.append({"a": me, "b": r["team"], "as": [issue_text(x) for x in r["send"]], "bs": [issue_text(x) for x in r["get"]],
                    "a_sends_value": round(r["vO"]), "b_sends_value": round(r["vR"]), "gap_pct": round(100 * abs(r["vO"] - r["vR"]) / max(r["vO"], r["vR"])),
                    "windows": {me: LAB[u["mode"]], r["team"]: LAB[r["tm"]]}, "why": why})
        if len(out) >= limit: break
    return out
