#!/usr/bin/env python3
"""
Pull Dynastree league data from Sleeper's public API and write JSON for the site.

- Stdlib only (no pip install needed, works in GitHub Actions as-is).
- Finds the league by Sleeper username + league name, so no league ID needed.
- Writes to ../data relative to this file (i.e. <repo>/data).

Usage:
    python scripts/sleeper_pull.py
    python scripts/sleeper_pull.py --season 2026
    LEAGUE_ID=123456789 python scripts/sleeper_pull.py     # skip the lookup
"""
import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from collections import defaultdict
from datetime import datetime, timezone

API = "https://api.sleeper.app/v1"
USERNAME = "StealingGas"
LEAGUE_NAME = "Dynastree"

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.normpath(os.path.join(HERE, "..", "data"))
CACHE = os.path.normpath(os.path.join(HERE, "..", ".cache"))

# MAXPF = total points scored by everyone on the roster that week (starters + bench).
# True  -> include IR/taxi players in the total
# False -> only count players who were eligible to be started
# Calibrate against the MAXPF column in Issue 4 and flip this if the numbers are off.
MAXPF_INCLUDE_RESERVE = True

SLOT_ELIGIBLE = {
    "QB": {"QB"}, "RB": {"RB"}, "WR": {"WR"}, "TE": {"TE"}, "K": {"K"}, "DEF": {"DEF"},
    "FLEX": {"RB", "WR", "TE"},
    "WRRB_FLEX": {"RB", "WR"},
    "REC_FLEX": {"WR", "TE"},
    "SUPER_FLEX": {"QB", "RB", "WR", "TE"},
    "DL": {"DL"}, "LB": {"LB"}, "DB": {"DB"},
    "IDP_FLEX": {"DL", "LB", "DB"},
}

PLAYERS = {}


def get(path):
    url = f"{API}{path}"
    for attempt in range(4):
        try:
            with urllib.request.urlopen(url, timeout=60) as r:
                return json.load(r)
        except (urllib.error.URLError, TimeoutError):
            if attempt == 3:
                raise
            time.sleep(2 ** attempt)


def load_players():
    """Sleeper asks for /players/nfl at most once a day, so cache it locally."""
    os.makedirs(CACHE, exist_ok=True)
    path = os.path.join(CACHE, "players.json")
    if os.path.exists(path) and time.time() - os.path.getmtime(path) < 86400:
        with open(path) as f:
            return json.load(f)
    data = get("/players/nfl")
    with open(path, "w") as f:
        json.dump(data, f)
    return data


def pinfo(pid):
    p = PLAYERS.get(str(pid)) or {}
    name = f"{p.get('first_name', '')} {p.get('last_name', '')}".strip() or str(pid)
    return name, p.get("position", "UNK"), p.get("team")


def find_league(season):
    if os.environ.get("LEAGUE_ID"):
        return get(f"/league/{os.environ['LEAGUE_ID']}")
    user = get(f"/user/{USERNAME}")
    leagues = get(f"/user/{user['user_id']}/leagues/nfl/{season}")
    want = LEAGUE_NAME.lower()
    hits = [l for l in leagues if l["name"].strip().lower() == want]
    hits = hits or [l for l in leagues if want in l["name"].lower()]
    if not hits:
        names = ", ".join(l["name"] for l in leagues) or "(none)"
        sys.exit(f"No league matching {LEAGUE_NAME!r} for {season}. Found: {names}")
    return hits[0]


def optimal_lineup(slots, pool):
    """pool: list of (pid, pts). Fill least-flexible slots first, best player each time."""
    order = sorted((s for s in slots if s in SLOT_ELIGIBLE), key=lambda s: len(SLOT_ELIGIBLE[s]))
    ranked = sorted(pool, key=lambda x: -x[1])
    used, total = set(), 0.0
    for s in order:
        for pid, pts in ranked:
            if pid not in used and pinfo(pid)[1] in SLOT_ELIGIBLE[s]:
                used.add(pid)
                total += pts
                break
    return total


def best_of(pids, pp):
    if not pids:
        return None
    pid = max(pids, key=lambda p: pp.get(p, 0))
    name, pos, team = pinfo(pid)
    return {"name": name, "pos": pos, "pts": round(pp.get(pid, 0), 2)}


