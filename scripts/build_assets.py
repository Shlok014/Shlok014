"""Builds the static profile SVGs: the eye-chart header and the project cards.

Run: python3 scripts/build_assets.py   (writes assets/*.svg, light and dark)
"""

from theme import (MONO, ROOT, SANS, THEMES, esc, font_css, measure, optotype_defs, wrap)

OUT = ROOT / "assets"

# ---------------------------------------------------------------- eye chart header

W, H = 1000, 640
CX = W / 2

# Rows read top to bottom like a Snellen chart and spell the name. Acuity is in metres,
# the way Indian clinics write it (6/6, not 20/20).
OPTO_ROWS = [  # letters, letter height, top y, row label, acuity
    ("S", 120, 50, "1", "6/60"),
    ("HL", 84, 210, "2", "6/36"),
    ("OKD", 60, 330, "3", "6/24"),
    ("AHALE", 44, 420, "4", "6/12"),
]
TEXT_ROWS = [  # text, size, baseline, row label, acuity
    ("SECURITY · FULL-STACK · HEALTHCARE SOFTWARE", 21, 534, "5", "6/9"),
    ("IF YOU CAN READ THIS, YOUR VISION IS 6/6", 15, 573, "6", "6/6"),
]
RED_Y, GREEN_Y = 487, 595


def focus_filter(fid, delay):
    """Blur that resolves, overshoots slightly and locks: a phoropter finding focus."""
    total = delay + 0.95
    k = [0, delay / total, (delay + 0.45) / total, (delay + 0.68) / total, 1]
    kt = ";".join(f"{x:.3f}" for x in k)
    return (
        f'<filter id="{fid}" x="-30%" y="-60%" width="160%" height="220%">'
        f'<feGaussianBlur stdDeviation="0">'
        f'<animate attributeName="stdDeviation" values="9;9;0;1.8;0" keyTimes="{kt}" '
        f'dur="{total:.2f}s" fill="freeze"/></feGaussianBlur></filter>'
    ), kt, total


def fade(kt, total):
    return (f'<animate attributeName="opacity" values="0.15;0.15;1;1;1" keyTimes="{kt}" '
            f'dur="{total:.2f}s" fill="freeze"/>')


def chart(theme):
    t = THEMES[theme]
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
        f'viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-labelledby="t d">',
        '<title id="t">Shlok Dahale</title>',
        '<desc id="d">An eye chart whose rows spell SHLOK DAHALE, with the smallest lines '
        'reading: Security, full-stack, healthcare software. If you can read this, your vision '
        'is 6/6.</desc>',
        f"<style>{font_css('next-700', 'mono-400')}"
        f".lab{{font:400 15px {MONO};fill:{t['muted']}}}"
        f".row{{font-family:{SANS};font-weight:700;fill:{t['ink']}}}</style>",
        f"<defs>{optotype_defs(t['ink'])}",
    ]
    filters, bodies = [], []
    rows = len(OPTO_ROWS) + len(TEXT_ROWS)
    for i in range(rows):
        f, kt, total = focus_filter(f"f{i}", 0.2 + i * 0.3)
        filters.append(f)
        bodies.append((kt, total))
    parts.append("".join(filters) + "</defs>")
    parts.append(f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="18" '
                 f'fill="{t["panel"]}" stroke="{t["hair"]}"/>')

    def labels(label, acuity, mid):
        return (f'<text class="lab" x="86" y="{mid + 5:.1f}">{label}</text>'
                f'<text class="lab" x="{W - 86}" y="{mid + 5:.1f}" text-anchor="end">{acuity}</text>')

    for i, (letters, size, top, label, acuity) in enumerate(OPTO_ROWS):
        kt, total = bodies[i]
        width = size * (2 * len(letters) - 1)  # gaps between letters are one letter wide
        x0 = CX - width / 2
        uses = "".join(
            f'<use xlink:href="#o{ch}" href="#o{ch}" x="{x0 + j * 2 * size:.1f}" y="{top}" '
            f'width="{size}" height="{size}"/>' for j, ch in enumerate(letters))
        parts.append(f'<g filter="url(#f{i})" opacity="1">{fade(kt, total)}{uses}</g>')
        parts.append(labels(label, acuity, top + size / 2))
        if letters == "AHALE":
            parts.append(f'<rect x="170" y="{RED_Y}" width="{W - 340}" height="3" fill="{t["red"]}">'
                         f'{fade(kt, total)}</rect>')

    for j, (text, size, base, label, acuity) in enumerate(TEXT_ROWS):
        i = len(OPTO_ROWS) + j
        kt, total = bodies[i]
        # Spread the letters like a chart line, but never wider than the red line.
        natural = measure(text, size, "next-700")
        track = min(size * 0.24, (600 - natural) / (len(text) - 1))
        parts.append(
            f'<g filter="url(#f{i})">{fade(kt, total)}<text class="row" x="{CX}" y="{base}" '
            f'font-size="{size}" letter-spacing="{track:.2f}" text-anchor="middle">{esc(text)}</text></g>')
        parts.append(labels(label, acuity, base - size * 0.36))
        if acuity == "6/6":
            parts.append(f'<rect x="170" y="{GREEN_Y}" width="{W - 340}" height="3" '
                         f'fill="{t["green"]}">{fade(kt, total)}</rect>')

    parts.append("</svg>")
    return "".join(parts)


