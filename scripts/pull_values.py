#!/usr/bin/env python3
"""Market values + manager portfolios.

Pulls FantasyCalc's dynasty trade values (built from real trades on Sleeper and other platforms), keeps the top 1,000
players and picks as a live JSON index, then runs every roster in the league through it.

Writes:
    data/market/fantasycalc.json   the value index (shared, overwritten each run)
    data/<season>/portfolio.json   per-manager portfolio: value, position split, top assets, sidelined capital,
                                   30-day market move, status flag, and a snapshot history that grows every run

Run after sleeper_pull.py, before build_managers.py:   python scripts/pull_values.py
A closed season is frozen and skipped. Any failure leaves the existing files untouched (the Action step is
continue-on-error, and the manager pages simply skip the portfolio block when the file is missing)."""
import json, os, re, sys, urllib.error, urllib.parse, urllib.request
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import sleeper_pull as sp
import seasons as ss
import market as mk
from market import PickBook, ordinal

ROOT = os.path.normpath(os.path.join(HERE, ".."))
MARKET = os.path.join(ROOT, "data", "market")
FC = "https://api.fantasycalc.com/values/current"
TOP_N = 1000
SIDELINED = {"Out", "IR", "PUP", "Doubtful", "Sus"}   # Sleeper injury_status values that count as capital you cannot use

# League format, passed to FantasyCalc so values match THIS league (superflex, 12 teams, full PPR).
FORMAT = {"isDynasty": "true", "numQbs": 2, "numTeams": 12, "ppr": 1}

# Status rules. "Market move" = what the market did to the players you hold over 30 days (trade-neutral).
# "Sidelined" = share of your portfolio value sitting on IR/Out/PUP players.
CRASH_MOVE_PCT = -5.0
CRASH_SIDELINED_PCT = 25.0
CORRECTION_MOVE_PCT = -2.5
BULL_MOVE_PCT = 5.0
KEEP_SNAPSHOTS = 120


