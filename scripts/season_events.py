#!/usr/bin/env python3
"""Pure helpers for the things the pull used to leave to a person: reading a finished draft and a decided championship
out of Sleeper's JSON. No network here (sleeper_pull.py fetches, this file interprets), so it can be tested offline.

  draft_records(picks, rid_to_manager)   Sleeper /draft/<id>/picks      -> the rows data/<season>/draft.json holds
  draft_meta(draft)                      Sleeper /league/<id>/drafts[i] -> {"draft_id", "type", "completed_at", ...}
  championship(bracket, weeks, start, rid_to_manager)
                                         winners_bracket + our week files -> champion, runner-up, final score (or None)
"""
from datetime import datetime, timezone


def _iso(ms):
    return datetime.fromtimestamp(ms / 1000, timezone.utc).date().isoformat() if ms else None


def draft_records(picks, rid_to_manager):
    """One row per pick, shaped like the existing draft.json: r (round), s (pick within the round), m, name, pos, team, auto."""
    n = max(len(rid_to_manager), 1)
    out = []
    for p in sorted(picks or [], key=lambda p: p.get("pick_no") or 0):
        md = p.get("metadata") or {}
        name = f'{md.get("first_name", "")} {md.get("last_name", "")}'.strip()
        mgr = rid_to_manager.get(p.get("roster_id"))
        if not name or not mgr:
            continue
        out.append({"r": p["round"], "s": ((p["pick_no"] - 1) % n) + 1, "m": mgr, "name": name,
                    "pos": md.get("position") or "UNK", "team": md.get("team") or "FA", "auto": False})
    return out


def draft_meta(d):
    return {"draft_id": d.get("draft_id"), "type": d.get("type"), "status": d.get("status"),
            "rounds": (d.get("settings") or {}).get("rounds"),
            "started_at": _iso(d.get("start_time")), "completed_at": _iso(d.get("last_picked") or d.get("start_time"))}


def championship(bracket, weeks, start, rid_to_manager):
    """The champion once Sleeper's winners bracket has a winner for the placement-1 game.
    Final score is the two teams' points in the championship round; a two-week final is summed (the same pairing in
    consecutive weeks from the round's first week). Returns None until the bracket and those weeks are final."""
    fin = next((m for m in (bracket or []) if m.get("p") == 1), None)
    if not fin or not fin.get("w") or not fin.get("l"):
        return None
    champ, runner = rid_to_manager.get(fin["w"]), rid_to_manager.get(fin["l"])
    if not champ or not runner:
        return None
    first = int(start) + int(fin.get("r") or 1) - 1
    by_week = {w["week"]: w for w in weeks}
    pts_c = pts_r = 0.0
    used = []
    wk = first
    while wk in by_week:
        w = by_week[wk]
        t = next((x for x in w["teams"] if x["roster_id"] == fin["w"]), None)
        if not t or t.get("opponent") != runner:
            break
        if not w.get("final"):
            return None
        pts_c += t["points"]; pts_r += t["opponent_points"]; used.append(wk)
        wk += 1
    if not used:
        return None
    return {"champion": champ, "runner_up": runner, "final_score": [round(pts_c, 2), round(pts_r, 2)], "weeks": used}