# ---------------------------------------------------------------- project rows

def card(theme, eyebrow, title, desc, tags, live=False, w=840, h=150):
    """One project as a full-width row: name and stack on the left, what it does on the right."""
    t = THEMES[theme]
    pad, split = 32, 356
    size = 15.5
    lines = wrap(desc, size, w - split - pad - 34)
    eb_color = t["green"] if live else t["muted"]
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" '
        f'role="img" aria-labelledby="t d"><title id="t">{esc(title)}</title>'
        f'<desc id="d">{esc(desc)}</desc>',
        f"<style>{font_css('next-400', 'next-700', 'mono-400', 'mono-600')}"
        f".eb{{font:600 11.5px {MONO};letter-spacing:1.6px;fill:{eb_color}}}"
        f".ti{{font:700 27px {SANS};fill:{t['ink']};letter-spacing:-.3px}}"
        f".de{{font:400 {size}px {SANS};fill:{t['muted']}}}"
        f".tg{{font:400 11.5px {MONO};letter-spacing:1.1px;fill:{t['muted']}}}"
        f".ar{{font:400 18px {SANS};fill:{t['muted']}}}</style>",
        f'<rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="14" fill="{t["panel"]}" '
        f'stroke="{t["hair"]}"/>',
    ]
    x = pad
    if live:
        out.append(f'<circle cx="{x + 4}" cy="{pad + 5}" r="4" fill="{t["green"]}">'
                   f'<animate attributeName="opacity" values="1;.35;1" dur="2.4s" '
                   f'repeatCount="indefinite"/></circle>')
        x += 16
    out.append(f'<text class="eb" x="{x}" y="{pad + 9}">{esc(eyebrow)}</text>')
    out.append(f'<text class="ti" x="{pad}" y="{pad + 50}">{esc(title)}</text>')
    out.append(f'<text class="tg" x="{pad}" y="{h - pad + 2}">{esc(" · ".join(tags))}</text>')
    out.append(f'<line x1="{split - 26}" y1="{pad - 4}" x2="{split - 26}" y2="{h - pad + 4}" '
               f'stroke="{t["hair"]}"/>')
    top = h / 2 - (len(lines) - 1) * 12 + 5
    for i, line in enumerate(lines):
        out.append(f'<text class="de" x="{split}" y="{top + i * 24:.1f}">{esc(line)}</text>')
    out.append(f'<text class="ar" x="{w - pad + 4}" y="{pad + 12}" text-anchor="end">↗</text>')
    out.append("</svg>")
    return "".join(out)


CARDS = {
    "watchtower": dict(
        eyebrow="SECURITY OPERATIONS", title="Watchtower",
        desc="Ingests logs from many sources, correlates detections as they happen, runs "
             "response playbooks and keeps a tamper-evident audit ledger.",
        tags=["PYTHON", "FLASK", "REACT", "SKLEARN"]),
    "iac": dict(
        eyebrow="DEVSECOPS · LLM", title="LLM IaC Security",
        desc="LLM fixes for Terraform and Dockerfile misconfigurations. Each fix is "
             "parse-checked, drift-checked and rescanned before it is returned.",
        tags=["PYTHON", "CHECKOV", "TRIVY", "ACTIONS"]),
    "foveal": dict(
        live=True, eyebrow="LIVE · FOVEAL.IN", title="Foveal",
        desc="Clinic software for ophthalmologists: queue, eye exam, prescriptions, surgery, "
             "optical, pharmacy and billing, with row-level security on every clinical table.",
        tags=["REACT", "TYPESCRIPT", "SUPABASE"]),
}


def main():
    for theme in THEMES:
        (OUT / f"chart-{theme}.svg").write_text(chart(theme))
        for name, spec in CARDS.items():
            (OUT / f"card-{name}-{theme}.svg").write_text(card(theme, **spec))
    print("built", sorted(p.name for p in OUT.glob("*.svg")))


if __name__ == "__main__":
    main()
