#!/usr/bin/env python3
"""Write data/brief.json: ONE file with everything Claude needs to draft the next issue.
Run after sleeper_pull.py and build_site.py (the GitHub Action does this). Numbers only come from data/;
this file adds no new facts, it just gathers and summarises them so nobody has to share eight files."""
import json, os, sys
from datetime import datetime, timezone
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_site as bs

def main():
    league = bs.jload("data/league.json", {})
    weeks = [w for n in league.get("weeks_with_scores", []) for w in [bs.load_week(n)] if w]
    final = [w["week"] for w in weeks if w["final"]]
    live = [w["week"] for w in weeks if not w["final"]]
    man = bs.manifest()                               # newest first
    latest = man[0] if man else None
    covered = {i.get("wire_week") for i in man if i.get("wire_week")}
    warn = []
    if not final:
        raise SystemExit("make_brief: no final weeks in data/, nothing to brief")
    wk = max(final)
    ready = wk not in covered
    no = (latest["no"] + 1) if latest else 1
    nxt = ({"no": no, "wire_week": wk, "pre_week": wk + 1} if ready
           else {"no": no, "wire_week": wk + 1, "pre_week": wk + 2, "blocked_until": f"Week {wk + 1} is final"})
    if not ready:
        warn.append(f"Week {wk} is already covered by Issue {latest['no']}. Wait for Week {wk + 1} to go final (Tuesday after its Monday game) before drafting a new issue.")
    if live:
        warn.append(f"Week {live[0]} is in progress (not final). It is excluded from records, standings and MAXPF.")

    rows = bs.asof(wk)
    fb = bs.faab_by_week(wk)
    bank = {m: {"faab": fb[wk][m], "change_this_week": fb[wk][m] - fb[wk - 1][m]} for m in fb[wk]}
    cur = bs.load_week(wk)["teams"]
    seen, games = set(), []
    for t in sorted(cur, key=lambda t: t["roster_id"]):
        k = frozenset((t["manager"], t["opponent"]))
        if k in seen:
            continue
        seen.add(k)
        o = next(x for x in cur if x["manager"] == t["opponent"])
        w, l = (t, o) if t["points"] >= o["points"] else (o, t)
        games.append({"winner": w["manager"], "winner_pts": w["points"], "loser": l["manager"], "loser_pts": l["points"],
                      "margin": round(w["points"] - l["points"], 2),
                      "winner_mvp": f'{w["mvp"]["name"]} {w["mvp"]["pts"]}', "loser_mvp": f'{l["mvp"]["name"]} {l["mvp"]["pts"]}',
                      "winner_bench": w["bench_points"], "loser_bench": l["bench_points"],
                      "winner_left_on_bench": w["left_on_bench"], "loser_left_on_bench": l["left_on_bench"]})
    perfect = [t["manager"] for t in cur if t["optimal"] and abs(t["points"] - t["optimal"]) < 0.005]
    top, low = max(cur, key=lambda t: t["points"]), min(cur, key=lambda t: t["points"])
    sched = (bs.jload("data/schedule.json", {}) or {}).get(str(wk + 1))
    rec = {r["manager"]: r["record"] for r in rows}
    if not sched:
        warn.append(f"data/schedule.json has no Week {wk + 1} matchups yet; pre-game cards need them from the chat log.")
    tx = [t for t in bs.txfeed() if t["week"] >= wk]
    prev_json = None
    if latest and latest.get("web"):
        prev_json = bs.jload(f"data/issues/issue-{latest['no']:02d}.json")
    brief = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "data_pulled_at": league.get("generated_at"),
        "ready_for_new_issue": ready,
        "warnings": warn,
        "next_issue": nxt,
        "final_weeks": final, "in_progress_weeks": live,
        "latest_published_issue": latest,
        "week_summary": {"week": wk, "games": games, "perfect_lineups": perfect,
                         "top_score": {"manager": top["manager"], "points": top["points"]},
                         "low_score": {"manager": low["manager"], "points": low["points"]},
                         "biggest_margin": max(games, key=lambda g: g["margin"]), "closest": min(games, key=lambda g: g["margin"])},
        "standings_after_week": rows,
        "bankroll": bank,
        "next_week_matchups": [{"a": a, "a_record": rec.get(a), "b": b, "b_record": rec.get(b)} for a, b in (sched or [])],
        "transactions_this_week_and_later": tx,
        "fut_cap": bs.jload("data/fut_cap.json", {}),
        "managers": {k: v.get("team_name") for k, v in bs.managers().items()},
        "league": {k: league.get(k) for k in ("league_id", "name", "season", "roster_positions", "waiver_budget")},
        "previous_issue_json": prev_json,
        "issue_template": bs.jload("data/issues/issue-template.json"),
    }
    out = os.path.join(bs.ROOT, "data", "brief.json")
    json.dump(brief, open(out, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print(f"brief written: ready={ready}, Issue {nxt['no']} = Week {nxt['wire_week']} post-game + Week {nxt['pre_week']} pre-game, {os.path.getsize(out)//1024} KB")
    for w in warn:
        print("  warning:", w)

if __name__ == "__main__":
    main()