def fetch_index():
    url = FC + "?" + urllib.parse.urlencode(FORMAT)
    req = urllib.request.Request(url, headers={"User-Agent": "dynastree-chronicles/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        raw = json.load(r)
    rows = []
    for it in raw:
        p = it.get("player") or {}
        rows.append({
            "name": p.get("name"), "pos": p.get("position"), "team": p.get("maybeTeam"), "age": p.get("maybeAge"),
            "sleeper_id": p.get("sleeperId"), "value": it.get("value") or 0, "rank": it.get("overallRank"),
            "pos_rank": it.get("positionRank"), "trend30": it.get("trend30Day") or 0,
        })
    rows.sort(key=lambda x: x["rank"] or 10 ** 6)
    top = rows[:TOP_N]
    return top + [r for r in rows[TOP_N:] if r["pos"] == "PICK"]   # picks are always kept so no owned pick goes unvalued


def owned_picks(lid, rosters, season, draft_rounds):
    """Future picks per roster_id after trades. Sleeper's traded_picks lists only the ones that moved."""
    traded = sp.get(f"/league/{lid}/traded_picks")
    seasons = sorted({int(t["season"]) for t in traded} | {int(season) + 1, int(season) + 2})
    seasons = [s for s in seasons if s > int(season)]
    own = {r["roster_id"]: [] for r in rosters}
    moved = {(int(t["season"]), t["round"], t["roster_id"]): t["owner_id"] for t in traded}
    for s in seasons:
        for r in rosters:
            for rnd in range(1, draft_rounds + 1):
                holder = moved.get((s, rnd, r["roster_id"]), r["roster_id"])
                if holder in own:
                    own[holder].append({"season": s, "round": rnd, "from": r["roster_id"]})
    return own


def classify(move_pct, sidelined_pct):
    if move_pct <= CRASH_MOVE_PCT or sidelined_pct >= CRASH_SIDELINED_PCT:
        return "crash"
    if move_pct <= CORRECTION_MOVE_PCT:
        return "correction"
    if move_pct >= BULL_MOVE_PCT:
        return "bull"
    return "stable"


def main():
    index = fetch_index()
    now = datetime.now(timezone.utc)
    os.makedirs(MARKET, exist_ok=True)
    with open(os.path.join(MARKET, "fantasycalc.json"), "w", encoding="utf-8") as f:
        json.dump({"source": "FantasyCalc", "url": "https://www.fantasycalc.com", "format": FORMAT,
                   "fetched_at": now.isoformat(timespec="seconds"), "count": len(index), "values": index}, f, separators=(",", ":"))
    mk.save_snapshot(index, now.date().isoformat())   # dated copy: the ledger values trades and picks "as of" a date from these
    print(f"FantasyCalc: {len(index)} values, snapshot {now.date().isoformat()} saved")

    reg = ss.load()
    season = ss.active(reg)
    if not season or ss.is_closed(reg.get(season)):
        print("Season closed or missing: index and snapshot saved, portfolios left alone.")
        return
    lid = (reg.get(season) or {}).get("league_id")
    if not lid:
        print("No Sleeper league id for this season yet: nothing to value.")
        return

    by_sid = {str(v["sleeper_id"]): v for v in index if v.get("sleeper_id")}
    book = PickBook(index)
    print(f"FantasyCalc picks parsed: {len(book.by_tier) + len(book.by_slot)}")

    sp.PLAYERS = sp.load_players()
    users = {u["user_id"]: u["display_name"] for u in sp.get(f"/league/{lid}/users")}
    rosters = sp.get(f"/league/{lid}/rosters")
    league = sp.get(f"/league/{lid}")
    rounds = (league.get("settings") or {}).get("draft_rounds") or 4
    picks = owned_picks(lid, rosters, season, min(rounds, 5))
    try:
        slot_of = {r["roster_id"]: r.get("draft_pick") for r in json.load(open(os.path.join(ss.sdir(season), "standings.json"), encoding="utf-8"))}
    except Exception:
        slot_of = {}
    handle_of = {r["roster_id"]: users.get(r.get("owner_id"), f"roster {r['roster_id']}") for r in rosters}

    out_dir = ss.sdir(season); path = os.path.join(out_dir, "portfolio.json")
    try:
        prev = json.load(open(path, encoding="utf-8"))
    except Exception:
        prev = {}
    hist = prev.get("history") or []

    team = {}
    unmatched_picks = set()
    for r in rosters:
        mgr = users.get(r.get("owner_id"), f"roster {r['roster_id']}")
        reserve = set(r.get("reserve") or [])
        assets, total, sidelined, move, off_index = [], 0.0, 0.0, 0.0, 0
        for pid in r.get("players") or []:
            meta = sp.PLAYERS.get(str(pid)) or {}
            if meta.get("position") in (None, "DEF"):
                continue
            v = by_sid.get(str(pid))
            if not v:
                off_index += 1
                continue
            out = pid in reserve or (meta.get("injury_status") in SIDELINED)
            assets.append({"name": v["name"], "pos": v["pos"], "team": v["team"], "value": v["value"], "rank": v["rank"],
                           "trend30": v["trend30"], "sidelined": bool(out),
                           "status": "IR" if pid in reserve else (meta.get("injury_status") or "")})
            total += v["value"]; move += v["trend30"]
            if out:
                sidelined += v["value"]
        pick_val, pick_n, pick_list = 0.0, 0, []
        next_year = int(season) + 1
        for pk in picks.get(r["roster_id"], []):
            v, label = book.value(pk["season"], pk["round"], slot_of.get(pk["from"]), pk["season"] == next_year)
            if v:
                pick_val += v["value"]; pick_n += 1; move += v["trend30"]
            else:
                unmatched_picks.add(label)
            pick_list.append({"label": label, "season": pk["season"], "round": pk["round"],
                              "via": handle_of.get(pk["from"]) if pk["from"] != r["roster_id"] else None,
                              "value": v["value"] if v else 0, "trend30": v["trend30"] if v else 0})
        pick_list.sort(key=lambda x: (-x["value"], x["season"], x["round"]))
        grand = total + pick_val
        base = grand - move   # what the same holdings were worth 30 days ago
        move_pct = round(100 * move / base, 1) if base > 0 else 0.0
        sid_pct = round(100 * sidelined / grand, 1) if grand else 0.0
        by_pos = {}
        for a in assets:
            by_pos[a["pos"]] = by_pos.get(a["pos"], 0) + a["value"]
        by_pos["PICK"] = pick_val
        assets.sort(key=lambda a: -a["value"])
        team[mgr] = {"total": round(grand), "players": round(total), "picks": round(pick_val), "pick_count": pick_n,
                     "by_pos": {k: round(v) for k, v in by_pos.items() if v},
                     "move30": round(move), "move30_pct": move_pct, "sidelined": round(sidelined), "sidelined_pct": sid_pct,
                     "status": classify(move_pct, sid_pct), "top": assets[:6], "pick_list": pick_list,
                     "sidelined_players": [a for a in assets if a["sidelined"]][:5], "off_index": off_index}

    ranked = sorted(team, key=lambda m: -team[m]["total"])
    for i, m in enumerate(ranked, 1):
        team[m]["rank"] = i
    today = now.date().isoformat()
    # Wealth Index: one entry per finished NFL week, rewritten until the next week finishes, then frozen (movement compares with the week before).
    wk = 0
    wdir = os.path.join(out_dir, "weeks")
    for fn in (os.listdir(wdir) if os.path.isdir(wdir) else []):
        try:
            d = json.load(open(os.path.join(wdir, fn), encoding="utf-8"))
            if d.get("final"):
                wk = max(wk, int(d["week"]))
        except Exception:
            pass
    wpath = os.path.join(out_dir, "wealth.json")
    try:
        W = json.load(open(wpath, encoding="utf-8"))
    except Exception:
        W = {}
    W.setdefault("weeks", {})[str(wk)] = {"date": today, "teams": {m: {"roster": t["players"], "picks": t["picks"], "total": t["total"]} for m, t in team.items()}}
    W.update(season=season, source="FantasyCalc", format=FORMAT)
    json.dump(W, open(wpath, "w", encoding="utf-8"), indent=1)
    # Change since the last snapshot at least 5 days old (includes trades, unlike the 30-day market move).
    old = [h for h in hist if (now.date() - datetime.fromisoformat(h["date"]).date()).days >= 5]
    base = old[-1] if old else None
    for m, t in team.items():
        prev_total = (base or {}).get("totals", {}).get(m)
        t["since"] = base["date"] if prev_total is not None else None
        t["since_change"] = (t["total"] - prev_total) if prev_total is not None else None
    snap = {"date": today, "totals": {m: team[m]["total"] for m in team}}
    hist = [h for h in hist if h["date"] != today] + [snap]
    hist = hist[-KEEP_SNAPSHOTS:]

    with open(path, "w", encoding="utf-8") as f:
        json.dump({"season": season, "source": "FantasyCalc", "format": FORMAT, "generated_at": now.isoformat(timespec="seconds"),
                   "thresholds": {"crash_move_pct": CRASH_MOVE_PCT, "crash_sidelined_pct": CRASH_SIDELINED_PCT,
                                  "correction_move_pct": CORRECTION_MOVE_PCT, "bull_move_pct": BULL_MOVE_PCT},
                   "league_avg": round(sum(t["total"] for t in team.values()) / max(len(team), 1)),
                   "teams": team, "history": hist}, f, indent=1)
    print(f"Portfolio written for {len(team)} managers. Top: {ranked[0]} ({team[ranked[0]]['total']}).")
    if unmatched_picks:
        print(f"::warning::Picks with no FantasyCalc value (counted as 0): {sorted(unmatched_picks)[:6]}")


if __name__ == "__main__":
    try:
        main()
    except (urllib.error.URLError, TimeoutError) as ex:
        print(f"::warning::FantasyCalc or Sleeper did not answer ({ex}). Portfolio files left as they were.")
