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

if __name__ == "__main__":
    inject("index.html", "STANDINGS", standings())
    issue("04")
    print("site built")
