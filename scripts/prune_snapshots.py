#!/usr/bin/env python3
"""Thin out data/market/snapshots/ without changing any number the site shows. Run by the daily workflow after the new snapshot is saved.

Policy (all from data/settings.json > "snapshots", defaults shown):
  daily_days  60   keep every snapshot from the last 60 days
  older            keep the LAST snapshot of each calendar week
  always           keep the very first snapshot (the 30-day estimate for older events is built from it), the newest one, and the snapshot
                   nearest to every event the ledger values "as of" a date: each trade, each draft's pick date. Those are PINNED, so
                   a trade's "value at the time" and a pick's "value at the pick" can never shift because of pruning.
Issue values and review points are locked in their own files and do not read snapshots again, so they are unaffected.
Use --dry to see what would go without deleting anything."""
import datetime, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import build_site as bs
import seasons as ss
import pick_grades as pg
import market as mk
from build_site import jload


def event_dates():
    """Every date the ledger looks a value up for: trade dates and draft pick dates."""
    out = set()
    reg = ss.load()
    L = jload("data/ledger.json", {}) or {}
    for y in reg:
        for tx in jload(f"data/{y}/transactions.json", []) or []:
            if tx.get("type") == "trade" and tx.get("created"):
                out.add(datetime.datetime.fromtimestamp(tx["created"] / 1000, datetime.timezone.utc).date())
        if jload(f"data/{y}/draft.json", None):
            out.add(pg.pick_date(y, jload(f"data/{y}/draft_meta.json", {}) or {}, L.get("drafts")))
    return out


def plan(days, events, today, daily_days):
    """days: sorted list of snapshot dates. Returns (keep, drop) sets."""
    keep = {days[0], days[-1]}
    cutoff = today - datetime.timedelta(days=daily_days)
    weekly = {}
    for d in days:
        if d >= cutoff:
            keep.add(d)
        else:
            weekly[d.isocalendar()[:2]] = d      # last one of each week wins (days is sorted)
    keep.update(weekly.values())
    for e in events:
        keep.add(min(days, key=lambda d: (abs((d - e).days), d)))
    return keep, set(days) - keep


def main():
    dry = "--dry" in sys.argv
    cfg = (jload("data/settings.json", {}) or {}).get("snapshots") or {}
    daily_days = int(cfg.get("daily_days", 60))
    if not os.path.isdir(mk.SNAPDIR):
        print("No snapshots yet."); return
    days = sorted(datetime.date.fromisoformat(f[:-5]) for f in os.listdir(mk.SNAPDIR) if f.endswith(".json"))
    if len(days) < 3:
        print("Fewer than 3 snapshots: nothing to prune."); return
    keep, drop = plan(days, event_dates(), datetime.date.today(), daily_days)
    for d in sorted(drop):
        if not dry:
            os.remove(os.path.join(mk.SNAPDIR, f"{d.isoformat()}.json"))
    print(f"snapshots: {len(days)} on file, keeping {len(keep)}, {'would remove' if dry else 'removed'} {len(drop)} (daily for {daily_days} days, then weekly, plus pinned dates)")


if __name__ == "__main__":
    main()
