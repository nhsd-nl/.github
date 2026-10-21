#!/usr/bin/env python3
"""Build the SVG cards for the nhsd-nl organisation profile.

GitHub shows SVGs through <img>, which cannot load webfonts, so every card
embeds its own font subset (fetched from Google Fonts with only the glyphs
that card uses). Run from anywhere:

    python3 profile/src/build.py

Writes to profile/assets/. Standard library only; needs network access.
"""

import base64
import html
import re
import urllib.parse
import urllib.request
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "assets"
W = 1200

# Design tokens, from the nhsd.nl design handoff.
INK = "#12110f"
SHEET = "#fcfcfb"
WARM = "#f4f2ee"
HAIRLINE = "#e6e3dd"
RULE = "#d8d4cc"
BODY = "#57534c"
MUTED = "#6b665e"
AMBER = "#d99444"
AMBER_DARK = "#8f5e14"
AMBER_INK = "#3d2f18"
DARK_BODY = "#b5b0a8"
DARK_MUTED = "#918b81"
DARK_LINE = "#2a2724"

FONTS = {
    "head": ("Archivo", 600),
    "body": ("Public Sans", 400),
    "mono": ("IBM Plex Mono", 400),
    "monob": ("IBM Plex Mono", 500),
}
UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0 Safari/537.36"
)
_font_cache = {}


def font_face(key, chars):
    family, weight = FONTS[key]
    text = "".join(sorted(set(chars) | set(" ")))
    cache_key = (key, text)
    if cache_key not in _font_cache:
        q = urllib.parse.urlencode(
            {"family": f"{family}:wght@{weight}", "text": text, "display": "block"}
        )
        req = urllib.request.Request(
            f"https://fonts.googleapis.com/css2?{q}", headers={"User-Agent": UA}
        )
        css = urllib.request.urlopen(req).read().decode()
        url = re.search(r"url\((https://[^)]+)\)", css).group(1)
        data = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA})).read()
        _font_cache[cache_key] = base64.b64encode(data).decode()
    b64 = _font_cache[cache_key]
    return (
        f"@font-face{{font-family:'n-{key}';font-weight:{weight};"
        f"src:url(data:font/woff2;base64,{b64}) format('woff2');}}"
    )


class Svg:
    """Collects text per font so each card ships only the glyphs it shows."""

    def __init__(self, h, title, css=""):
        self.h = h
        self.title = title
        self.css = css
        self.parts = []
        self.chars = {k: set() for k in FONTS}

    def add(self, s):
        self.parts.append(s)

    def text(self, x, y, s, font, size, fill, track=0.0, anchor="start", cls="", extra=""):
        self.chars[font] |= set(s)
        c = f' class="{cls}"' if cls else ""
        ls = f' letter-spacing="{track * size:.2f}"' if track else ""
        a = f' text-anchor="{anchor}"' if anchor != "start" else ""
        self.add(
            f'<text x="{x}" y="{y}" font-family="n-{font}" font-size="{size}" '
            f'fill="{fill}"{ls}{a}{c}{extra}>{html.escape(s, quote=False)}</text>'
        )

    def spans(self, x, y, size, track, runs, anchor="start"):
        """One line made of runs: (text, font, fill, cls)."""
        a = f' text-anchor="{anchor}"' if anchor != "start" else ""
        ls = f' letter-spacing="{track * size:.2f}"' if track else ""
        inner = ""
        for s, font, fill, cls in runs:
            self.chars[font] |= set(s)
            c = f' class="{cls}"' if cls else ""
            inner += (
                f'<tspan font-family="n-{font}" fill="{fill}"{c}>'
                f"{html.escape(s, quote=False)}</tspan>"
            )
        self.add(f'<text x="{x}" y="{y}" font-size="{size}"{ls}{a}>{inner}</text>')

    def write(self, name):
        faces = "".join(font_face(k, v) for k, v in self.chars.items() if v)
        svg = (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{self.h}" '
            f'viewBox="0 0 {W} {self.h}" role="img" aria-label="{html.escape(self.title)}">'
            f"<title>{html.escape(self.title)}</title>"
            f"<style>{faces}{self.css}"
            "@media (prefers-reduced-motion:reduce){*{animation:none!important}}"
            "</style>" + "".join(self.parts) + "</svg>"
        )
        (OUT / name).write_text(svg)
        print(f"{name:24} {len(svg) / 1024:6.1f} KB")