def process_week(lid, week, rmeta, slots, final):
    ms = get(f"/league/{lid}/matchups/{week}")
    if not ms or all((m.get("points") or 0) == 0 for m in ms):
        return None

    pairs = defaultdict(list)
    for m in ms:
        if m.get("matchup_id") is not None:
            pairs[m["matchup_id"]].append(m["roster_id"])
    opp = {}
    for ids in pairs.values():
        if len(ids) == 2:
            opp[ids[0]], opp[ids[1]] = ids[1], ids[0]
    pts_by_rid = {m["roster_id"]: m.get("points") or 0 for m in ms}

    teams = []
    for m in ms:
        rid = m["roster_id"]
        pp = m.get("players_points") or {}
        starters = [s for s in (m.get("starters") or []) if s and s != "0"]
        players = list(m.get("players") or [])
        blocked = rmeta[rid]["reserve"] | rmeta[rid]["taxi"]
        startable = (set(players) - blocked) | set(starters)
        bench = [p for p in players if p not in set(starters)]

        points = m.get("points") or 0
        counted = players if MAXPF_INCLUDE_RESERVE else list(startable)
        maxpf = sum(pp.get(p, 0) for p in counted)
        bench_pts = sum(pp.get(p, 0) for p in bench if p in startable)
        opt = optimal_lineup(slots, [(p, pp.get(p, 0)) for p in startable])
        opt = max(opt, points)  # never report optimal below actual

        o = opp.get(rid)
        result = None
        if o is not None:
            result = "W" if points > pts_by_rid[o] else "L" if points < pts_by_rid[o] else "T"

        teams.append({
            "roster_id": rid,
            "manager": rmeta[rid]["manager"],
            "points": round(points, 2),
            "maxpf": round(maxpf, 2),
            "bench_points": round(bench_pts, 2),
            "optimal": round(opt, 2),
            "left_on_bench": round(opt - points, 2),
            "efficiency": round(100 * points / opt, 1) if opt else None,
            "mvp": best_of(starters, pp),
            "best_bench": best_of([p for p in bench if p in startable], pp),
            "opponent": rmeta[opp[rid]]["manager"] if rid in opp else None,
            "opponent_points": round(pts_by_rid[opp[rid]], 2) if rid in opp else None,
            "result": result,
        })
    return {"week": week, "final": final, "teams": teams}


def build_transactions(lid, weeks, rmeta):
    out = []
    mgr = lambda rid: rmeta[rid]["manager"] if rid in rmeta else f"roster {rid}"
    for w in weeks:
        for tx in get(f"/league/{lid}/transactions/{w}") or []:
            if tx.get("status") != "complete":
                continue
            adds = tx.get("adds") or {}
            drops = tx.get("drops") or {}
            base = {"week": w, "type": tx["type"], "created": tx.get("created")}
            if tx["type"] == "trade":
                picks = tx.get("draft_picks") or []
                faab = tx.get("waiver_budget") or []
                sides = []
                for rid in tx.get("roster_ids", []):
                    sides.append({
                        "manager": mgr(rid),
                        "receives_players": [dict(zip(("name", "pos", "team"), pinfo(p)))
                                             for p, r in adds.items() if r == rid],
                        "receives_picks": [
                            {"season": p["season"], "round": p["round"],
                             "original_owner": mgr(p["roster_id"])}
                            for p in picks if p["owner_id"] == rid],
                        "receives_faab": sum(f["amount"] for f in faab if f["receiver"] == rid),
                    })
                out.append({**base, "sides": sides})
            else:  # waiver / free_agent
                for pid, rid in adds.items():
                    dropped = [pinfo(p)[0] for p, r in drops.items() if r == rid]
                    out.append({
                        **base, "manager": mgr(rid),
                        "added": dict(zip(("name", "pos", "team"), pinfo(pid))),
                        "dropped": dropped,
                        "bid": (tx.get("settings") or {}).get("waiver_bid", 0)
                        if tx["type"] == "waiver" else 0,
                    })
    return out


def dump(name, obj):
    path = os.path.join(OUT, name)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(obj, f, indent=2)


