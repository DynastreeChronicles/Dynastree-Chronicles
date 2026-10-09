#!/usr/bin/env python3
"""FantasyCalc helpers shared by pull_values.py, ledger_values.py and the build scripts. Library only, no network.

FantasyCalc serves CURRENT values only, so the site saves a dated snapshot on every pull (data/market/snapshots/YYYY-MM-DD.json)
and looks values up "as of" a date from those. For dates before the first snapshot it makes an ESTIMATE: each snapshot carries
a 30-day trend, so (value - trend) approximates the value 30 days earlier. Anything older than that uses the earliest value on file.
Every lookup says which of these it used, so the pages can mark estimates with a ~."""
import json, os, re
from datetime import date, timedelta

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
SNAPDIR = os.path.join(ROOT, "data", "market", "snapshots")
EXACT_DAYS = 3        # a real snapshot within this many days counts as "at the time"


def norm(n):
    return " ".join(re.sub(r"\b(jr|sr|ii|iii|iv|v)\b", "", re.sub(r"[^a-z ]", "", (n or "").lower().replace("-", " "))).split())


def vkey(name, pos):
    return norm(name) + "|" + (pos or "")


def ordinal(n):
    return {1: "1st", 2: "2nd", 3: "3rd"}.get(n, f"{n}th")


# ---------------------------------------------------------------- picks
def parse_pick(name):
    """FantasyCalc lists picks as players with position PICK. Names look like "2027 1st (Mid)", "2028 2nd" or "2027 Pick 1.05".
    Returns (season, round, tier or None, slot or None); tier is Early, Mid or Late."""
    n = name or ""
    yr = re.search(r"(20\d\d)", n)
    slot = re.search(r"Pick\s+(\d+)\.(\d+)", n, re.I)
    rnd = re.search(r"(\d+)(?:st|nd|rd|th)\b", n, re.I)
    tier = re.search(r"\b(Early|Mid|Late)\b", n, re.I)
    if not yr or not (slot or rnd):
        return None
    return (int(yr.group(1)), int(slot.group(1)) if slot else int(rnd.group(1)),
            tier.group(1).capitalize() if tier else None, int(slot.group(2)) if slot else None)


def tier_for_slot(slot):
    """Draft slot 1 to 12 (1 = 1.01) to a FantasyCalc tier: 1-4 Early, 5-8 Mid, 9-12 Late."""
    return None if not slot else "Early" if slot <= 4 else "Mid" if slot <= 8 else "Late"


class PickBook:
    """rows: dicts with pos, name, value, trend30 (the PICK rows of an index or of a snapshot)."""
    def __init__(self, rows):
        self.by_tier, self.by_slot = {}, {}
        for v in rows:
            if v.get("pos") != "PICK":
                continue
            k = parse_pick(v.get("name"))
            if not k:
                continue
            season, rnd, tier, slot = k
            (self.by_slot if slot else self.by_tier)[(season, rnd, slot) if slot else (season, rnd, tier)] = v

    def count(self):
        return len(self.by_tier) + len(self.by_slot)

    def value(self, season, rnd, slot, next_draft):
        """Best FantasyCalc row for a pick, plus a label. The next draft uses the exact slot, then the tier from that slot;
        later drafts use FantasyCalc's untiered pick, then Mid, then the average of whatever tiers exist."""
        if next_draft and slot:
            v = self.by_slot.get((season, rnd, slot))
            if v:
                return v, v["name"]
            v = self.by_tier.get((season, rnd, tier_for_slot(slot)))
            if v:
                return v, v["name"]
        for t in (None, "Mid"):
            v = self.by_tier.get((season, rnd, t))
            if v:
                return v, v["name"]
        have = [x for (sn, r, t), x in self.by_tier.items() if sn == season and r == rnd]
        if have:
            avg = {"name": f"{season} {ordinal(rnd)}", "value": round(sum(x["value"] for x in have) / len(have)),
                   "trend30": round(sum(x["trend30"] for x in have) / len(have))}
            return avg, avg["name"]
        return None, f"{season} {ordinal(rnd)}"


# ---------------------------------------------------------------- snapshots
def save_snapshot(index, day):
    """index: rows from FantasyCalc (name, pos, value, trend30). One file per day; a second pull the same day replaces it."""
    os.makedirs(SNAPDIR, exist_ok=True)
    snap = {"date": day, "p": {}, "k": {}}
    for v in index:
        pair = [round(v.get("value") or 0), round(v.get("trend30") or 0)]
        if v.get("pos") == "PICK":
            snap["k"][v["name"]] = pair
        else:
            snap["p"][vkey(v["name"], v["pos"])] = pair
    with open(os.path.join(SNAPDIR, f"{day}.json"), "w", encoding="utf-8") as f:
        json.dump(snap, f, separators=(",", ":"))


def load_snapshots():
    out = []
    if os.path.isdir(SNAPDIR):
        for fn in sorted(os.listdir(SNAPDIR)):
            if fn.endswith(".json"):
                try:
                    out.append(json.load(open(os.path.join(SNAPDIR, fn), encoding="utf-8")))
                except Exception:
                    pass
    return out


class Snap:
    def __init__(self, raw, est=False):
        self.date = date.fromisoformat(raw["date"]); self.p, self.k, self.est = raw["p"], raw["k"], est
        self._byname = None

    def player(self, name, pos):
        """(value, trend30) or None. Falls back to the same name under another position (Sleeper and FantasyCalc sometimes differ)."""
        v = self.p.get(vkey(name, pos))
        if v is None:
            if self._byname is None:
                self._byname = {}
                for k, x in self.p.items():
                    self._byname.setdefault(k.split("|")[0], x)
            v = self._byname.get(norm(name))
        return v

    def picks(self):
        return PickBook({"pos": "PICK", "name": n, "value": v[0], "trend30": v[1]} for n, v in self.k.items())


class Timeline:
    def __init__(self, raws=None):
        raws = load_snapshots() if raws is None else raws
        self.snaps = [Snap(r) for r in raws]
        self.first = self.snaps[0].date if self.snaps else None
        self.latest = self.snaps[-1] if self.snaps else None
        self._cands = list(self.snaps)
        if self.snaps:   # estimated snapshot 30 days before the first real one
            f = raws[0]
            back = {"date": (self.first - timedelta(days=30)).isoformat(),
                    "p": {k: [v[0] - v[1], v[1]] for k, v in f["p"].items()},
                    "k": {k: [v[0] - v[1], v[1]] for k, v in f["k"].items()}}
            self._cands.insert(0, Snap(back, est=True))

    def at(self, d):
        """The snapshot nearest to date d: (Snap, how, days_off). how: "snapshot" (real, within 3 days), "estimate" (30-day trend
        back-cast) or "nearest" (the closest real snapshot, more than 3 days away). None when nothing is on file."""
        if not self._cands:
            return None
        best = min(self._cands, key=lambda s: abs((s.date - d).days))
        off = abs((best.date - d).days)
        how = "estimate" if best.est else "snapshot" if off <= EXACT_DAYS else "nearest"
        return best, how, off