def mono_width(s, size, track):
    # IBM Plex Mono advances 600 units per 1000 em.
    return len(s) * size * (0.6 + track)


def card(svg, fill, stroke=None, rx=24):
    st = f' stroke="{stroke}"' if stroke else ""
    svg.add(f'<rect x="0.5" y="0.5" width="{W - 1}" height="{svg.h - 1}" rx="{rx}" fill="{fill}"{st}/>')


def wordmark(svg, x, y, size, letters, brackets=AMBER):
    svg.spans(x, y, size, -0.02, [("[ ", "monob", brackets, ""), ("nhsd", "monob", letters, ""), (" ]", "monob", brackets, "")])


# --------------------------------------------------------------------- hero

HERO_CSS = """
.caret{animation:blink 1.1s steps(1) infinite}
@keyframes blink{50%{opacity:0}}
.pulse{transform-origin:76px 140px;animation:pulse 2.4s ease-out infinite}
@keyframes pulse{0%{transform:scale(1);opacity:.55}80%,100%{transform:scale(3.2);opacity:0}}
"""


def hero(dark):
    bg, ink, body, muted, line, pill = (
        (INK, SHEET, DARK_BODY, DARK_MUTED, DARK_LINE, "#1d1b18")
        if dark
        else (SHEET, INK, BODY, MUTED, HAIRLINE, WARM)
    )
    kicker = AMBER if dark else AMBER_DARK
    s = Svg(540, "nhsd · Niels Heisterkamp, freelance senior software developer", HERO_CSS)
    card(s, bg, line)

    wordmark(s, 48, 50, 24, ink)
    s.text(1152, 47, "SOFTWARE DEVELOPMENT B.V.", "mono", 11, muted, 0.18, "end")
    s.add(f'<line x1="0" y1="84" x2="{W}" y2="84" stroke="{line}"/>')

    label = "OPEN FOR NEW WORK FROM Q1 2027"
    pw = 64 + mono_width(label, 12, 0.12)
    s.add(f'<rect x="48" y="122" width="{pw:.0f}" height="36" rx="18" fill="{pill}" stroke="{line}"/>')
    s.add(f'<circle class="pulse" cx="76" cy="140" r="5" fill="{AMBER}"/>')
    s.add(f'<circle cx="76" cy="140" r="5" fill="{AMBER}"/>')
    s.text(94, 144.5, label, "mono", 12, ink, 0.12)
    s.text(pw + 72, 144.5, "FREELANCE · HILLEGOM, NL", "mono", 11, kicker, 0.18)

    s.text(44, 252, "A senior developer you can", "head", 76, ink, -0.05)
    s.spans(44, 330, 76, -0.05, [("hand the hard part to.", "head", ink, ""), (" ", "head", ink, ""), ("▍", "mono", AMBER, "caret")])

    s.text(48, 388, "Twenty years of building software end to end. Give me the piece nobody", "body", 20, body)
    s.text(48, 418, "wants to own and you get it back working and documented.", "body", 20, body)

    s.add(f'<line x1="48" y1="456" x2="1152" y2="456" stroke="{line}"/>')
    meta = [("STATUS", "Open from Q1 2027"), ("BASIS", "Freelance"), ("REMOTE", "NL / EU"), ("LANGUAGES", "Dutch, English")]
    for i, (k, v) in enumerate(meta):
        x = 48 + i * 276
        s.text(x, 488, k, "mono", 11, muted, 0.18)
        s.text(x, 514, v, "body", 17, ink)
    s.write(f"hero-{'dark' if dark else 'light'}.svg")


# -------------------------------------------------------------------- stats


