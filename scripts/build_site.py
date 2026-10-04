#!/usr/bin/env python3
"""Bake data into the HTML so pages never depend on a fetch() succeeding.
  - index.html: renders the standings table from data/standings.json
  - issues/2026/issue-04/index.html: embeds data/issues/issue-04.json
Run after sleeper_pull.py (the GitHub Action does this)."""
import json, os, re
ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
esc = lambda s: str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def inject(path, tag, html):
    p = os.path.join(ROOT, path)
    s = open(p, encoding="utf-8").read()
    pat = re.compile(rf"<!--{tag}-->.*?<!--/{tag}-->", re.S)
    assert pat.search(s), f"markers {tag} missing in {path}"
    open(p, "w", encoding="utf-8").write(pat.sub(lambda m: f"<!--{tag}-->\n{html}\n<!--/{tag}-->", s))

def standings():
    rows = json.load(open(os.path.join(ROOT, "data/standings.json")))
    league = json.load(open(os.path.join(ROOT, "data/league.json")))
    weeks = [w for w in league["weeks_with_scores"]]
    fin = rows and max(r["wins"] + r["losses"] + r["ties"] for r in rows)
    body = []
    for r in rows:
        m = r.get("move", 0)
        mv = f'<span class="up">&#9650; {m}</span>' if m > 0 else f'<span class="dn">&#9660; {-m}</span>' if m < 0 else '<span class="flat">&mdash;</span>'
        body.append(
            f'<tr data-rank="{r["rank"]}" data-draft="{r["draft_pick"]}"><td class="n">{r["rank"]}</td><td><b>{esc(r["manager"])}</b></td>'
            f'<td class="n">{esc(r["record"])}</td><td class="n mv">{mv}</td><td class="n">{r["pf"]:.2f}</td>'
            f'<td class="n">{r["maxpf"]:.2f}</td><td class="n">${r["faab_remaining"]}</td>'
            f'<td class="n pick">1.{r["draft_pick"]:02d}</td></tr>')
    head = ('<th class="n">#</th><th>Team</th><th class="n">W-L</th><th class="n">Move</th><th class="n">PF</th>'
            '<th class="n">MAXPF</th><th class="n">FAAB</th><th class="n">2027 pick</th>')
    return (f'<div class="sortbar" role="group" aria-label="Sort standings"><button class="chip on" data-sort="rank">Standings order</button>'
            f'<button class="chip" data-sort="draft">Draft order</button></div>'
            f'<div class="sc"><table id="standtable"><thead><tr>{head}</tr></thead><tbody>{"".join(body)}</tbody></table></div>'
            f'<p class="key">Records, PF and MAXPF through Week {fin} finals. Move = change in standings spots since the previous week. '
            f'MAXPF = every point your whole roster scored (starters + bench). 2027 pick: lowest MAXPF gets 1.01, highest gets 1.12. '
            f'FAAB is the current balance.</p>')

def issue(n="04"):
    d = open(os.path.join(ROOT, f"data/issues/issue-{n}.json"), encoding="utf-8").read()
    json.loads(d)
    d = json.dumps(json.loads(d), ensure_ascii=False).replace("</", "<\\/")
    inject(f"issues/2026/issue-{n}/index.html", "ISSUE-DATA", f'<script id="issue-data" type="application/json">{d}</script>')

def leaderboard():
    rows = json.load(open(os.path.join(ROOT, "data/standings.json")))
    pk = [("Top", r) for r in rows[:3]] + [("Bottom", r) for r in rows[-2:]]
    cards = "".join(f'<div class="{"hi" if k == "Top" else "lo"}"><small>{k}</small><b class="rk">#{r["rank"]}</b><h3>{esc(r["manager"])}</h3><p>{esc(r["record"])} &middot; {r["pf"]:.1f} PF</p></div>' for k, r in pk)
    return f'<div class="lb">{cards}</div><p class="key"><a href="#standings">Full standings below</a></p>'

def transactions():
    tx = sorted(json.load(open(os.path.join(ROOT, "data/transactions.json"))), key=lambda t: -(t.get("created") or 0))[:8]
    out = []
    for t in tx:
        if t["type"] == "trade":
            tag, txt = "Trade", " &harr; ".join(esc(s["manager"]) for s in t["sides"])
        else:
            tag = "Waiver"
            txt = f'<b>{esc(t["manager"])}</b> + {esc(t["added"]["name"])}' + (f' &minus; {esc(", ".join(t["dropped"]))}' if t["dropped"] else "") + (f' (${t["bid"]})' if t.get("bid") else "")
        out.append(f'<div class="tx"><span class="tg {tag.lower()}">{tag}</span><span>{txt}</span><small>Wk {t["week"]}</small></div>')
    return '<div class="txl">' + "".join(out) + '</div><p class="key"><a href="issues/2026/issue-04/#wire">Full wire and grades in the latest issue</a></p>'

def rules():
    from collections import Counter
    c = Counter(json.load(open(os.path.join(ROOT, "data/league.json")))["roster_positions"])
    nm = {"SUPER_FLEX": "SFLEX", "BN": "Bench"}
    lineup = ", ".join((f"{n}&times;" if n > 1 else "") + nm.get(p, p) for p, n in c.items())
    cards = [("Roster", lineup), ("Rookie draft", "2027 order by MAXPF, linear. Lowest MAXPF picks 1.01."), ("Trades", "Vetoes are on."), ("Payouts", "The playoff winner collects.")]
    return '<div class="rl">' + "".join(f"<div><h3>{a}</h3><p>{b}</p></div>" for a, b in cards) + "</div>"

if __name__ == "__main__":
    inject("index.html", "LEADERBOARD", leaderboard())
    inject("index.html", "TX", transactions())
    inject("index.html", "RULES", rules())
    inject("index.html", "STANDINGS", standings())
    issue("04")
    print("site built")
