#!/usr/bin/env python3
"""Season registry and paths. One folder per season: data/2026/, data/2027/, ...

Shared across seasons (never inside a season folder):
    data/managers.json, data/issues.json, data/seasons.json, data/issues/<season>/, data/bios/, data/brief.json

Inside data/<season>/:
    league.json, standings.json, efficiency.json, transactions.json, schedule.json,
    draft.json, fut_cap.json, weeks/week-NN.json

data/seasons.json is the registry. Volume N = the Nth season. Example:
    {"2026": {"volume": 1, "league_id": "1389...", "status": "active"},
     "2027": {"volume": 2, "status": "active", "carry_from": "2026"}}
A season is CLOSED once its last issue ships: set "status": "closed" and "closed_at" to the release time of that
last issue (ISO, e.g. "2027-01-14T13:00:00Z"). A closed season is frozen: the pull never touches it again.
Anything that happens in Sleeper after closed_at belongs to the next season (its "carry_from" points back).

Run this file directly to migrate a legacy flat data/ folder into data/2026/ (safe to run any number of times).
"""
import glob, json, os, re, shutil
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, ".."))
DATA = os.path.join(ROOT, "data")
REG = os.path.join(DATA, "seasons.json")

# files that live inside a season folder (everything the pull writes, plus the two hand-kept season files)
SEASON_FILES = ["league.json", "standings.json", "efficiency.json", "transactions.json", "schedule.json", "draft.json", "fut_cap.json"]


def sdir(season, rel=""):
    return os.path.join(DATA, str(season), rel) if rel else os.path.join(DATA, str(season))


def srel(season, rel):
    """Repo-relative path (the form build_site.jload() takes)."""
    return f"data/{season}/{rel}"


def load():
    if os.path.exists(REG):
        return json.load(open(REG, encoding="utf-8"))
    return {}


def save(reg):
    os.makedirs(DATA, exist_ok=True)
    with open(REG, "w", encoding="utf-8") as f:
        json.dump(dict(sorted(reg.items())), f, indent=2)
        f.write("\n")


def to_ms(v):
    """closed_at as epoch milliseconds. Accepts ISO text, a date, or a number (seconds or milliseconds)."""
    if v in (None, ""):
        return None
    if isinstance(v, (int, float)):
        return int(v if v > 1e11 else v * 1000)
    s = str(v).strip().replace("Z", "+00:00")
    dt = datetime.fromisoformat(s)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return int(dt.timestamp() * 1000)


def is_closed(entry):
    return (entry or {}).get("status") == "closed"


def active(reg=None, persist=False):
    """The season being pulled right now: the newest season that is not closed.
    If every season is closed, open the next one (volume + 1) and remember that it carries over from the last."""
    reg = load() if reg is None else reg
    if not reg:
        return None
    open_ = [s for s in reg if not is_closed(reg[s])]
    if open_:
        return max(open_)
    last = max(reg)
    nxt = str(int(last) + 1)
    reg[nxt] = {"volume": reg[last].get("volume", len(reg)) + 1, "status": "active", "carry_from": last}
    if persist:
        save(reg)
    return nxt


def volume(season, reg=None):
    reg = load() if reg is None else reg
    return (reg.get(str(season)) or {}).get("volume") or (sorted(reg).index(str(season)) + 1 if str(season) in reg else None)


def has_data(season, rel="standings.json"):
    p = sdir(season, rel)
    if not os.path.exists(p):
        return False
    try:
        return bool(json.load(open(p, encoding="utf-8")))
    except Exception:
        return False


def latest_with_standings(reg=None):
    """Newest season whose standings.json has rows (what the home page leaderboard shows)."""
    reg = load() if reg is None else reg
    for s in sorted(reg, reverse=True):
        if has_data(s):
            return s
    return None


# ------------------------------------------------------------------ one-time migration
def migrate(season="2026"):
    """Move the legacy flat layout into data/<season>/. Idempotent: does nothing once data/<season>/ exists
    and no flat files are left. Prints what it moved."""
    moved = []
    os.makedirs(sdir(season), exist_ok=True)
    for name in SEASON_FILES:
        old, new = os.path.join(DATA, name), sdir(season, name)
        if os.path.exists(old):
            if os.path.exists(new):
                os.remove(old)          # the season copy wins; a stale flat copy is just leftovers
            else:
                shutil.move(old, new)
            moved.append(name)
    old_w, new_w = os.path.join(DATA, "weeks"), sdir(season, "weeks")
    if os.path.isdir(old_w):
        os.makedirs(new_w, exist_ok=True)
        for f in glob.glob(os.path.join(old_w, "*.json")):
            dst = os.path.join(new_w, os.path.basename(f))
            if os.path.exists(dst):
                os.remove(f)
            else:
                shutil.move(f, dst)
        shutil.rmtree(old_w, ignore_errors=True)
        moved.append("weeks/")
    # issue prose: data/issues/issue-NN.json -> data/issues/<year>/issue-NN.json (year from data/issues.json)
    man = {}
    p = os.path.join(DATA, "issues.json")
    if os.path.exists(p):
        man = {i["no"]: str(i.get("year", season)) for i in json.load(open(p, encoding="utf-8"))}
    for f in glob.glob(os.path.join(DATA, "issues", "issue-*.json")):
        m = re.search(r"issue-(\d+)\.json$", f)
        if not m:
            continue                      # issue-template.json stays where it is
        y = man.get(int(m.group(1)), season)
        dst = os.path.join(DATA, "issues", y, os.path.basename(f))
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        if os.path.exists(dst):
            os.remove(f)
        else:
            shutil.move(f, dst)
        moved.append(f"issues/{os.path.basename(f)} -> issues/{y}/")
    # registry
    reg = load()
    if season not in reg:
        lid = None
        lp = sdir(season, "league.json")
        if os.path.exists(lp):
            lid = json.load(open(lp, encoding="utf-8")).get("league_id")
        reg[season] = {"volume": 1, "status": "active", **({"league_id": lid} if lid else {})}
        save(reg)
        moved.append("seasons.json")
    print("migrate: " + (", ".join(moved) if moved else "nothing to move (already per-season)"))
    return moved


if __name__ == "__main__":
    migrate()
