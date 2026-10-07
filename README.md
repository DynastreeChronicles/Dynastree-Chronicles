# Dynastree Chronicles

The official newsletter of the DYNASTREE dynasty league: a 12-team, superflex dynasty league on Sleeper. Web only, one page per issue, plus manager pages, a Hall of Fame, a draft and trade ledger, and a receipts archive.

**Live site:** https://dynastreechronicles.github.io/Dynastree-Chronicles/

---

## Contents

1. [How this README and the master state file fit together](#1-how-this-readme-and-the-master-state-file-fit-together)
2. [How the site works](#2-how-the-site-works) (see also "Automation at a glance" above it)
3. [Repo map](#3-repo-map)
4. [The GitHub Action](#4-the-github-action)
5. [Build scripts](#5-build-scripts)
6. [What you upload and what you never touch](#6-what-you-upload-and-what-you-never-touch)
7. [Making an issue](#7-making-an-issue)
8. [Issue data](#8-issue-data)
9. [Seasons and volumes](#9-seasons-and-volumes)
10. [The pages](#10-the-pages)
11. [MAXPF](#11-maxpf)
12. [Trophies](#12-trophies-reserved-art)
13. [On-deck issue cards](#13-on-deck-issue-cards)
14. [Site conventions: accessibility, fonts, meta tags, privacy](#14-site-conventions)
15. [Adding a new page](#15-adding-a-new-page)
16. [Running it locally](#16-running-it-locally)
17. [Backups](#17-backups)
18. [If the site looks wrong](#18-if-the-site-looks-wrong)

---

## 1. How this README and the master state file fit together

There are two documents, and they have different jobs.

| File | Audience | Purpose |
|---|---|---|
| `README.md` (this file) | A person opening the repo | What the site is, how it is built, what each folder and script does, what to upload, how to fix problems. |
| `DYNASTREE_MASTER_STATE.md` | A fresh Claude chat (and you) | The operating manual for making each issue: the league's rules and identity, the voice, the issue JSON schema, sort laws, open storylines, the per-issue checklist. |

Rules for keeping them in step:

* **The master state file is the authority for anything about league content and the issue workflow** (rules, voice, schema, FUT CAP weights, steps for an issue). This README only summarises those and points to the matching master section.
* **This README is the authority for how the repo and the site are put together** (folders, scripts, the Action, conventions). The master state file keeps a shorter copy of the same facts in its sections 2, 3 and 6.
* **When code, the workflow, or a page changes, update both.** The master state file's section 14b lists exactly which sections to touch.
* If the two ever disagree, the code wins. Read the script, fix whichever document is wrong, and fix the other one in the same commit.

---

## Automation at a glance

* **Automatic on every Action run:** standings, records, MAXPF, manager pages, the Hall of Fame, the Ledger and its pick grades, Receipts, drafts, the champion, closing a season, and `brief.json`.
* **One bundle per issue (made in a Claude chat):** `issue-NN.json` (including `rulings` and `receipts`), the `data/issues.json` entry, `fut_cap.json`, and the 12 bios.
* **Once a year:** the volume `story` in `data/history.json`, and `"season_final": true` on the season-review issue.
* **By hand, rarely:** `data/settings.json` when league rules change, a hand verdict or trade obituary in `data/ledger.json`, a Toilet Bowl entry, and a rename the pull cannot match.

---

## 2. How the site works

Sleeper is the single source of truth for numbers. Nothing numeric is typed by hand. Words live in JSON files. Every page is generated, so never edit a generated HTML file: the next build overwrites it.

```
Sleeper API --scripts/sleeper_pull.py--> data/<season>/*.json (+ draft.json, draft_meta.json, result.json), data/managers.json, assets/avatars/   all numbers
data/ + data/issues/<season>/*.json  --scripts/build_site.py--> index.html + issues/<season>/issue-NN/index.html
data/ + data/bios/                   --scripts/build_managers.py--> managers/index.html + managers/<handle>/index.html
all seasons + data/history.json      --scripts/build_history.py--> history/index.html
Sleeper stats + projections         --scripts/pull_player_stats.py--> data/stats/<season>.json
draft + stats + data/ledger.json    --scripts/build_ledger.py (+ pick_grades.py)--> ledger/index.html   pick grades at 12/24/36 months
issue JSON (receipts, rulings)      --scripts/build_receipts.py, build_history.py (via auto_data.py)--> receipts/ and history/
all of the above                     --scripts/make_brief.py--> data/brief.json   (the one file shared with Claude)
chat log + master state + brief.json --Claude--> data/issues/<season>/issue-NN.json (incl. rulings + receipts) + data/issues.json + fut_cap + bios   all words
```

Two rules follow from this:

* **Numbers:** if a number looks wrong, the Sleeper data or the issue JSON is wrong or stale. Fix the source and rebuild. Never patch a number into prose.
* **Words:** prose lives only in the issue JSON, the bios, and the hand-entered files in section 6.

The data is baked into the HTML at build time, so pages do not depend on a fetch succeeding. Issue pages still use a small script (`js/issue.js`) to draw several sections from JSON that is embedded in the page (see section 14).

---

## 3. Repo map

```
.github/workflows/update-data.yml   the Action (section 4)
assets/                             images: crests, badges, trophies, grade art, avatars, issue cards (not in zips; large)
css/
  dynastree.css                     the stylesheet for every page
  managers.css, history.css,        extra styles, loaded only by the page that needs them
  ledger.css, receipts.css
  style.css                         legacy and unused; safe to delete
js/
  issue.js                          draws the dynamic sections of an issue page
  site.js                           home page icons and the standings sort toggle
  nav.js                            The Vault dropdown
data/
  seasons.json                      season registry: volume, league id, active or closed
  settings.json                     league settings shown on the home page
  managers.json                     everyone who has ever been in the league
  issues.json                       issue index: title, dek, banner, ticker, weeks
  history.json                      permanent league history (champions, prediction results, awards)
  ledger.json                       pick verdicts, trade obituaries, grading rules
  receipts.json                     extra hot takes for the Receipts page
  brief.json                        the one file shared with Claude (written by the Action)
  bios/<handle>.json                desk bio for each manager
  issues/<season>/issue-NN.json     all prose for one issue
  issues/issue-template.json        empty issue schema
  <season>/                         one folder per season: league, standings, efficiency, transactions,
                                    schedule, draft, fut_cap, weeks/week-NN.json
  stats/<season>.json               NFL stats used for auto-grading draft picks
scripts/                            the build (section 5)
  templates/issue.html              the shell every issue page is built from
index.html                          home page (shell + generated sections)
issues/<season>/issue-NN/           one generated page per issue
managers/                           the hub and one generated page per manager
history/  ledger/  receipts/        generated pages
DYNASTREE_MASTER_STATE.md           the operating manual (section 1)
```

The zip you share with Claude can leave out `assets/`; Claude never needs the images to change text, data, scripts, or styles. It just cannot check how art looks.

---

## 4. The GitHub Action

`.github/workflows/update-data.yml` ("Update league data") does all the work. You never run a script yourself.

**It runs:**

* Tuesday 11:00 UTC (after Monday Night Football) and Wednesday 13:00 UTC (after stat corrections).
* By hand: **Actions** > "Update league data" > **Run workflow**.
* Automatically on any push to `main` that touches `data/issues/**`, `data/issues.json`, `data/seasons.json`, `data/*/fut_cap.json`, `data/managers.json`, `data/settings.json`, `data/history.json`, `data/ledger.json`, `data/receipts.json`, `data/bios/**`, `scripts/**`, `css/**`, or `js/**`.

**Steps, in order:**

1. Check out the repo, set up Python 3.12, `pip install pillow` (used only for avatar images).
2. `sleeper_pull.py` (Sleeper data)
3. `build_site.py` (home and issue pages)
4. `build_managers.py` (manager pages)
5. `build_history.py` (Hall of Fame)
6. `pull_player_stats.py` (allowed to fail without failing the run)
7. `build_ledger.py` (ledger)
8. `build_receipts.py` (receipts)
9. `make_brief.py` (the one-file brief)
10. Commit `data/`, `index.html`, `issues/`, `managers/`, `history/`, `ledger/`, `receipts/` and `assets/avatars/` as `dynastree-bot`, then push.

**One run at a time.** The workflow has a `concurrency` group, so overlapping triggers queue instead of racing. If you upload files while the Tuesday run is mid-build, your upload's run waits its turn and then rebuilds with your files. A queued or "pending" run is normal, not an error. The commit step also pulls and retries the push up to three times, so a late upload cannot make the bot's push fail on its own. A push made by the bot does not trigger another run, so there is no loop.

**If a run goes red,** open the run, find the red step, and read its log. A red `Build ...` step means that script failed; the usual causes are invalid JSON, a handle typo, or a missing file.

---

## 5. Build scripts

All scripts run from the repo root, in the order below, and read only from `data/`.

| Script | Reads | Writes | Notes |
|---|---|---|---|
| `sleeper_pull.py` | Sleeper's public API | `data/<season>/*` (incl. `draft_meta.json`, `draft.json` when missing, `result.json` once the champion is decided), `data/managers.json`, `assets/avatars/*.webp`, and `data/seasons.json` when it closes a season | Finds the league by name; no league id needed. Prints the MAXPF check. Closes the season when the champion is decided and the review issue (`season_final`) exists. A missing league is a warning, not a failure. |
| `seasons.py` | `data/seasons.json` | (library) | Season registry and paths; migrates the old flat layout once. |
| `build_site.py` | `data/`, `scripts/templates/issue.html` | `index.html` (between its `<!--MARKER-->` comments), every `issues/<season>/issue-NN/index.html` | Prints `note (issue NN): ...` lines that flag mismatches between prose and data. |
| `build_managers.py` | `data/`, bios, issue JSON | `managers/` | Imports `build_site.py`, so it runs after it. |
| `build_history.py` | every season, `result.json`, `data/history.json`, `data/settings.json`, issue `rulings` | `history/index.html` | Permanent; never resets. |
| `trophies.py` | (library) | none | The single place that says which trophy means what. |
| `pull_player_stats.py` | Sleeper stats and projections | `data/stats/<season>.json` | Points, games, position rank and Sleeper's projected points for every drafted player. Network trouble, or no projections, is a warning. |
| `build_ledger.py` | draft, draft_meta, stats, `data/ledger.json`, issue JSON | `ledger/index.html` | Grades picks at 12/24/36 months through `pick_grades.py`. |
| `build_receipts.py` | issue JSON (`receipts`, `rulings`), `data/history.json`, `data/receipts.json` | `receipts/index.html` | |
| `make_brief.py` | everything above | `data/brief.json` | Adds no new facts; gathers and summarises, including `predictions_to_rule` and `season_end`. |
| `auto_data.py` | issue JSON | (library) | Merges each issue's `rulings` and `receipts` into History and Receipts. |
| `season_events.py` | Sleeper JSON | (library) | Reads a finished draft and a decided championship; no network, testable offline. |
| `pick_grades.py` | stats, draft dates | (library) | The 12/24/36-month pick grading rules. |

Every script has a docstring at the top that says what it does, what it reads, and where it writes.

---

## 6. What you upload and what you never touch

**Hand-written or Claude-written (you upload these):**

| File | What it is |
|---|---|
| `data/issues/<season>/issue-NN.json` | All prose for one issue. New each issue. |
| `data/issues.json` | The issue index. Replaced each issue. |
| `data/<season>/fut_cap.json` | Future-capital score per manager, recomputed each issue. |
| `data/bios/<handle>.json` | A manager's tagline, desk file, and per-season story. Normally all 12 each issue. |
| `data/history.json` | Optional now: the volume `story`, `awards` and `toilet_bowl` entries, hand prediction overrides. The champion and prediction results come from `result.json` and the issue files. |
| `data/ledger.json` | Grading thresholds, plus exceptions only: a hand verdict over an automatic grade, and trade obituaries. |
| `data/receipts.json` | Optional: extra hot takes added by hand. Normal hot takes ride in each issue file. |
| `data/settings.json`, `data/seasons.json`, `data/managers.json` | Edit only when a rule, season, or handle changes. |
| `css/`, `js/`, `scripts/` | Style and code. Claude will name the exact path for every file it changes. |
| `DYNASTREE_MASTER_STATE.md`, `README.md` | The two documents in section 1. |

**Written by the Action (never upload or edit):** `index.html` between its markers, `issues/`, `managers/`, `history/`, `ledger/`, `receipts/`, `data/brief.json`, `data/stats/`, `data/<season>/` (except `fut_cap.json`), and `assets/avatars/`.

When Claude changes site code, it hands back only the edited files and says where each one goes. Upload just those; do not re-upload the whole repo.

---

## 7. Making an issue

The full procedure is in `DYNASTREE_MASTER_STATE.md` sections 1, 3 and 4. In short:

1. Wait for the Tuesday or Wednesday Action run (or run it by hand) and check `data/brief.json` says `ready_for_new_issue: true`.
2. Start a Claude chat with the master state file, `brief.json`, and the new chat log.
3. Claude shows a data summary, you confirm, Claude returns the issue files and the updated master.
4. Upload the files to the paths Claude gives you, in one commit. The Action rebuilds the whole site, including every manager page.
5. Check the live site, then update the master state file's checklist (section 14).

---

## 8. Issue data

* `data/issues.json` lists the issues, newest first. `wire_week` is the post-game week; the pre-game week is `wire_week + 1`. Each entry needs `"year"`.
* `data/issues/<season>/issue-NN.json` is **prose only**: `desk`, `hero`, `zero`, headlines, takes, grades, projections, bold predictions, `wire.desk`, `bank.notes`, and `prev_motw`. The full schema is `DYNASTREE_MASTER_STATE.md` section 9; copy `data/issues/issue-template.json` to start one.
* Two bundled lists in the issue file replace separate uploads: **`rulings`** settles earlier issues' bold predictions (each `{issue, i, result, note}`; `brief.json` > `predictions_to_rule` lists what is open) and **`receipts`** carries hot takes from the chat log (each `{who, text, context, status, note}`). History and Receipts read them straight from every issue.
* Everything else on an issue page (standings, FAAB, draft slots, scores, records, bench points, MVPs, match-of-the-week stats, trade assets, waiver claims, bankroll) is computed at build time from `data/<season>/` as of the issue's week. The home page always shows the latest finished week.
* Waiver flags and one-liners live in `wire.waivers` as `{mgr, player, flag, note}`; the claims themselves come from Sleeper.
* Use exact handles everywhere (`C33DeezNutzz`, `fumbduckdumbfuck`, `CMac91`).
* **Renames:** add the old handle to `former_names` on the person's entry in `data/managers.json`. History stays attached and the old `managers/<old>/` address redirects. The pull detects most renames itself (same Sleeper user id) and prints `rename detected:`.

---

## 9. Seasons and volumes

Volume N is season N. Volume 1 is 2026. Issue numbers restart at 1 each volume.

* Each season has its own folder under `data/` (`data/2026/`, `data/2027/`, and so on). Prose is under `data/issues/<season>/`.
* `data/seasons.json` is the one switch. The newest season that is not `"closed"` is the active season; the pull, the brief and the issue workflow all use it. A closed season is frozen.
* **Closing a volume is automatic.** When Sleeper's winners bracket has a champion the pull writes `data/<season>/result.json`; History picks the champion, runner-up and score up from it. When the season-review issue is published with `"season_final": true` in its `data/issues.json` entry, the same run sets the season to `closed` with a `closed_at` timestamp, and the next pull opens the next volume. Only the volume `story` in `data/history.json` is hand-written (Claude does it once a year). The Toilet Bowl is not detected; add `toilet_bowl` to `data/history.json` by hand if you want it shown.
* Sleeper makes a new league id each season. The pull finds it by name. Until it exists, the pull keeps reading the old league and files anything after `closed_at` as week 0 (offseason) of the new season.
* The first issue of a new volume is the look-forward issue.

Details: `DYNASTREE_MASTER_STATE.md` sections 3b and 6c.

---

## 10. The pages

| Page | Address | Built by | What it shows |
|---|---|---|---|
| Home | `/` | `build_site.py` | Latest-issue banner, news ticker, leaderboard, standings (rank or draft order), archive, transactions, league rules and scoring. |
| Issue | `/issues/<season>/issue-NN/` | `build_site.py` + `js/issue.js` | One frozen issue: desk, hero and zero, standings, bankroll, transaction wire, post-game cards, drama, trade machine, pre-game cards, match of the week, bottom line, poll. |
| Managers | `/managers/` and `/managers/<handle>/` | `build_managers.py` | One page per manager: record, stat tiles, game log, transactions, desk quotes, bio, trophy case. Alumni keep their pages. |
| History | `/history/` | `build_history.py` | Hall of Fame: champions, all-time records, careers, award shelf, prediction ledger, timeline. |
| Ledger | `/ledger/` | `build_ledger.py` | Every draft pick and trade, with grades and blockbuster scores. |
| Receipts | `/receipts/` | `build_receipts.py` | Every quote, hit, bold prediction and hot take, with filters and a random-receipt button. |

Navigation: the sticky top bar has **Issues**, **The Vault** (a dropdown with Managers, History, Ledger, Receipts), **Standings**, **Transactions**, **Rules**, **Scoring**. Issue pages use their own section nav instead (Desk, Standings, Wire and so on). To add a page to The Vault, add a link to the `#vault` block in `index.html` and in every `build_*.py` shell (see section 15).

---

## 11. MAXPF

MAXPF is **Max PF: the points of each week's best possible lineup, added up over the season.** It matches Sleeper's own Max PF and is not "starters plus bench". The lowest MAXPF gets rookie pick 1.01 (linear order, not snake). The pull script prints a check against Sleeper's own figure on every run; if it lists a mismatch, look at the 1.01 order before publishing.

---

## 12. Trophies (reserved art)

Five trophies are reserved for one job each. They live in `assets/trophies/` and are mapped in `scripts/trophies.py`, the single place that says which trophy means what. Each has a full version and a `-sm` version for tight spots.

| Trophy | File | Used for |
|---|---|---|
| Lombardi Trophy | `lombardi` | League champion, once a year |
| Toilet Bowl Trophy | `toilet-bowl` | The Toilet Bowl (last-place bracket) |
| Best Manager (football with the rising arrow) | `best-manager` | Hall of Fame award shelf |
| Biggest Tank (deflated football, 1.01) | `biggest-tank` | Hall of Fame award shelf |
| Waiver Wire MVP (diamond) | `waiver-mvp` | Hall of Fame award shelf |

They are separate from the in-season rank trophies (`trophy-gold`, `-silver`, `-bronze`, `-trash`), which belong to the live standings and leaderboard. Do not use the five above for rank.

Where they appear:

* **History page, Champions wall:** Lombardi on each season's champion card. If a season has a `toilet_bowl` entry, a Toilet Bowl card follows it.
* **History page, Award shelf:** Best Manager, Biggest Tank and Waiver Wire MVP each show their own trophy.
* **Manager pages, Trophy case:** appears only once a manager has actually won something. Champion and Toilet Bowl come from `data/history.json`. The three awards count once their season is closed, or earlier if `history.json` names the winner by hand. A live season's current leader does not get the trophy early.

To show one anywhere new, call `trophies.img("lombardi", root)` (keys: `lombardi`, `toilet_bowl`, `best_manager`, `biggest_tank`, `waiver_mvp`) instead of writing the `<img>` by hand.

Recording a Toilet Bowl in `data/history.json`, next to the champion for that season:

```json
"2026": {
  "champion": "Handle", "runner_up": "Handle", "final_score": [131.4, 118.2],
  "toilet_bowl": {"winner": "Handle", "runner_up": "Handle", "final_score": [88.1, 71.5], "note": "Optional line."}
}
```

Only `winner` is required. `winner` is whoever takes the Toilet Bowl trophy.

---

## 13. On-deck issue cards

Cards for issues 18 to 36 are already in `assets/cards/` (`logo-NN.webp` is the crest "The Archive" card, `plain-NN.webp` is the number-only card). Nothing shows until that issue exists in `data/issues.json`. Then the build picks them up on its own:

* the **logo** card appears beside the issue title on the issue page;
* the **plain** card appears as the tile in the home page archive list.

Finished art always wins. If `assets/issue-card-NN.webp` or `assets/archive-issue-NN.webp` exists for an issue, it is used instead. To swap which style goes where, edit `CARD_STYLE` near the top of the issue-art helpers in `scripts/build_site.py`.

---

## 14. Site conventions

These apply to every page. Keep them when you change a shell.

**Accessibility**

* Every page starts with a **"Skip to main content" link** (`<a class="skip" href="#main">`), the first thing keyboard users reach. It is hidden until focused. The target is `<main class="wrap" id="main" tabindex="-1">`. Styles are at the end of `css/dynastree.css`.
* Keyboard focus is shown with the global `:focus-visible` outline in `css/dynastree.css`.
* Images carry `alt` text; decorative avatars use `alt=""`. Images have `width` and `height` set, and below-the-fold images use `loading="lazy"`.
* The ticker and live-dot animations stop when the visitor has reduced-motion turned on.
* The Vault dropdown is a real button with `aria-expanded`, and Escape closes it.

**Shared look**

* **Issue archive rows** (art tile, "Issue N: title", weeks, Read) come from one function, `archive_row()` in `scripts/build_site.py`, used by both the home page and the Hall of Fame issue index so the two always match. The whole row is a link and gets a green border on hover.
* **Manager handles** are bold green in "From the desk" (bolded at build time by `bold_handles()` in `build_site.py`) and in "The bottom line" (bolded in the browser by `bh()` in `js/issue.js`). Both use the exact handles from `data/managers.json`, so write handles exactly in prose; nicknames are not picked up. The colour is the `.art strong` rule in `css/dynastree.css`.
* **Section badges** (Post-Game, Trade Alert, Pre-Game) sit just left of the heading text; the rules are at the end of `css/dynastree.css`.
* **Manager stat tiles** are built by `stat_tiles()` in `scripts/build_managers.py` and styled at the end of `css/managers.css`. The Receipts manager dropdown is styled at the end of `css/receipts.css`.

**Pages that need JavaScript**

* On **issue pages**, the bankroll watch, transaction wire, post-game cards, drama, trade machine, pre-game cards, match of the week, bottom line and poll are drawn by `js/issue.js` from JSON embedded in the page. The hero, desk, hero and zero, and standings are plain HTML. With JavaScript off, a `<noscript>` note at the top of the page says so. If the script fails, `issue.js` shows a "failed to load" note. Both notes use the `.nojs` / `.loaderr` style.
* The home page, manager, history, ledger and receipts pages carry their content in HTML; scripts only add toggles, filters and the dropdown.

**Fonts**

* Inter (body) and Oswald (headings) load from Google Fonts. The link appears in `index.html`, `scripts/templates/issue.html`, and the font blocks of `build_managers.py`, `build_history.py`, `build_ledger.py` and `build_receipts.py`. To change a font, change all six.
* Self-hosting the fonts is optional. It would remove the one external request and the dependency on Google, but nothing is wrong with the current setup.

**Meta tags and privacy**

* Every page has `<meta name="robots" content="noindex">`, so search engines are asked to skip the site. It is a members-only newsletter. The site and the repo are still public, so anyone with a link can open them.
* Link previews use Open Graph tags in each page head.

---

## 15. Adding a new page

1. Write `scripts/build_<name>.py`. Copy the `shell()` function from an existing builder so you keep the skip link, `id="main"`, the nav, the footer and the scripts.
2. Add its stylesheet to `css/` if it needs one.
3. Add a step to the workflow, after the page it depends on, and add its output folder to the `git add -A` line in the commit step.
4. Add a link to the `#vault` block in `index.html` and in every `build_*.py` shell.
5. If it reads a new hand-edited data file, add that path to the workflow's push triggers.
6. Add it to the tables in section 10 here, and to the repo map and the matching section of `DYNASTREE_MASTER_STATE.md`.

---

## 16. Running it locally

You almost never need to. The Action does it. If you want to preview a change:

```
pip install pillow
python scripts/sleeper_pull.py
python scripts/build_site.py
python scripts/build_managers.py
python scripts/build_history.py
python scripts/pull_player_stats.py
python scripts/build_ledger.py
python scripts/build_receipts.py
python scripts/make_brief.py
```

Python 3.12. Pillow is only needed for avatars. Skip `sleeper_pull.py` and `pull_player_stats.py` to rebuild from the data already in the repo (they need internet). Serve the folder (`python -m http.server`) rather than opening files directly, so paths resolve.

---

## 17. Backups

Once a month, download a fresh zip (repo page > green **Code** button > **Download ZIP**) and keep it somewhere outside GitHub. If you leave out the large `assets/` folder from the zip you share with Claude, keep a separate copy of `assets/` too: the code and data cannot recreate the artwork.

---

## 18. If the site looks wrong

Open the **Actions** tab, click the latest "Update league data" run, and read the red step.

* **Nothing changed after an upload:** check the run exists. A waiting run is queued behind another one; give it a few minutes. If there is no run at all, the files you uploaded were not in the trigger list in section 4.
* **Invalid JSON:** a missing comma or quote. Paste the file into any JSON validator.
* **Handle typo:** the build prints `issue-NN.json names 'X', who is not in the league data`. Use the exact handle.
* **Numbers look wrong:** the data is stale. Run the Action by hand and check `data_pulled_at` in `data/brief.json`. Never patch a number into prose.
* **A manager page is missing or wrong:** read the "Build manager pages" step. It needs `scripts/build_managers.py`, `css/managers.css` and `data/managers.json`.
* **Style changes:** `css/dynastree.css` (site and issues) or the page's own stylesheet (`css/managers.css`, `history.css`, `ledger.css`, `receipts.css`).
* **Push failed in the Commit step:** it retries three times. If it still fails, run the Action again by hand.