def stats():
    # Each figure rolls up like an odometer, then rests on its value.
    stats = [(20, "YRS", "OF EXPERIENCE"), (8, "YRS", "IN A LEAD ROLE"), (3, "LIVE", "PRODUCTS TODAY"), (1, "DEV", "FULL STACK, END TO END")]
    step, base = 84, 112
    css = ""
    for i, (n, _, _) in enumerate(stats):
        css += (
            f".r{i}{{animation:r{i} {1.4 + n * 0.03:.2f}s cubic-bezier(.16,1,.3,1) {0.2 + i * 0.15:.2f}s both}}"
            f"@keyframes r{i}{{from{{transform:translateY(0)}}to{{transform:translateY({n * step}px)}}}}"
            f"@media (prefers-reduced-motion:reduce){{.r{i}{{transform:translateY({n * step}px)}}}}"
        )
    s = Svg(200, "20 years of experience · 8 years in a lead role · 3 products live today · 1 developer, full stack", css)
    card(s, INK, None, 20)
    col = W / 4
    for i, (n, unit, label) in enumerate(stats):
        x0 = i * col
        if i:
            s.add(f'<line x1="{x0}" y1="36" x2="{x0}" y2="164" stroke="{DARK_LINE}"/>')
        x = x0 + 40
        s.add(f'<clipPath id="c{i}"><rect x="{x - 4}" y="{base - 62}" width="120" height="78"/></clipPath>')
        s.add(f'<g clip-path="url(#c{i})"><g class="r{i}">')
        for k in range(n + 1):
            s.text(x, base - k * step, str(k), "head", 72, AMBER, -0.05, extra=' font-variant-numeric="tabular-nums"')
        s.add("</g></g>")
        digits = len(str(n))
        s.text(x + digits * 41 + 12, base, unit, "mono", 12, DARK_BODY, 0.12)
        s.text(x, base + 40, label, "mono", 11, DARK_MUTED, 0.14)
    s.write("stats.svg")


# ----------------------------------------------------------------- products


def product_text(s, kicker, title, lines, link, c_kicker, c_title, c_body, c_link):
    s.text(48, 68, kicker, "mono", 11, c_kicker, 0.18)
    s.text(45, 128, title, "head", 46, c_title, -0.045)
    for i, l in enumerate(lines):
        s.text(48, 176 + i * 28, l, "body", 17, c_body)
    s.text(48, 176 + len(lines) * 28 + 28, link, "monob", 13, c_link, 0.08)


QL_CSS = """
.type{transform-box:fill-box;transform-origin:0 0;animation:type 9s steps(14) infinite}
@keyframes type{0%,8%{transform:scaleX(0)}40%,100%{transform:scaleX(1)}}
.chip{opacity:0;animation:chip 9s infinite}
@keyframes chip{0%,44%{opacity:0;transform:translateY(4px)}50%,92%{opacity:1;transform:none}100%{opacity:0}}
.cur{animation:cur 9s steps(14) infinite}
@keyframes cur{0%,8%{transform:translateX(0)}40%,100%{transform:translateX(134.4px)}}
.blink{animation:blink 1s steps(1) infinite}
@keyframes blink{50%{opacity:0}}
"""


def quicklifts():
    s = Svg(320, "QuickLifts: a strength training log that stays out of your way. quicklifts.app", QL_CSS)
    card(s, WARM, HAIRLINE)
    product_text(
        s,
        "PRODUCT · IPHONE, ANDROID, WEB",
        "QuickLifts",
        ["A strength training log that stays out of your way.", "One line per exercise, in your own shorthand. It picks", "up sets, reps, weight and RPE as you type. Works offline."],
        "QUICKLIFTS.APP  →",
        MUTED, INK, BODY, AMBER_DARK,
    )
    # A log, as the app shows it: shorthand on the left, what it understood on the right.
    px, py, pw, ph = 640, 40, 512, 240
    s.add(f'<rect x="{px}" y="{py}" width="{pw}" height="{ph}" rx="18" fill="{SHEET}" stroke="{HAIRLINE}"/>')
    s.text(px + 28, py + 40, "TUE · LEGS & PULL", "mono", 11, MUTED, 0.18)
    s.text(px + pw - 28, py + 40, "62 MIN", "mono", 11, MUTED, 0.18, "end")
    s.add(f'<line x1="{px + 28}" y1="{py + 56}" x2="{px + pw - 28}" y2="{py + 56}" stroke="{HAIRLINE}"/>')

    def chips(y, items, cls=""):
        x = px + 236
        for it in items:
            w = mono_width(it, 11, 0.06) + 18
            c = f' class="{cls}"' if cls else ""
            s.add(f'<g{c}><rect x="{x}" y="{y - 15}" width="{w:.0f}" height="22" rx="11" fill="{WARM}" stroke="{HAIRLINE}"/>')
            s.text(x + 9, y, it, "mono", 11, AMBER_DARK, 0.06)
            s.add("</g>")
            x += w + 6

    rows = [("squat 5x5 100 @7", ["5 SETS", "5 REPS", "100 KG", "RPE 7"]), ("rdl 3x8 80 @8", ["3 SETS", "8 REPS", "80 KG", "RPE 8"])]
    for i, (line, items) in enumerate(rows):
        y = py + 96 + i * 46
        s.text(px + 28, y, line, "mono", 16, INK)
        chips(y - 2, items)
    y = py + 96 + 2 * 46
    typed = "row 4x10 60 @7"
    s.add(f'<clipPath id="tc"><rect class="type" x="{px + 28}" y="{y - 20}" width="134.4" height="28"/></clipPath>')
    s.text(px + 28, y, typed, "mono", 16, INK, extra=' clip-path="url(#tc)"')
    s.add(f'<g class="cur"><rect class="blink" x="{px + 29}" y="{y - 16}" width="2" height="20" fill="{AMBER}"/></g>')
    chips(y - 2, ["4 SETS", "10 REPS", "60 KG", "RPE 7"], "chip")
    s.write("quicklifts.svg")


