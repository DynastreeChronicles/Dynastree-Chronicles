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
import io
import re
import json
import os
import sys
import time
import urllib.error
import urllib.request
from collections import defaultdict
from datetime import datetime, timezone

try:
    from PIL import Image          # pip install pillow (avatars are skipped without it)
except ImportError:
    Image = None

API = "https://api.sleeper.app/v1"
USERNAME = "StealingGas"
LEAGUE_NAME = "Dynastree"

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.normpath(os.path.join(HERE, "..", "data"))
CACHE = os.path.normpath(os.path.join(HERE, "..", ".cache"))

# MAXPF = Max PF = the points of each week's OPTIMAL lineup (the best legal lineup the
# roster could have started), summed over final weeks. This is the same idea as Sleeper's
# built-in "Max PF" and it is what orders the 2027 rookie draft (lowest MAXPF = 1.01).
#
# It is NOT starters + bench. That number is kept as `roster_points` for reference only.
#
# True  -> IR/taxi players may be used to build the optimal lineup
# False -> only players who were eligible to be started (IR/taxi excluded)
MAXPF_INCLUDE_RESERVE = False
MAXPF_DEFINITION = "optimal lineup points per week, summed (Sleeper Max PF)"

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
        pool = players if MAXPF_INCLUDE_RESERVE else list(startable)
        roster_pts = sum(pp.get(p, 0) for p in pool)       # starters + bench, reference only
        bench_pts = sum(pp.get(p, 0) for p in bench if p in startable)
        opt = optimal_lineup(slots, [(p, pp.get(p, 0)) for p in pool])
        opt = max(opt, points)  # never report optimal below actual
        maxpf = opt             # MAXPF is the optimal lineup, not the roster total

        o = opp.get(rid)
        result = None
        if o is not None:
            result = "W" if points > pts_by_rid[o] else "L" if points < pts_by_rid[o] else "T"

        teams.append({
            "roster_id": rid,
            "manager": rmeta[rid]["manager"],
            "points": round(points, 2),
            "maxpf": round(maxpf, 2),
            "roster_points": round(roster_pts, 2),
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


def build_standings(weeks, info):
    """weeks: FINAL weeks only. info: {roster_id: {"manager", "faab_remaining"}}.
    Rank = wins (ties count half), then points for. Movement compares with the previous final week."""
    def agg(ws):
        a = defaultdict(lambda: defaultdict(float))
        for wk in ws:
            for t in wk["teams"]:
                x = a[t["roster_id"]]
                x["pf"] += t["points"]; x["pa"] += t["opponent_points"] or 0; x["maxpf"] += t["maxpf"]
                x["w"] += t["result"] == "W"; x["l"] += t["result"] == "L"; x["t"] += t["result"] == "T"
        return a

    def ranks(a):
        order = sorted(a, key=lambda r: (-(a[r]["w"] + 0.5 * a[r]["t"]), -a[r]["pf"]))
        return {r: i + 1 for i, r in enumerate(order)}

    cur = agg(weeks)
    rk = ranks(cur)
    pk = ranks(agg(weeks[:-1])) if len(weeks) > 1 else rk
    rows = []
    for rid, a in cur.items():
        rows.append({
            "roster_id": rid, "manager": info[rid]["manager"],
            "record": f"{int(a['w'])}-{int(a['l'])}" + (f"-{int(a['t'])}" if a["t"] else ""),
            "wins": int(a["w"]), "losses": int(a["l"]), "ties": int(a["t"]),
            "pf": round(a["pf"], 2), "pa": round(a["pa"], 2), "maxpf": round(a["maxpf"], 2),
            "faab_remaining": info[rid]["faab_remaining"],
            "sleeper_maxpf": info[rid].get("sleeper_maxpf"),
            "rank": rk[rid], "prev_rank": pk[rid], "move": pk[rid] - rk[rid],
        })
    rows.sort(key=lambda r: r["rank"])
    by_maxpf = sorted(rows, key=lambda r: r["maxpf"])
    low = by_maxpf[0]["maxpf"] if by_maxpf else 0
    for pick, r in enumerate(by_maxpf, 1):  # lowest MAXPF = 1.01
        r["draft_pick"] = pick
        r["maxpf_gap_to_1_01"] = round(r["maxpf"] - low, 2)
    return rows


def check_against_sleeper(rows, final_weeks, state):
    """Compare our MAXPF with Sleeper's own Max PF. Sleeper may already include a week we do not
    treat as final yet, so a gap is a warning to look at, never a reason to stop the build."""
    bad = [r for r in rows if r.get("sleeper_maxpf") is not None and abs(r["sleeper_maxpf"] - r["maxpf"]) > 0.05]
    if not rows or all(r.get("sleeper_maxpf") is None for r in rows):
        print("MAXPF check: Sleeper returned no potential-points figure, nothing to compare")
        return
    if not bad:
        print("MAXPF check: matches Sleeper's Max PF for every manager")
        return
    print("MAXPF check: our number and Sleeper's differ (check the 1.01 order before publishing):")
    for r in sorted(bad, key=lambda r: r["draft_pick"]):
        print(f"  1.{r['draft_pick']:02d} {r['manager']:<18} ours {r['maxpf']:>8.2f}  sleeper {r['sleeper_maxpf']:>8.2f}  diff {r['sleeper_maxpf'] - r['maxpf']:+.2f}")


def build_schedule(lid, rmeta):
    """Every regular-season matchup Sleeper has, including weeks nobody has scored in yet.
    process_week() skips unplayed weeks, so without this the pre-game matchups would not be in data/."""
    out = {}
    for w in range(1, 19):
        try:
            ms = get(f"/league/{lid}/matchups/{w}")
        except Exception as ex:   # a missing week must never break the pull
            print(f"schedule: week {w} skipped ({ex})")
            continue
        pairs = defaultdict(list)
        for m in ms or []:
            if m.get("matchup_id") is not None:
                pairs[m["matchup_id"]].append(m["roster_id"])
        games = [[rmeta[a]["manager"], rmeta[b]["manager"]] for a, b in (sorted(ids) for ids in pairs.values() if len(ids) == 2)]
        if games:
            out[str(w)] = games
    return out


def dump(name, obj):
    path = os.path.join(OUT, name)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(obj, f, indent=2)


ROOT = os.path.normpath(os.path.join(HERE, ".."))
AV_DIR = os.path.join(ROOT, "assets", "avatars")
AV_SIZE = 96


def slug(name):
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or "manager"


def fetch_avatar(key, size=AV_SIZE):
    """Download one avatar (Sleeper id or full URL), centre-crop square, shrink, return WebP bytes."""
    url = key if key.startswith("http") else f"https://sleepercdn.com/avatars/{key}"
    req = urllib.request.Request(url, headers={"User-Agent": "dynastree-site"})
    with urllib.request.urlopen(req, timeout=60) as r:
        im = Image.open(io.BytesIO(r.read())).convert("RGBA")
    side = min(im.size)
    left, top = (im.width - side) // 2, (im.height - side) // 2
    im = im.crop((left, top, left + side, top + side)).resize((size, size), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "WEBP", quality=82, method=6)
    return buf.getvalue()


def sync_avatars(rmeta):
    """Write data/managers.json and assets/avatars/<manager>.webp. An image is only
    re-downloaded when the avatar id changes; managers with no avatar get initials on the site."""
    path = os.path.join(OUT, "managers.json")
    old = json.load(open(path)) if os.path.exists(path) else {}
    out = {}
    for m in rmeta.values():
        name, key = m["manager"], m.get("team_avatar") or m.get("avatar")
        prev = old.get(name, {})
        rel = f"assets/avatars/{slug(name)}.webp"
        have = os.path.exists(os.path.join(ROOT, rel))
        entry = {"team_name": m.get("team_name"), "avatar_id": key, "avatar": None}
        if key and prev.get("avatar_id") == key and have:
            entry["avatar"] = rel                                  # unchanged: skip the download
        elif key and Image is not None:
            try:
                os.makedirs(AV_DIR, exist_ok=True)
                with open(os.path.join(ROOT, rel), "wb") as f:
                    f.write(fetch_avatar(key))
                entry["avatar"] = rel
            except Exception as ex:
                print(f"  avatar for {name} failed ({ex}); will retry next run")
                entry["avatar_id"] = prev.get("avatar_id")        # forces a retry
                entry["avatar"] = rel if have else None
        elif key:
            print("  Pillow not installed, so avatars were skipped (pip install pillow)")
        out[name] = entry
    dump("managers.json", out)
    print(f"Avatars: {sum(1 for e in out.values() if e['avatar'])}/{len(out)} managers have an image")


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
            "avatar": u.get("avatar"),                                   # Sleeper avatar id
            "team_avatar": (u.get("metadata") or {}).get("avatar"),      # custom team avatar URL, if set
            "reserve": set(r.get("reserve") or []),
            "taxi": set(r.get("taxi") or []),
            "roster": r,
        }
        st = r.get("settings") or {}
        if "ppts" in st:   # Sleeper's own season "potential points" (Max PF)
            rmeta[r["roster_id"]]["sleeper_ppts"] = round(st["ppts"] + st.get("ppts_decimal", 0) / 100, 2)

    sync_avatars(rmeta)

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

    # Season rollups: only FINAL weeks count (an in-progress week must not show up as a loss)
    final_weeks = [w for w in weeks if w["final"]]
    agg = defaultdict(lambda: defaultdict(float))
    for wk in final_weeks:
        for t in wk["teams"]:
            a = agg[t["roster_id"]]
            a["pf"] += t["points"]
            a["optimal"] += t["optimal"]
            a["bench_points"] += t["bench_points"]
            a["left_on_bench"] += t["left_on_bench"]

    budget = (league.get("settings") or {}).get("waiver_budget", 0)
    info = {rid: {"manager": rmeta[rid]["manager"],
                  "sleeper_maxpf": rmeta[rid].get("sleeper_ppts"),
                  "faab_remaining": budget - (rmeta[rid]["roster"].get("settings") or {}).get("waiver_budget_used", 0)}
            for rid in rmeta}
    rows = build_standings(final_weeks, info)
    dump("standings.json", rows)
    check_against_sleeper(rows, final_weeks, state)

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

    dump("schedule.json", build_schedule(lid, rmeta))
    dump("transactions.json", build_transactions(lid, range(1, (max(played) if played else cur_week) + 1), rmeta))

    dump("league.json", {
        "league_id": lid, "name": league["name"], "season": season,
        "roster_positions": league["roster_positions"],
        "weeks_with_scores": played,
        "maxpf_includes_reserve": MAXPF_INCLUDE_RESERVE,
        "maxpf_definition": MAXPF_DEFINITION,
        "waiver_budget": budget,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    })
    print(f"Wrote JSON to {OUT}")


if __name__ == "__main__":
    main()
