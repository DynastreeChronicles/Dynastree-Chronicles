#!/usr/bin/env python3
"""The trophy registry. One place that says which trophy means what, so every page uses them the same way.

These eleven trophies are RESERVED. They are not the in-season rank trophies (trophy-gold / silver / bronze / trash,
which belong to the live standings and leaderboard). They are only shown for the thing they stand for:

  lombardi      League champion, once a year. Champions wall and award shelf on the History page, and the winner's manager page.
  silver_cup    Silver Cup: the championship runner-up. Award shelf on the History page, and the manager page.
  apex_predator Apex Predator: highest regular-season PF. Award shelf on the History page, and the manager page.
  toilet_bowl   Toilet Bowl (last-place bracket). Champions wall and award shelf on the History page, and the winner's manager page.
  best_manager  Hall of Fame award shelf: Best Manager.
  biggest_tank  Hall of Fame award shelf: Biggest Tank (the 1.01).
  waiver_mvp    Hall of Fame award shelf: Waiver Wire MVP.
  best_draft_pick  Best Draft Pick: the highest-scoring player from the most recent draft (credited to the manager who picked him).
  the_shark        The Shark: trade of the year (largest FantasyCalc value gain for one side of a trade).
  punching_bag     The Punching Bag: highest regular-season points against (PA).
  quote_of_year    Quote of the Year: the desk's pick from the weekly Quotes of the Week.

The last four have NO ART YET. Until assets/trophies/<file>.webp and <file>-sm.webp exist, img() draws a dashed placeholder cup labelled
"Art coming soon". Drop the two files in (and fix the sizes in TROPHIES if they are not 480x640 / 180x240) and the real art replaces it, no other change.
Files live in assets/trophies/<file>.webp (tall, 640 px) and <file>-sm.webp (240 px, for tight spots).
To show a trophy anywhere new, call trophies.img(key, root) rather than writing the <img> by hand.
"""
import os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TROPHIES = {
    # key:          (file,           label,              what it is for,                 full (w, h),   small (w, h))
    "lombardi":     ("lombardi",     "Lombardi Trophy",  "League champion",              (351, 640),    (132, 240)),
    "toilet_bowl":  ("toilet-bowl",  "Toilet Bowl Trophy", "Toilet Bowl (last-place bracket)", (353, 640), (132, 240)),
    "silver_cup":   ("silver-cup",   "Silver Cup",       "Championship runner-up",       (480, 640),    (180, 240)),
    "apex_predator": ("apex-predator", "Apex Predator",  "Highest points scored (PF)",   (480, 640),    (180, 240)),
    "best_manager": ("best-manager", "Best Manager",     "Best Manager award",           (435, 640),    (163, 240)),
    "biggest_tank": ("biggest-tank", "Biggest Tank",     "Biggest Tank award",           (437, 640),    (164, 240)),
    "waiver_mvp":   ("waiver-mvp",   "Waiver Wire MVP",  "Waiver Wire MVP award",        (438, 640),    (164, 240)),
    "best_draft_pick": ("best-draft-pick", "Best Draft Pick", "Highest-scoring player from the most recent draft", (480, 640), (180, 240)),
    "the_shark":    ("the-shark",    "The Shark",        "Trade of the year",            (480, 640),    (180, 240)),
    "punching_bag": ("punching-bag", "The Punching Bag", "Highest points against (PA)",  (480, 640),    (180, 240)),
    "quote_of_year": ("quote-of-the-year", "Quote of the Year", "Best quote of the year", (480, 640),  (180, 240)),
}
AWARD_KEYS = ("apex_predator", "best_manager", "biggest_tank", "waiver_mvp", "best_draft_pick", "the_shark", "punching_bag", "quote_of_year")   # derived from the numbers, each with its reserved trophy
SHELF_ORDER = ("lombardi", "silver_cup", "apex_predator", "best_manager", "toilet_bowl", "biggest_tank", "waiver_mvp", "bold_hit",
               "best_draft_pick", "the_shark", "punching_bag", "quote_of_year")   # award shelf: three rows of four
# Shown to people who earned them, in this order, on their manager page.
CASE_ORDER = ("lombardi", "silver_cup", "apex_predator", "toilet_bowl", "best_manager", "waiver_mvp", "biggest_tank",
              "best_draft_pick", "the_shark", "punching_bag", "quote_of_year")


def label(key):
    return TROPHIES[key][1]


def src(key, root, small=False):
    f = TROPHIES[key][0]
    return f"{root}assets/trophies/{f}{'-sm' if small else ''}.webp"


def has_art(key):
    f = TROPHIES[key][0]
    return all(os.path.exists(os.path.join(ROOT, "assets", "trophies", f + sfx + ".webp")) for sfx in ("", "-sm"))


def placeholder(key, cls="", small=False, alt=None):
    """A dashed cup with 'Art coming soon', used until the real trophy files are added to assets/trophies/."""
    lab = TROPHIES[key][1]
    w, h = TROPHIES[key][4 if small else 3]
    c = f' class="{cls}"' if cls else ""
    a = (lab if alt is None else alt)
    return (f'<svg{c} xmlns="http://www.w3.org/2000/svg" role="img" aria-label="{a}" viewBox="0 0 480 640" width="{w}" height="{h}">'
            '<g fill="none" stroke="#5b6b86" stroke-width="10" stroke-dasharray="22 16" stroke-linecap="round" stroke-linejoin="round">'
            '<path d="M140 120H340V250C340 330 290 380 240 380C190 380 140 330 140 250Z"/>'
            '<path d="M140 160H100C100 260 130 285 152 290"/><path d="M340 160H380C380 260 350 285 328 290"/>'
            '<path d="M240 380V470"/><path d="M190 470H290V520H190Z"/><path d="M160 520H320"/></g>'
            '<text x="240" y="585" text-anchor="middle" fill="#5b6b86" font-family="Oswald,Arial Narrow,sans-serif" font-size="38" '
            'font-weight="600" letter-spacing="3">ART COMING SOON</text></svg>')


def img(key, root, cls="", small=False, alt=None, lazy=True):
    """The <img> tag for one trophy (or a placeholder while its art does not exist yet). root is the relative path back to the site root."""
    if not has_art(key):
        return placeholder(key, cls, small, alt)
    f, lab, _, full, sm = TROPHIES[key]
    w, h = sm if small else full
    c = f' class="{cls}"' if cls else ""
    lz = ' loading="lazy"' if lazy else ""
    a = lab if alt is None else alt
    return f'<img{c} src="{src(key, root, small)}" alt="{a}" width="{w}" height="{h}"{lz}>'
