#!/usr/bin/env python3
"""The trophy registry. One place that says which trophy means what, so every page uses them the same way.

These seven trophies are RESERVED. They are not the in-season rank trophies (trophy-gold / silver / bronze / trash,
which belong to the live standings and leaderboard). They are only shown for the thing they stand for:

  lombardi      League champion, once a year. Champions wall and award shelf on the History page, and the winner's manager page.
  silver_cup    Silver Cup: the championship runner-up. Award shelf on the History page, and the manager page.
  apex_predator Apex Predator: highest regular-season PF. Award shelf on the History page, and the manager page.
  toilet_bowl   Toilet Bowl (last-place bracket). Champions wall and award shelf on the History page, and the winner's manager page.
  best_manager  Hall of Fame award shelf: Best Manager.
  biggest_tank  Hall of Fame award shelf: Biggest Tank (the 1.01).
  waiver_mvp    Hall of Fame award shelf: Waiver Wire MVP.

Files live in assets/trophies/<file>.webp (tall, 640 px) and <file>-sm.webp (240 px, for tight spots).
To show a trophy anywhere new, call trophies.img(key, root) rather than writing the <img> by hand.
"""
TROPHIES = {
    # key:          (file,           label,              what it is for,                 full (w, h),   small (w, h))
    "lombardi":     ("lombardi",     "Lombardi Trophy",  "League champion",              (351, 640),    (132, 240)),
    "toilet_bowl":  ("toilet-bowl",  "Toilet Bowl Trophy", "Toilet Bowl (last-place bracket)", (353, 640), (132, 240)),
    "silver_cup":   ("silver-cup",   "Silver Cup",       "Championship runner-up",       (356, 640),    (133, 240)),
    "apex_predator": ("apex-predator", "Apex Predator",  "Highest points scored (PF)",   (424, 640),    (159, 240)),
    "best_manager": ("best-manager", "Best Manager",     "Best Manager award",           (435, 640),    (163, 240)),
    "biggest_tank": ("biggest-tank", "Biggest Tank",     "Biggest Tank award",           (437, 640),    (164, 240)),
    "waiver_mvp":   ("waiver-mvp",   "Waiver Wire MVP",  "Waiver Wire MVP award",        (438, 640),    (164, 240)),
}
AWARD_KEYS = ("apex_predator", "best_manager", "biggest_tank", "waiver_mvp")   # derived from the numbers, each with its reserved trophy
SHELF_ORDER = ("lombardi", "silver_cup", "apex_predator", "best_manager", "toilet_bowl", "biggest_tank", "waiver_mvp", "bold_hit")   # award shelf: two rows of four
# Shown to people who earned them, in this order, on their manager page.
CASE_ORDER = ("lombardi", "silver_cup", "apex_predator", "toilet_bowl", "best_manager", "waiver_mvp", "biggest_tank")


def label(key):
    return TROPHIES[key][1]


def src(key, root, small=False):
    f = TROPHIES[key][0]
    return f"{root}assets/trophies/{f}{'-sm' if small else ''}.webp"


def img(key, root, cls="", small=False, alt=None, lazy=True):
    """The <img> tag for one trophy. root is the relative path back to the site root ("../", "../../", ...)."""
    f, lab, _, full, sm = TROPHIES[key]
    w, h = sm if small else full
    c = f' class="{cls}"' if cls else ""
    lz = ' loading="lazy"' if lazy else ""
    a = lab if alt is None else alt
    return f'<img{c} src="{src(key, root, small)}" alt="{a}" width="{w}" height="{h}"{lz}>'
