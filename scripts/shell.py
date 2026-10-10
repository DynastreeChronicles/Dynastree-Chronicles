#!/usr/bin/env python3
"""Shared page furniture: the sticky top bar (with its two dropdowns), the home-page tiles, and a plain page shell.
The top bar and the home-page tiles are built from the same two lists below, so a link added here shows up everywhere: on every page's
top bar, in both dropdowns, and on the home page. index.html gets them through the NAV and VAULT markers on each build_site run."""
VAULT = [("managers/", "Managers", "Meet the suspects"),
         ("history/", "History", "Hall of Fame &amp; records"),
         ("ledger/", "Ledger", "Drafts &amp; blockbusters"),
         ("receipts/", "Receipts", "Hot takes on file")]
RESEARCH = [("market/", "The Market", "Portfolio values &amp; trends"),
            ("market/#calculator", "Trade Calculator", "Test a deal before you send it"),
            ("rules/", "Rules", "League settings"),
            ("scoring/", "Scoring", "Every point, every position")]

FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
         '<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Oswald:wght@500;600;700&display=swap" rel="stylesheet">')


def _menu(R, ident, items):
    links = "".join(f'<a href="{R}{h}"><b>{t}</b><small>{s}</small></a>' for h, t, s in items)
    return f'<div class="ddm" id="{ident}" hidden>{links}</div>'


def nav(R=""):
    """The sticky top bar. R is the path back to the site root ("" on the home page, "../" one folder down)."""
    return ('<nav class="sticky"><div class="wrap">'
            '<button class="ddb" type="button" aria-expanded="false" aria-controls="vault">The Vault <i>&#9662;</i></button>'
            '<button class="ddb" type="button" aria-expanded="false" aria-controls="research">Research <i>&#9662;</i></button>'
            f'<a href="{R}#standings">Standings</a><a href="{R}#transactions">Transactions</a><a href="{R}#archive">Issues</a></div>'
            + _menu(R, "vault", VAULT) + _menu(R, "research", RESEARCH) + '</nav>')


def vault_block(R=""):
    """Home page: two distinct groups of four links beside the crest."""
    def group(cls, head, items):
        t = "".join(f'<a class="vt" href="{R}{h}"><b>{n}</b><span>{s}</span></a>' for h, n, s in items)
        return f'<div class="vault{cls}"><p class="vh">{head}</p><div class="vg">{t}</div></div>'
    return '<div class="vaults">' + group("", "Inside the Vault", VAULT) + group(" research", "Research", RESEARCH) + '</div>'


def page(R, title, sub, body, og, desc, css=()):
    """A plain content page: masthead, top bar, main, footer. `og` is the Open Graph block from build_site.og_block."""
    sheets = "".join(f'<link rel="stylesheet" href="{R}css/{c}.css">' for c in ("dynastree", *css))
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} | Dynastree Chronicles</title><meta name="description" content="{desc}"><meta name="robots" content="noindex">
{og}
{FONTS}{sheets}
<link rel="icon" type="image/png" sizes="32x32" href="{R}assets/favicon-32.png"><link rel="apple-touch-icon" href="{R}assets/apple-touch-icon.png"></head><body>
<a class="skip" href="#main">Skip to main content</a>
<header class="mast"><div class="wrap"><img src="{R}assets/crest-mark.webp" alt="Dynastree Chronicles crest" width="79" height="96"><div><h1><a href="{R}">Dynastree <span>Chronicles</span></a></h1><p>{sub}</p></div></div></header>
{nav(R)}
<main class="wrap" id="main" tabindex="-1">{body}</main>
<footer><div class="wrap"><img class="tree wm" src="{R}assets/logo-dynastree-chronicles.webp" alt="Dynastree Chronicles" width="180" height="69" loading="lazy"><p>Time heals all wounds, but screenshots last forever.</p></div></footer>
<script src="{R}js/site.js"></script><script src="{R}js/nav.js"></script></body></html>'''