def main():
    global PLAYERS
    ap = argparse.ArgumentParser()
    ap.add_argument("--season")
    args = ap.parse_args()

    state = get("/state/nfl")
    season = args.season or state["season"]
    league = find_league(season)
    lid = league["league_id"]
    league = get(f"/league/{lid}")  # full record (roster_positions, settings)
    print(f"League: {league['name']} ({lid}), season {season}")

    users = {u["user_id"]: u for u in get(f"/league/{lid}/users")}
    rosters = get(f"/league/{lid}/rosters")
    PLAYERS = load_players()

    rmeta = {}
    for r in rosters:
        u = users.get(r.get("owner_id"), {})
        rmeta[r["roster_id"]] = {
            "manager": u.get("display_name", f"roster {r['roster_id']}"),
            "team_name": (u.get("metadata") or {}).get("team_name"),
            "reserve": set(r.get("reserve") or []),
            "taxi": set(r.get("taxi") or []),
            "roster": r,
        }

    slots = [s for s in league["roster_positions"] if s != "BN"]
    cur_week = state.get("week", 1)
    in_season = state.get("season_type") == "regular"

    weeks = []
    for w in range(1, 19):
        final = (w < cur_week) or not in_season
        data = process_week(lid, w, rmeta, slots, final)
        if data is None:
            continue
        weeks.append(data)
        dump(f"weeks/week-{w:02d}.json", data)
    played = [x["week"] for x in weeks]
    print(f"Weeks with scores: {played}")

    # Season rollups
    agg = defaultdict(lambda: defaultdict(float))
    for wk in weeks:
        for t in wk["teams"]:
            a = agg[t["roster_id"]]
            a["pf"] += t["points"]
            a["pa"] += t["opponent_points"] or 0
            a["maxpf"] += t["maxpf"]
            a["optimal"] += t["optimal"]
            a["bench_points"] += t["bench_points"]
            a["left_on_bench"] += t["left_on_bench"]
            a["w"] += t["result"] == "W"
            a["l"] += t["result"] == "L"
            a["t"] += t["result"] == "T"

    budget = (league.get("settings") or {}).get("waiver_budget", 0)
    rows = []
    for rid, a in agg.items():
        rs = rmeta[rid]["roster"].get("settings") or {}
        rows.append({
            "roster_id": rid,
            "manager": rmeta[rid]["manager"],
            "record": f"{int(a['w'])}-{int(a['l'])}" + (f"-{int(a['t'])}" if a["t"] else ""),
            "wins": int(a["w"]), "losses": int(a["l"]), "ties": int(a["t"]),
            "pf": round(a["pf"], 2), "pa": round(a["pa"], 2),
            "maxpf": round(a["maxpf"], 2),
            "faab_remaining": budget - rs.get("waiver_budget_used", 0),
            "sleeper_record": f"{rs.get('wins', 0)}-{rs.get('losses', 0)}",
        })
    rows.sort(key=lambda r: (-r["wins"], -r["pf"]))
    for i, r in enumerate(rows, 1):
        r["rank"] = i
    by_maxpf = sorted(rows, key=lambda r: r["maxpf"])
    low = by_maxpf[0]["maxpf"] if by_maxpf else 0
    for pick, r in enumerate(by_maxpf, 1):
        r["draft_pick"] = pick
        r["maxpf_gap_to_1_01"] = round(r["maxpf"] - low, 2)
    dump("standings.json", rows)

    eff = []
    for rid, a in agg.items():
        eff.append({
            "manager": rmeta[rid]["manager"],
            "points": round(a["pf"], 2),
            "optimal": round(a["optimal"], 2),
            "efficiency": round(100 * a["pf"] / a["optimal"], 1) if a["optimal"] else None,
            "left_on_bench": round(a["left_on_bench"], 2),
            "bench_points": round(a["bench_points"], 2),
        })
    eff.sort(key=lambda r: -(r["efficiency"] or 0))
    dump("efficiency.json", eff)

    dump("transactions.json", build_transactions(lid, range(1, (max(played) if played else cur_week) + 1), rmeta))

    dump("league.json", {
        "league_id": lid, "name": league["name"], "season": season,
        "roster_positions": league["roster_positions"],
        "weeks_with_scores": played,
        "maxpf_includes_reserve": MAXPF_INCLUDE_RESERVE,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    })
    print(f"Wrote JSON to {OUT}")


if __name__ == "__main__":
    main()
