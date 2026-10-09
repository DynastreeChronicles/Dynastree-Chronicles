#!/usr/bin/env python3
"""Values for the Draft & Trade Ledger from FantasyCalc snapshots. Run after pull_values.py and pull_player_stats.py, before build_ledger.py.

Reads   data/market/snapshots/*.json (saved by pull_values.py), every season's transactions.json, draft.json, draft_meta.json,
        data/stats/<season>.json (only for its "final" flag), data/ledger.json, standings.json (draft slots)
Writes  data/market/ledger_values.json
  trades: for every trade, per side, the value of what that side received (1) at the time of the trade and (2) in the latest pull.
  picks:  for every draft pick, the value at the time of the pick, then one value per review point. A review point is LOCKED the
          first time the run sees that NFL season final, and never changes after (the verdict is judged at that moment).
Nothing here is typed by hand. Trades or picks older than the first snapshot use an estimate (see market.py); those carry how != "snapshot"."""
import datetime, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import build_site as bs
import seasons as ss
import pick_grades as pg
import market as mk
from build_site import jload, ROOT

OUT = os.path.join(ROOT, "data", "market", "ledger_values.json")


def side_values(side, snap_then, snap_now, pb_then, pb_now, slot_of, next_year):
    assets = []
    for p in side.get("receives_players", []):
        a, b = snap_then.player(p["name"], p["pos"]), snap_now.player(p["name"], p["pos"])
        assets.append({"label": f'{p["name"]} ({p["pos"]})', "then": a[0] if a else 0, "now": b[0] if b else 0})
    for k in side.get("receives_picks", []):
        slot = slot_of.get(k["original_owner"]); nxt = int(k["season"]) == next_year
        a, la = pb_then.value(int(k["season"]), int(k["round"]), slot, nxt)
        b, lb = pb_now.value(int(k["season"]), int(k["round"]), slot, nxt)
        assets.append({"label": lb if b else la, "then": a["value"] if a else 0, "now": b["value"] if b else 0, "pick": True})
    return {"manager": side["manager"], "assets": assets, "then": sum(x["then"] for x in assets), "now": sum(x["now"] for x in assets),
            "faab": side.get("receives_faab") or 0}


def main():
    tl = mk.Timeline()
    if not tl.snaps:
        print("No FantasyCalc snapshots yet: ledger values skipped.")
        return
    reg = ss.load(); active = ss.active(reg) or max(reg)
    L = jload("data/ledger.json", {}) or {}
    try:
        prev = json.load(open(OUT, encoding="utf-8"))
    except Exception:
        prev = {}
    stats = {}
    for y in reg:
        s = jload(f"data/stats/{y}.json", None)
        if s:
            stats[str(y)] = s
    for y in range(min(int(k) for k in reg), int(active) + 4):   # seasons after the registry's last (a 3-season review reaches forward)
        s = jload(f"data/stats/{y}.json", None)
        if s:
            stats[str(y)] = s
    standings = jload(f"data/{active}/standings.json", []) or []
    slot_of = {r["manager"]: r.get("draft_pick") for r in standings}
    next_year = int(active) + 1
    latest = tl.latest; pb_now = latest.picks()
    out = {"generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
           "first_snapshot": tl.first.isoformat(), "latest_snapshot": latest.date.isoformat(), "trades": {}, "picks": {}}

    for y in sorted(reg):
        for tx in jload(f"data/{y}/transactions.json", []) or []:
            if tx.get("type") != "trade" or len(tx.get("sides", [])) != 2 or not tx.get("created"):
                continue
            d = datetime.datetime.fromtimestamp(tx["created"] / 1000, datetime.timezone.utc).date()
            snap, how, off = tl.at(d)
            pb_then = snap.picks()
            out["trades"][str(tx["id"])] = {"date": d.isoformat(), "how": how, "snap": snap.date.isoformat(),
                                            "sides": [side_values(sd, snap, latest, pb_then, pb_now, slot_of, next_year) for sd in tx["sides"]]}

    drafts = (L.get("drafts") or {}); G = L.get("grading") or {}
    for y in sorted(reg):
        picks = jload(f"data/{y}/draft.json", None)
        if not picks:
            continue
        meta = jload(f"data/{y}/draft_meta.json", {}) or {}
        dt = pg.pick_date(y, meta, drafts)
        snap, how, off = tl.at(dt)
        startup = bool((drafts.get(str(y)) or {}).get("startup"))
        ks = [1] if startup else (G.get("checkpoints_seasons") or [1, 2, 3])
        for p in picks:
            key = f'{y}:{p["r"]}.{p["s"]:02d}'
            v0 = snap.player(p["name"], p["pos"])
            old = ((prev.get("picks") or {}).get(key) or {}).get("cps") or {}
            rec = {"at": {"value": v0[0] if v0 else 0, "how": how, "snap": snap.date.isoformat(), "date": dt.isoformat()}, "cps": {}}
            cur = latest.player(p["name"], p["pos"])
            for k in ks:
                season = int(y) + k - 1
                if (old.get(str(k)) or {}).get("locked"):
                    rec["cps"][str(k)] = old[str(k)]; continue
                st = stats.get(str(season))
                if not st:
                    break
                cp = {"season": season, "value": cur[0] if cur else 0, "snap": latest.date.isoformat(), "locked": bool(st.get("final"))}
                rec["cps"][str(k)] = cp
                if not cp["locked"]:
                    break
            out["picks"][key] = rec
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(out, open(OUT, "w", encoding="utf-8"), separators=(",", ":"))
    locked = sum(1 for r in out["picks"].values() for c in r["cps"].values() if c["locked"])
    print(f'ledger values: {len(out["trades"])} trades, {len(out["picks"])} picks, {locked} review points locked, snapshots {out["first_snapshot"]} to {out["latest_snapshot"]}')


if __name__ == "__main__":
    main()
