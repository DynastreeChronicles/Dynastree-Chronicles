#!/usr/bin/env python3
"""Write data/brief.json: ONE file with everything Claude needs to draft the next issue.
Run after sleeper_pull.py and build_site.py (the GitHub Action does this). Numbers only come from data/;
this file adds no new facts, it just gathers and summarises them so nobody has to share eight files."""
import json, os, sys
from datetime import datetime, timezone
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_site as bs
import auto_data as ad

def season_end(season):
    """Has Sleeper's bracket decided the champion? And does the season-review issue exist yet? (The pull closes the season
    on its own once both are true.)"""
    r = bs.jload(f"data/{season}/result.json", None)
    if not r:
        return {"decided": False}
    fin = bs.ss.final_issue(season)
    out = {"decided": True, "champion": r.get("champion"), "runner_up": r.get("runner_up"), "final_score": r.get("final_score"),
           "season_final_issue_published": bool(fin)}
    if not fin:
        out["action"] = ("The championship is decided. Write the season-review issue and set \"season_final\": true on its entry in "
                         "data/issues.json. The next pull then closes the volume and opens the next one by itself. "
                         "Also write the volume story for data/history.json (seasons.<year>.story) if it is still the placeholder.")
    return out


def unruled_predictions():
    """Bold predictions from earlier issues that no issue has ruled on yet. The next issue's `rulings` should settle them."""
    H = bs.jload("data/history.json", {}) or {}
    res = ad.merged_predictions(H)
    out = []
    for y, n, f in sorted(bs.issue_files(), key=lambda x: (x[0], x[1])):
        d = bs.canon(json.load(open(f, encoding="utf-8")))
        for i, b in enumerate(d.get("bold") or []):
            if (res.get(f"{y}-{n}-{i}") or {}).get("result", "pending") == "pending":
                out.append({"year": y, "issue": n, "i": i, "prediction": b[0], "context": b[1] if len(b) > 1 else ""})
    return out


def market_portfolios(season):
    """FantasyCalc portfolio standings for the brief: who is up, who is crashing, what is sitting on IR. Empty if the pull has not run."""
    P = bs.jload(f"data/{season}/portfolio.json", None)
    if not P or not P.get("teams"):
        return None
    teams = P["teams"]
    ranked = sorted(teams, key=lambda m: teams[m]["rank"])
    return {"source": P.get("source"), "as_of": (P.get("generated_at") or "")[:10], "league_avg": P.get("league_avg"),
            "how_to_read": ("Values are FantasyCalc dynasty trade values (superflex, 12 teams, full PPR). move30 = 30-day market move of the "
                            "players held now (trade-neutral). since_change = change since the snapshot dated `since` (includes trades). "
                            "sidelined = value on IR/Out/PUP. Status flags: crash, correction, stable, bull."),
            "crash_watch": [m for m in ranked if teams[m]["status"] == "crash"],
            "teams": [{"manager": m, "rank": teams[m]["rank"], "total": teams[m]["total"], "status": teams[m]["status"],
                       "move30": teams[m]["move30"], "move30_pct": teams[m]["move30_pct"],
                       "since": teams[m].get("since"), "since_change": teams[m].get("since_change"),
                       "sidelined": teams[m]["sidelined"], "sidelined_pct": teams[m]["sidelined_pct"],
                       "picks": teams[m]["picks"],
                       "top_assets": [f'{a["name"]} ({a["pos"]}) {a["value"]}' for a in teams[m]["top"][:3]],
                       "sidelined_players": [f'{a["name"]} ({a["status"] or "OUT"}) {a["value"]}' for a in teams[m]["sidelined_players"]]}
                      for m in ranked]}


def main():
    reg = bs.ss.load()
    season = bs.ss.active(reg) or bs.display_season()
    bs.use(season)                                    # brief is always about the ACTIVE season
    league = bs.jload(bs.S("league.json"), {})
    weeks = [w for n in league.get("weeks_with_scores", []) for w in [bs.load_week(n)] if w]
    final = [w["week"] for w in weeks if w["final"]]
    live = [w["week"] for w in weeks if not w["final"]]
    man = [i for i in bs.manifest() if str(i["year"]) == str(season)]   # this volume's issues, newest first
    latest = man[0] if man else None
    covered = {i.get("wire_week") for i in man if i.get("wire_week")}
    warn = []
    if not final:
        brief = {"generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"), "season": season,
                 "volume": bs.vol(season), "ready_for_new_issue": False, "phase": league.get("phase"),
                 "warnings": [f"Season {season} has no final weeks yet (phase: {league.get('phase')}). Offseason moves carried in: "
                              f"{sum(1 for t in bs.txfeed() if t['week'] == 0)}. The Volume {bs.vol(season)} opener is a look-forward issue, "
                              "written from the chat log plus transactions_offseason."],
                 "transactions_offseason": [t for t in bs.txfeed() if t["week"] == 0],
                 "market_portfolios": market_portfolios(season),
                 "latest_published_issue": man[0] if man else None, "league": league,
                 "managers": {k: v.get("team_name") for k, v in bs.managers().items() if v.get("active", True)},
                 "alumni": [k for k, v in bs.managers().items() if not v.get("active", True)],
                 "issue_template": bs.jload("data/issues/issue-template.json")}
        out = os.path.join(bs.ROOT, "data", "brief.json")
        json.dump(brief, open(out, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
        print(f"brief written (offseason, no final weeks yet): season {season}")
        return
    wk = max(final)
    ready = wk not in covered
    no = (latest["no"] + 1) if latest else 1
    nxt = ({"no": no, "wire_week": wk, "pre_week": wk + 1} if ready
           else {"no": no, "wire_week": wk + 1, "pre_week": wk + 2, "blocked_until": f"Week {wk + 1} is final"})
    if not ready:
        warn.append(f"Week {wk} is already covered by Issue {latest['no']}. Wait for Week {wk + 1} to go final (Tuesday after its Monday game) before drafting a new issue.")
    se = season_end(season)
    if se.get("action"):
        warn.append(se["action"])
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
    sched = (bs.jload(bs.S("schedule.json"), {}) or {}).get(str(wk + 1))
    rec = {r["manager"]: r["record"] for r in rows}
    if not sched:
        warn.append(f"schedule.json has no Week {wk + 1} matchups yet; pre-game cards need them from the chat log.")
    tx = [t for t in bs.txfeed() if t["week"] >= wk]
    prev_json = None
    if latest and latest.get("web"):
        prev_json = bs.canon(json.load(open(bs.ipath(season, latest["no"]), encoding="utf-8")))
    brief = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "season": season, "volume": bs.vol(season), "season_status": (reg.get(season) or {}).get("status"),
        "data_pulled_at": league.get("generated_at"),
        "ready_for_new_issue": ready,
        "warnings": warn,
        "next_issue": nxt,
        "season_end": se,
        "predictions_to_rule": unruled_predictions(),
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
        "market_portfolios": market_portfolios(season),
        "managers": {k: v.get("team_name") for k, v in bs.managers().items() if v.get("active", True)},
        "alumni": [k for k, v in bs.managers().items() if not v.get("active", True)],
        "league": {k: league.get(k) for k in ("league_id", "name", "season", "volume", "roster_positions", "waiver_budget")},
        "bios": {m: bs.jload(f"data/bios/{m}.json", {}) for m in bs.managers()},
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
