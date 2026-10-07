#!/usr/bin/env python3
"""Automatic draft-pick verdicts (hit / mid / bust), graded at 12, 24 and 36 months after the pick. Pure functions, no network.

For each checkpoint k (default 12, 24, 36 months):
  * It is DUE once today is that many months after the pick date AND the NFL season it judges has finished
    (the k-th season since the pick: pick year + k - 1).
  * Production grade: the player's position rank in that season, against the thresholds in data/ledger.json "grading"
    (hit = inside the "hit" rank for the position, mid = inside "mid", else bust; picks after "late_round" can't be busts).
  * Sleeper projection check: the player's actual points divided by the points Sleeper projected for the weeks he played.
    At or above "projection.over" (default 1.15) the grade moves up one step; at or below "projection.under" (default 0.70)
    it moves down one step. Missing projections just mean no nudge.
The verdict is the latest due checkpoint; after the last one it is final. Hand verdicts in data/ledger.json still override.
"""
import calendar
from datetime import date

STEPS = ["bust", "mid", "hit"]


def months_after(d, m):
    y, mo = divmod(d.month - 1 + m, 12)
    y, mo = d.year + y, mo + 1
    return date(y, mo, min(d.day, calendar.monthrange(y, mo)[1]))


def pick_date(year, meta=None, ledger_drafts=None):
    """When the pick was made: the draft's completion date from Sleeper (data/<year>/draft_meta.json), else a hand date in
    data/ledger.json drafts[year].date, else Sept 1 of the draft year."""
    for src in ((meta or {}).get("completed_at"), ((ledger_drafts or {}).get(str(year)) or {}).get("date")):
        try:
            if src:
                return date.fromisoformat(str(src)[:10])
        except ValueError:
            pass
    return date(int(year), 9, 1)


def base_grade(rank, pos, rnd, G):
    hit, mid = G.get("hit", {}), G.get("mid", {})
    if rank and rank <= hit[pos]:
        return "hit"
    if rank and rank <= mid.get(pos, 0):
        return "mid"
    return "mid" if rnd > G.get("late_round", 10) else "bust"


def nudge(grade, rec, rnd, G):
    """Apply the Sleeper-projection check. Returns (grade, ratio or None)."""
    proj, gp = rec.get("proj"), rec.get("gp") or 0
    P = G.get("projection") or {}
    if not proj or proj <= 0 or gp < P.get("min_games", 4):
        return grade, None
    ratio = (rec.get("pts") or 0) / proj
    i = STEPS.index(grade)
    if ratio >= P.get("over", 1.15):
        i = min(i + 1, 2)
    elif ratio <= P.get("under", 0.70):
        i = max(i - 1, 0)
    g = STEPS[i]
    if g == "bust" and rnd > G.get("late_round", 10):
        g = "mid"
    return g, round(ratio, 2)


def grade_pick(year, p, G, stats, today, pdate, key):
    """p: {"r","pos",...}. stats: {"2026": {"final", "players": {key: {"pts","gp","posrank","proj"}}}}.
    Returns {"grade", "final", "cps": [{"k","months","season","state","grade","posrank","ratio","due"}]}.
    state: "graded" (checkpoint reached), "waiting" (season is over, the month mark is not), "building" (season in progress)."""
    months = G.get("checkpoints_months") or [12, 24, 36]
    out = {"grade": None, "final": False, "cps": []}
    if p["pos"] not in G.get("hit", {}):
        return out
    graded = 0
    for k, m in enumerate(months, 1):
        season = int(year) + k - 1
        st = stats.get(str(season))
        rec = st and st["players"].get(key)
        if not rec:
            break
        due = months_after(pdate, m)
        cp = {"k": k, "months": m, "season": season, "posrank": rec.get("posrank"), "ratio": None, "due": due, "grade": None}
        if not st.get("final"):
            cp["state"] = "building"; out["cps"].append(cp); break
        if today < due:
            cp["state"] = "waiting"; out["cps"].append(cp); break
        g, ratio = nudge(base_grade(rec.get("posrank"), p["pos"], p["r"], G), rec, p["r"], G)
        cp.update(state="graded", grade=g, ratio=ratio)
        out["cps"].append(cp); out["grade"] = g; graded += 1
    out["final"] = graded == len(months)
    return out
