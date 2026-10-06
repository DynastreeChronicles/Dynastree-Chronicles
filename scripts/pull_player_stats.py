#!/usr/bin/env python3
"""Pull NFL season stats for every drafted player: data/stats/<season>.json. Feeds the Ledger's auto-grading.

For each draft year Y, seasons Y, Y+1, Y+2 are tracked (grading stops after season 3). A season file is rewritten on every
run until the NFL season is over (Jan 10 of the next year), then marked final and never touched again.
Points use the league's own scoring_settings from Sleeper (falls back to PPR). Network trouble is a warning, never a failed run."""
import glob, json, os, re, sys, urllib.request
from datetime import date
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import seasons as ss
API, ROOT = "https://api.sleeper.app/v1", ss.ROOT
POS = ("QB", "RB", "WR", "TE")

def get(path):
    with urllib.request.urlopen(urllib.request.Request(API + path, headers={"User-Agent": "dynastree-site"}), timeout=90) as r:
        return json.load(r)

def norm(n):
    return re.sub(r"\b(jr|sr|ii|iii|iv|v)\b", "", re.sub(r"[^a-z ]", "", n.lower().replace("-", " "))).split() and " ".join(re.sub(r"\b(jr|sr|ii|iii|iv|v)\b", "", re.sub(r"[^a-z ]", "", n.lower().replace("-", " "))).split())

def main():
    reg, today = ss.load(), date.today()
    drafts = {y: json.load(open(f, encoding="utf-8")) for y in reg for f in [os.path.join(ROOT, "data", y, "draft.json")] if os.path.exists(f)}
    if not drafts:
        print("player stats: no drafts yet"); return
    want = {}
    for d in drafts.values():
        for p in d: want[(norm(p["name"]), p["pos"])] = p["name"]
    seasons = sorted({int(y) + k for y in drafts for k in range(3) if date(int(y) + k, 9, 1) <= today})
    if not seasons:
        print("player stats: first season has not started"); return
    out_dir = os.path.join(ROOT, "data", "stats"); os.makedirs(out_dir, exist_ok=True)
    try:
        players = get("/players/nfl")
        lid = next((v.get("league_id") for v in reversed(list(reg.values())) if v.get("league_id")), None)
        scoring = (get(f"/league/{lid}").get("scoring_settings") or {}) if lid else {}
    except Exception as ex:
        print(f"::warning::player stats skipped, Sleeper did not answer ({ex})"); return
    ids = {}
    for pid, pl in players.items():
        if pl.get("position") in POS and pl.get("full_name") or pl.get("first_name"):
            nm = pl.get("full_name") or f'{pl.get("first_name", "")} {pl.get("last_name", "")}'
            ids.setdefault((norm(nm), pl.get("position")), pid)
    for s in seasons:
        path = os.path.join(out_dir, f"{s}.json")
        if os.path.exists(path) and json.load(open(path)).get("final"):
            continue
        tot, gp, weeks = {}, {}, 0
        try:
            for w in range(1, 19):
                wk = get(f"/stats/nfl/regular/{s}/{w}") or {}
                if not wk: continue
                weeks = w
                for pid, st in wk.items():
                    if (st.get("gp") or 0) < 1 and not st.get("pts_ppr"): continue
                    t = tot.setdefault(pid, {})
                    for k, v in st.items():
                        if isinstance(v, (int, float)): t[k] = t.get(k, 0) + v
                    gp[pid] = gp.get(pid, 0) + 1
        except Exception as ex:
            print(f"::warning::player stats {s} incomplete ({ex}); keeping the last good file"); continue
        if not weeks:
            print(f"player stats: no {s} stats yet"); continue
        pts = {pid: round(sum(t.get(k, 0) * v for k, v in scoring.items()) if scoring else t.get("pts_ppr", 0), 2) for pid, t in tot.items()}
        by_pos = {}
        for pid, v in pts.items():
            pos = (players.get(pid) or {}).get("position")
            if pos in POS and gp.get(pid, 0) > 0: by_pos.setdefault(pos, []).append((v, pid))
        rank = {pid: i + 1 for lst in by_pos.values() for i, (v, pid) in enumerate(sorted(lst, reverse=True))}
        rec, miss = {}, []
        for (n, pos), name in want.items():
            if pos not in POS: continue
            pid = ids.get((n, pos))
            if not pid: miss.append(name); continue
            rec[f"{n}|{pos}"] = {"pts": pts.get(pid, 0), "gp": gp.get(pid, 0), "posrank": rank.get(pid)}
        final = today >= date(s + 1, 1, 10)
        json.dump({"season": s, "final": final, "through_week": weeks, "scoring": "league" if scoring else "ppr", "players": rec},
                  open(path, "w"), separators=(",", ":"))
        print(f"player stats {s}: {len(rec)} players, through week {weeks}{', FINAL' if final else ''}" + (f"; unmatched: {', '.join(miss[:8])}" if miss else ""))

if __name__ == "__main__":
    main()
