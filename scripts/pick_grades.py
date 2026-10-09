#!/usr/bin/env python3
"""Automatic draft-pick verdicts (hit / mid / bust), judged after each season ends. Pure functions, no network.

CURRENT METHOD (grade_pick_value): FantasyCalc market value. A pick's value at the time of the pick is compared with its value at each
review point (the end of NFL season k). ratio = value at review point / max(value at pick, floor). At or above "value.over"
(default 1.15) = hit, at or below "value.under" (default 0.70) = bust, otherwise mid; a bust after "late_round" becomes mid. The floor
(default 500) keeps a pick that was near zero from looking like a miracle on a tiny gain. Values come from data/market/ledger_values.json
(scripts/ledger_values.py). The older production-based grader below (position rank + Sleeper projection) is kept for reference only.

Evaluations are per SEASON, not per calendar month:
  * Rookie drafts get a 1-season, 2-season and 3-season evaluation (season k = draft year + k - 1), each made once that
    NFL season is final.
  * The 2026 startup draft (data/ledger.json drafts.2026.startup = true) gets a single season-long evaluation: its first
    season, made after the season is finished and filed in the next volume's Issue 1.
  * Production grade: the player's position rank in that season, against the thresholds in data/ledger.json "grading"
    (hit = inside the "hit" rank for the position, mid = inside "mid", else bust; picks after "late_round" can't be busts).
  * Sleeper projection check: actual points divided by the points Sleeper projected for the weeks he played. At or above
    "projection.over" (default 1.15) the grade moves up one step; at or below "projection.under" (default 0.70) it moves
    down one step. Missing projections just mean no nudge.
The verdict is the latest finished evaluation; after the last one it is final. Hand verdicts in data/ledger.json still override.
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


def grade_pick(year, p, G, stats, key, n=None):
    """p: {"r","pos",...}. stats: {"2026": {"final", "players": {key: {"pts","gp","posrank","proj"}}}}.
    n: number of season evaluations (startup draft = 1); default G["checkpoints_seasons"] or [1, 2, 3].
    Returns {"grade", "final", "cps": [{"k","season","state","grade","posrank","ratio"}]}.
    state: "graded" (season final) or "building" (season in progress)."""
    ks = list(range(1, n + 1)) if n else (G.get("checkpoints_seasons") or [1, 2, 3])
    out = {"grade": None, "final": False, "cps": []}
    if p["pos"] not in G.get("hit", {}):
        return out
    graded = 0
    for k in ks:
        season = int(year) + k - 1
        st = stats.get(str(season))
        rec = st and st["players"].get(key)
        if not rec:
            break
        cp = {"k": k, "season": season, "posrank": rec.get("posrank"), "ratio": None, "grade": None}
        if not st.get("final"):
            cp["state"] = "building"; out["cps"].append(cp); break
        g, ratio = nudge(base_grade(rec.get("posrank"), p["pos"], p["r"], G), rec, p["r"], G)
        cp.update(state="graded", grade=g, ratio=ratio)
        out["cps"].append(cp); out["grade"] = g; graded += 1
    out["final"] = graded == len(ks)
    return out


def grade_pick_value(p, G, rec, n=None):
    """Value-based verdicts. p: {"r","pos",...}; rec: data/market/ledger_values.json picks[key] ({"at": {...}, "cps": {"1": {...}}}).
    Returns {"grade", "final", "at", "at_how", "cps": [{"k","season","state","grade","value","pct","ratio"}]}.
    state: "graded" (season final, value locked) or "building" (season in progress, live value, no grade yet)."""
    ks = list(range(1, n + 1)) if n else (G.get("checkpoints_seasons") or [1, 2, 3])
    out = {"grade": None, "final": False, "at": None, "at_how": None, "cps": []}
    if not rec or p["pos"] not in G.get("hit", {}):
        return out
    V = G.get("value") or {}
    over, under, floor = V.get("over", 1.15), V.get("under", 0.70), V.get("floor", 500)
    at = (rec.get("at") or {}).get("value") or 0
    out["at"], out["at_how"] = at, (rec.get("at") or {}).get("how")
    graded = 0
    for k in ks:
        cp = (rec.get("cps") or {}).get(str(k))
        if not cp:
            break
        ratio = cp["value"] / max(at, floor)
        item = {"k": k, "season": cp["season"], "value": cp["value"], "ratio": round(ratio, 2),
                "pct": round(100 * (cp["value"] / at - 1)) if at else None, "grade": None}
        if not cp.get("locked"):
            item["state"] = "building"; out["cps"].append(item); break
        g = "hit" if ratio >= over else "bust" if ratio <= under else "mid"
        if g == "bust" and p["r"] > G.get("late_round", 10):
            g = "mid"
        item.update(state="graded", grade=g)
        out["cps"].append(item); out["grade"] = g; graded += 1
    out["final"] = graded == len(ks)
    return out
