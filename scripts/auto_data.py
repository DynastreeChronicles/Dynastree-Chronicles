#!/usr/bin/env python3
"""Everything that used to need its own hand-edited file now rides inside the issue JSON, and is merged here at build time.

  issue-NN.json  "rulings":  verdicts on EARLIER issues' bold predictions
                             [{"issue": 4, "i": 0, "result": "hit|miss|pending", "note": "...", "star": false}]
                             ("year" is optional; it defaults to the year of the issue that carries the ruling)
  issue-NN.json  "receipts": hot takes spotted in the chat log this issue
                             [{"who": "Handle", "text": "exact line", "context": "", "date": "", "tags": [],
                               "status": "pending|aged_well|aged_badly", "note": ""}]
  issue-NN.json  anything else in the file is unchanged.

Rules:
  * A later issue's ruling or receipt update overrides an earlier one for the same prediction / same take (same who + text).
  * data/history.json "predictions" and data/receipts.json "takes" still work as hand overrides / extras. A hand entry
    wins, except a hand "pending" never blocks a ruling that came in from an issue.
"""
import json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import build_site as bs


def _issues():
    """[(year, no, data)] for every issue file, oldest first."""
    return [(y, n, bs.canon(json.load(open(f, encoding="utf-8")))) for y, n, f in sorted(bs.issue_files(), key=lambda x: (x[0], x[1]))]


def rulings():
    """{ "2026-4-0": {"result", "note", "star"} } from every issue's `rulings`. Later issues win."""
    out = {}
    for y, n, d in _issues():
        for r in d.get("rulings") or []:
            try:
                key = f'{r.get("year", y)}-{int(r["issue"])}-{int(r["i"])}'
            except (KeyError, TypeError, ValueError):
                print(f"  note (issue {n}): a ruling is missing 'issue' or 'i' and was ignored")
                continue
            out[key] = {k: r[k] for k in ("result", "note", "star") if k in r}
    return out


def merged_predictions(H):
    """data/history.json predictions + issue rulings. Hand entries win unless they are still 'pending'."""
    out = dict(rulings())
    for k, v in ((H or {}).get("predictions") or {}).items():
        if k in out and (v or {}).get("result") in (None, "pending"):
            continue
        out[k] = v
    return out


def issue_receipts():
    """Hot takes carried by issues, de-duplicated on (who, text). The first issue that carried a take owns its source link;
    a later issue that repeats it can update its status and desk note."""
    seen, out = {}, []
    for y, n, d in _issues():
        for t in d.get("receipts") or []:
            if not t.get("text") or not t.get("who"):
                continue
            key = (re.sub(r"\W+", "", t["text"].lower()), t["who"])
            e = {"season": str(t.get("season", y)), "who": t["who"], "text": t["text"], "ctx": t.get("context", ""), "issue": n,
                 "desk": t.get("note", ""), "status": t.get("status", "pending"), "date": t.get("date", ""), "tags": t.get("tags") or []}
            if key in seen:
                old = seen[key]
                old["status"], old["desk"] = e["status"], e["desk"] or old["desk"]
                old["tags"] = e["tags"] or old["tags"]
                continue
            seen[key] = e
            out.append(e)
    return out