BS_CSS = """
.drift{animation:drift 14s ease-in-out infinite}
@keyframes drift{0%,100%{transform:translate(0,0)}25%{transform:translate(-14px,6px)}50%{transform:translate(-6px,-10px)}75%{transform:translate(10px,4px)}}
.rec{animation:rec 1.4s steps(1) infinite}
@keyframes rec{50%{opacity:.15}}
.focus{transform-origin:896px 160px;animation:focus 14s ease-in-out infinite}
@keyframes focus{0%,100%{transform:scale(1)}48%{transform:scale(1)}52%{transform:scale(.94)}56%{transform:scale(1)}}
"""


def benchscope():
    s = Svg(320, "BenchScope: your iPhone as a bench microscope, up to 120 fps. benchscope.nhsd.nl", BS_CSS)
    card(s, INK)
    product_text(
        s,
        "PRODUCT · IPHONE",
        "BenchScope",
        ["Your iPhone as a bench microscope. Up to 120 fps for", "soldering and electronics repair, with lens, focus,", "exposure and white balance all under your control."],
        "BENCHSCOPE.NHSD.NL  →",
        DARK_MUTED, SHEET, DARK_BODY, AMBER,
    )
    cx, cy, r = 896, 160, 124
    s.add(f'<clipPath id="lens"><circle cx="{cx}" cy="{cy}" r="{r}"/></clipPath>')
    s.add(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="#1b1916"/>')
    # A magnified board: traces, an SOIC chip and a pad being soldered.
    board = [f'<g clip-path="url(#lens)"><g class="drift">']
    for k in range(-6, 7):
        board.append(f'<path d="M{cx - 200} {cy + k * 26} h{150 + (k % 3) * 30} l26 26 h400" stroke="#2f2b26" stroke-width="7" fill="none"/>')
    board.append(f'<rect x="{cx - 70}" y="{cy - 46}" width="140" height="92" rx="6" fill="#0c0b0a" stroke="#3a352f"/>')
    for k in range(5):
        for side in (-1, 1):
            board.append(f'<rect x="{cx - 56 + k * 26}" y="{cy + side * 46 - (12 if side < 0 else 0)}" width="12" height="12" fill="#a8a29a"/>')
    board.append(f'<circle cx="{cx - 70 + 44}" cy="{cy - 26}" r="5" fill="#2a2724"/>')
    board.append(f'<circle cx="{cx + 92}" cy="{cy + 64}" r="16" fill="#c9c2b6"/><circle cx="{cx + 92}" cy="{cy + 64}" r="16" fill="{AMBER}" opacity=".35"/>')
    board.append("</g></g>")
    s.add("".join(board))
    s.add(f'<g class="focus" fill="none" stroke="{AMBER}" stroke-width="1.5">'
          f'<path d="M{cx - 18} {cy}h12M{cx + 6} {cy}h12M{cx} {cy - 18}v12M{cx} {cy + 6}v12"/>'
          f'<path d="M{cx - 48} {cy - 32}v-16h16M{cx + 48} {cy - 32}v-16h-16M{cx - 48} {cy + 32}v16h16M{cx + 48} {cy + 32}v16h-16"/></g>')
    s.add(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{DARK_LINE}" stroke-width="2"/>')
    hud = [(640, 70, "start", "120 FPS"), (640, 92, "start", "ISO 200"), (1152, 70, "end", "WB 5200 K"), (1152, 92, "end", "MF 0.42"), (1152, 262, "end", "4K · HEVC")]
    for x, y, a, t in hud:
        s.text(x, y, t, "mono", 11, DARK_MUTED, 0.14, a)
    s.add(f'<circle class="rec" cx="646" cy="258" r="5" fill="{AMBER}"/>')
    s.text(658, 262, "REC", "mono", 11, AMBER, 0.14)
    s.write("benchscope.svg")


def sangara():
    zinc, fg, body, line, muted = "#09090b", "#fafafa", "#a1a1aa", "#27272a", "#71717a"
    s = Svg(320, "Sangara Elektrotechniek: website for a certified electrician in Noord-Holland. sangara-elektrotechniek.nl", "")
    card(s, zinc, line)
    product_text(
        s,
        "CLIENT · WEBSITE",
        "Sangara Elektrotechniek",
        ["Website for a certified electrician in Noord-Holland:", "services, guide prices and quote requests.", "Design, build and hosting."],
        "SANGARA-ELEKTROTECHNIEK.NL  →",
        muted, fg, body, fg,
    )
    # A browser window with the shape of the site: nav, hero, a row of service cards.
    bx, by, bw, bh = 640, 40, 512, 240
    s.add(f'<rect x="{bx}" y="{by}" width="{bw}" height="{bh}" rx="14" fill="#18181b" stroke="{line}"/>')
    for k in range(3):
        s.add(f'<circle cx="{bx + 22 + k * 16}" cy="{by + 20}" r="4.5" fill="{line}"/>')
    s.add(f'<rect x="{bx + 84}" y="{by + 11}" width="{bw - 168}" height="18" rx="9" fill="{zinc}"/>')
    s.text(bx + bw / 2, by + 24, "sangara-elektrotechniek.nl", "mono", 10, muted, 0.04, "middle")
    s.add(f'<line x1="{bx}" y1="{by + 40}" x2="{bx + bw}" y2="{by + 40}" stroke="{line}"/>')
    ix = bx + 24
    s.add(f'<path d="M{ix + 8} {by + 56}l-7 13h6l-3 10 9-14h-6l4-9z" fill="#facc15"/>')
    s.add(f'<rect x="{ix + 22}" y="{by + 62}" width="70" height="8" rx="4" fill="{body}"/>')
    for k in range(3):
        s.add(f'<rect x="{bx + bw - 200 + k * 50}" y="{by + 62}" width="36" height="6" rx="3" fill="{line}"/>')
    s.add(f'<rect x="{ix}" y="{by + 96}" width="250" height="14" rx="7" fill="{fg}"/>')
    s.add(f'<rect x="{ix}" y="{by + 118}" width="180" height="14" rx="7" fill="{fg}"/>')
    s.add(f'<rect x="{ix}" y="{by + 142}" width="210" height="6" rx="3" fill="{line}"/>')
    s.add(f'<rect x="{bx + bw - 154}" y="{by + 98}" width="130" height="34" rx="17" fill="{fg}"/>')
    s.text(bx + bw - 89, by + 119, "OFFERTE AANVRAGEN", "monob", 9, zinc, 0.08, "middle")
    cw = (bw - 48 - 24) / 3
    for k in range(3):
        x = ix + k * (cw + 12)
        s.add(f'<rect x="{x:.0f}" y="{by + 166}" width="{cw:.0f}" height="56" rx="8" fill="{zinc}" stroke="{line}"/>')
        s.add(f'<rect x="{x + 12:.0f}" y="{by + 180}" width="{cw * 0.55:.0f}" height="7" rx="3.5" fill="{body}"/>')
        s.add(f'<rect x="{x + 12:.0f}" y="{by + 198}" width="{cw * 0.35:.0f}" height="6" rx="3" fill="{line}"/>')
    s.write("sangara.svg")


# -------------------------------------------------------------------- close


def close():
    s = Svg(260, "Looking forward to hearing from you. niels@nhsd.nl", "")
    card(s, AMBER)
    s.text(48, 64, "04 · GET IN TOUCH", "mono", 11, AMBER_INK, 0.18)
    s.text(46, 124, "Looking forward to hearing from you.", "head", 44, INK, -0.04)
    s.text(48, 166, "Send a short description of the work and when you need it.", "body", 18, AMBER_INK)
    s.text(48, 216, "NIELS@NHSD.NL  →", "monob", 14, INK, 0.08)
    wordmark(s, 1152 - mono_width("[ nhsd ]", 40, -0.02), 214, 40, INK, AMBER_INK)
    s.write("close.svg")


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    hero(False)
    hero(True)
    stats()
    quicklifts()
    benchscope()
    sangara()
    close()
