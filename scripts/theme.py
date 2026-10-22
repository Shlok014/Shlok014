"""Shared palette, fonts and drawing helpers for the profile SVGs.

Standard library only, so the daily GitHub Action can import it without installing anything.
"""

import base64
import json
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent.parent
FONTS = ROOT / "assets" / "fonts"

# Colours come from a Snellen chart: black optotypes on a backlit panel, a red line at the
# driving standard and a green line at normal vision. Dark mode keeps the same roles.
THEMES = {
    "light": {
        "page": "#ffffff",
        "panel": "#f5f7f6",
        "ink": "#11161b",
        "muted": "#66707a",
        "hair": "#d8dee1",
        "red": "#c8102e",
        "green": "#0b7a4b",
        "bar": "#11161b",
    },
    "dark": {
        "page": "#0d1117",
        "panel": "#141a21",
        "ink": "#e8edf2",
        "muted": "#8b949e",
        "hair": "#2a323c",
        "red": "#f2545b",
        "green": "#3fb97a",
        "bar": "#e8edf2",
    },
}

_METRICS = json.loads((FONTS / "metrics.json").read_text())


def font_css(*stems):
    """@font-face rules with the subset fonts inlined (an <img> SVG cannot fetch fonts)."""
    rules = []
    for stem in stems:
        family = "Atkinson Next" if stem.startswith("next") else "Atkinson Mono"
        weight = stem.split("-")[1]
        data = base64.b64encode((FONTS / f"{stem}.woff2").read_bytes()).decode()
        rules.append(
            f"@font-face{{font-family:'{family}';font-weight:{weight};"
            f"src:url(data:font/woff2;base64,{data}) format('woff2');}}"
        )
    return "".join(rules)


SANS = "'Atkinson Next',-apple-system,'Segoe UI',Helvetica,Arial,sans-serif"
MONO = "'Atkinson Mono',ui-monospace,SFMono-Regular,Menlo,monospace"


def measure(text, size, stem="next-400", tracking=0.0):
    widths = _METRICS[stem]
    return sum(widths.get(ch, 0.55) for ch in text) * size + tracking * max(len(text) - 1, 0)


def wrap(text, size, max_width, stem="next-400"):
    lines, line = [], ""
    for word in text.split():
        trial = f"{line} {word}".strip()
        if line and measure(trial, size, stem) > max_width:
            lines.append(line)
            line = word
        else:
            line = trial
    if line:
        lines.append(line)
    return lines


def esc(text):
    return escape(text, {'"': "&quot;"})


# Optotypes drawn the way Sloan letters are: on a 5 x 5 grid with a stroke one unit wide.
# Each <symbol> clips to its own box, so diagonal stroke ends are cut square like a printed chart.
OPTOTYPES = {
    "S": "M4.5 1.5A2 1 0 0 0 .5 1.5A2 1 0 0 0 2.5 2.5A2 1 0 0 1 4.5 3.5A2 1 0 0 1 .5 3.5",
    "H": "M.5 0V5M4.5 0V5M.5 2.5H4.5",
    "L": "M.5 0V4.5H5",
    "O": "M2.5 .5A2 2 0 1 1 2.5 4.5A2 2 0 1 1 2.5 .5Z",
    "K": "M.5 0V5M5.3 -.4L.9 3.1M2.3 2L5.3 5.4",
    "D": "M.5 0V5M0 .5H2.5A2 2 0 0 1 2.5 4.5H0",
    "A": "M.2 5.4L2.5 -.4L4.8 5.4M1.3 3.4H3.7",
    "E": "M5 .5H.5V4.5H5M.5 2.5H4.3",
}


def optotype_defs(color):
    out = []
    for ch, d in OPTOTYPES.items():
        out.append(
            f'<symbol id="o{ch}" viewBox="0 0 5 5"><path d="{d}" fill="none" stroke="{color}" '
            f'stroke-width="1" stroke-linejoin="miter" stroke-linecap="butt"/></symbol>'
        )
    return "".join(out)
