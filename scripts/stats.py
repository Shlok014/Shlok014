"""Draws the 12-month contribution card from the GitHub contribution calendar.

Run by .github/workflows/profile.yml every day:
    GITHUB_TOKEN=... python3 scripts/stats.py <login> <out_dir>
"""

import datetime as dt
import json
import os
import sys
import urllib.request
from pathlib import Path

from theme import MONO, SANS, THEMES, font_css

QUERY = """query($login:String!){user(login:$login){contributionsCollection{
contributionCalendar{totalContributions weeks{contributionDays{date contributionCount}}}}}}"""


def fetch(login):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": login}}).encode(),
        headers={"Authorization": f"bearer {os.environ['GITHUB_TOKEN']}",
                 "Content-Type": "application/json", "User-Agent": "profile-stats"},
    )
    body = json.load(urllib.request.urlopen(req, timeout=30))
    if "errors" in body:
        sys.exit(f"GitHub API error: {body['errors']}")
    return body["data"]["user"]["contributionsCollection"]["contributionCalendar"]


def summarise(cal):
    weeks = [[d["contributionCount"] for d in w["contributionDays"]] for w in cal["weeks"]]
    days = [d for w in cal["weeks"] for d in w["contributionDays"]]
    counts = [d["contributionCount"] for d in days]
    longest = run = 0
    for c in counts:
        run = run + 1 if c else 0
        longest = max(longest, run)
    # Today may have no contributions yet, so a streak that ended yesterday is still current.
    tail = counts[:-1] if counts and counts[-1] == 0 else counts
    current = 0
    for c in reversed(tail):
        if not c:
            break
        current += 1
    return {
        "total": cal["totalContributions"],
        "longest": longest,
        "current": current,
        "active": sum(1 for c in counts if c),
        "weekly": [sum(w) for w in weeks],
        "updated": dt.date.fromisoformat(days[-1]["date"]),
    }


def card(theme, s):
    t = THEMES[theme]
    w, h, pad = 840, 236, 32
    figures = [
        (f"{s['total']:,}", "CONTRIBUTIONS"),
        (f"{s['active']}", "ACTIVE DAYS"),
        (f"{s['longest']}", "LONGEST STREAK"),
        (f"{s['current']}", "CURRENT STREAK"),
    ]
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" '
        f'role="img" aria-labelledby="t"><title id="t">{s["total"]:,} contributions in the last '
        f'12 months, {s["active"]} active days, longest streak {s["longest"]} days, current streak '
        f'{s["current"]} days</title>',
        f"<style>{font_css('next-700', 'mono-400', 'mono-600')}"
        f".eb{{font:600 11.5px {MONO};letter-spacing:1.6px;fill:{t['muted']}}}"
        f".up{{font:400 11.5px {MONO};fill:{t['muted']}}}"
        f".n{{font:700 34px {SANS};fill:{t['ink']};letter-spacing:-.5px}}"
        f".l{{font:400 11px {MONO};letter-spacing:1.3px;fill:{t['muted']}}}"
        f".bar{{animation:rise .7s cubic-bezier(.2,.8,.2,1) both;transform-box:fill-box;"
        f"transform-origin:bottom}}@keyframes rise{{from{{transform:scaleY(0)}}}}"
        f"@media (prefers-reduced-motion:reduce){{.bar{{animation:none}}}}</style>",
        f'<rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="14" fill="{t["panel"]}" '
        f'stroke="{t["hair"]}"/>',
        f'<text class="eb" x="{pad}" y="{pad + 9}">THE LAST 12 MONTHS</text>',
        f'<text class="up" x="{w - pad}" y="{pad + 9}" text-anchor="end">'
        f'updated {s["updated"].strftime("%d %b %Y")}</text>',
    ]
    col = (w - 2 * pad) / len(figures)
    for i, (num, label) in enumerate(figures):
        x = pad + i * col
        out.append(f'<text class="n" x="{x}" y="{pad + 62}">{num}</text>')
        out.append(f'<text class="l" x="{x}" y="{pad + 84}">{label}</text>')

    # One bar per week. The busiest week is the only coloured one.
    weekly = s["weekly"]
    top, base = pad + 112, h - pad
    span = w - 2 * pad
    step = span / len(weekly)
    bw = step * 0.62
    peak = max(weekly) or 1
    best = weekly.index(peak)
    for i, v in enumerate(weekly):
        cx = pad + i * step + step / 2
        if not v:  # a quiet week is a dot on the baseline, not a bar
            out.append(f'<circle cx="{cx:.1f}" cy="{base - 1.5}" r="1.5" fill="{t["bar"]}" '
                       f'opacity=".22"/>')
            continue
        bh = max(3, (base - top) * v / peak)
        fill, op = (t["green"], 1) if i == best else (t["bar"], 0.22)
        out.append(f'<rect class="bar" x="{pad + i * step + (step - bw) / 2:.1f}" '
                   f'y="{base - bh:.1f}" width="{bw:.1f}" height="{bh:.1f}" rx="1.5" fill="{fill}" '
                   f'opacity="{op}" style="animation-delay:{i * 12}ms"/>')
    out.append("</svg>")
    return "".join(out)


def main():
    login, out_dir = sys.argv[1], Path(sys.argv[2])
    out_dir.mkdir(parents=True, exist_ok=True)
    s = summarise(fetch(login))
    for theme in THEMES:
        (out_dir / f"stats-{theme}.svg").write_text(card(theme, s))
    print({k: v for k, v in s.items() if k != "weekly"})


if __name__ == "__main__":
    main()
