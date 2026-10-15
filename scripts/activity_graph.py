"""Render profile/activity.svg: daily contributions over the last 31 days.

The y axis is logarithmic so a single huge day doesn't flatten the rest:
the gap between 10 and 100 reads as clearly as the one between 100 and 1000.

Fetches the contribution calendar from the GitHub GraphQL API (GH_TOKEN),
or reads a {"YYYY-MM-DD": count} JSON file passed as the first argument.
"""
import json
import math
import os
import sys
import urllib.request
from datetime import date, timedelta
from pathlib import Path

USER = "alvrichh"
DAYS = 31
OUT = Path("profile/activity.svg")

W, H = 850, 300
LEFT, RIGHT, TOP, BOTTOM = 60, 25, 55, 45
BG, TITLE, LINE, POINT, AXIS, GRID = "#1a1b27", "#70a5fd", "#bf91f3", "#38bdae", "#a9b1d6", "#2a2e45"

# Axis marks to choose from; the top of the axis is the first one >= the peak.
TICKS = (0, 1, 5, 10, 25, 50, 100, 250, 500, 1000, 2500, 5000, 10000)
MIN_GAP = 22  # px between labelled gridlines

QUERY = """
query($login: String!, $from: DateTime!, $to: DateTime!) {
  user(login: $login) {
    contributionsCollection(from: $from, to: $to) {
      contributionCalendar { weeks { contributionDays { date contributionCount } } }
    }
  }
}"""


def fetch(start: date, end: date) -> dict:
    body = json.dumps({"query": QUERY, "variables": {
        "login": USER, "from": f"{start}T00:00:00Z", "to": f"{end}T23:59:59Z"}}).encode()
    request = urllib.request.Request("https://api.github.com/graphql", data=body, headers={
        "Authorization": "Bearer " + os.environ["GH_TOKEN"], "Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = json.load(response)
    if payload.get("errors"):
        raise SystemExit(f"GraphQL error: {payload['errors']}")
    weeks = payload["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
    return {d["date"]: d["contributionCount"] for w in weeks for d in w["contributionDays"]}


def smooth(xy: list) -> str:
    """SVG path through every point, monotone cubic (Fritsch-Carlson): curvy
    like a roller coaster but never overshooting a point, so it can't dip
    below zero or above a peak."""
    n = len(xy)
    dx = [xy[i + 1][0] - xy[i][0] for i in range(n - 1)]
    slope = [(xy[i + 1][1] - xy[i][1]) / dx[i] for i in range(n - 1)]
    tangent = [slope[0]] + [0.0 if a * b <= 0 else (a + b) / 2 for a, b in zip(slope, slope[1:])] + [slope[-1]]
    for i, s in enumerate(slope):
        if s == 0:
            tangent[i] = tangent[i + 1] = 0.0
            continue
        a, b = tangent[i] / s, tangent[i + 1] / s
        if a * a + b * b > 9:
            k = 3 / math.hypot(a, b)
            tangent[i], tangent[i + 1] = k * a * s, k * b * s
    d = [f"M{xy[0][0]:.1f},{xy[0][1]:.1f}"]
    for i in range(n - 1):
        (x0, y0), (x1, y1), h = xy[i], xy[i + 1], dx[i] / 3
        d.append(f"C{x0 + h:.1f},{y0 + tangent[i] * h:.1f} {x1 - h:.1f},{y1 - tangent[i + 1] * h:.1f} {x1:.1f},{y1:.1f}")
    return " ".join(d)


def render(points: list) -> str:
    peak = max(max(c for _, c in points), 1)
    top = next((t for t in TICKS if t >= peak), peak)
    pw, ph = W - LEFT - RIGHT, H - TOP - BOTTOM
    x = lambda i: LEFT + pw * i / (len(points) - 1)
    y = lambda c: TOP + ph * (1 - math.log1p(c) / math.log1p(top))

    marks = []
    for value in (t for t in TICKS if t <= top):
        if not marks or y(marks[-1]) - y(value) >= MIN_GAP or value == top:
            if marks and value == top and y(marks[-1]) - y(value) < MIN_GAP:
                marks.pop()  # keep the top label, drop its crowded neighbour
            marks.append(value)

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Contribution activity, last {DAYS} days">',
        "<defs><linearGradient id=\"fill\" x1=\"0\" y1=\"0\" x2=\"0\" y2=\"1\">"
        f'<stop offset="0" stop-color="{LINE}" stop-opacity="0.45"/><stop offset="1" stop-color="{LINE}" stop-opacity="0.02"/></linearGradient></defs>',
        f'<rect width="{W}" height="{H}" rx="6" fill="{BG}"/>',
        f'<text x="{W / 2}" y="32" text-anchor="middle" font-family="Segoe UI, Ubuntu, sans-serif" font-size="20" font-weight="600" fill="{TITLE}">Álvaro\'s Contribution Graph</text>',
    ]
    font = 'font-family="Segoe UI, Ubuntu, sans-serif" font-size="11"'
    for value in marks:
        parts.append(f'<line x1="{LEFT}" x2="{W - RIGHT}" y1="{y(value):.1f}" y2="{y(value):.1f}" stroke="{GRID}"/>')
        parts.append(f'<text x="{LEFT - 10}" y="{y(value) + 4:.1f}" text-anchor="end" {font} fill="{AXIS}">{value}</text>')
    for i, (day, _) in enumerate(points):
        if i % 2 == 0:
            parts.append(f'<text x="{x(i):.1f}" y="{H - BOTTOM + 20}" text-anchor="middle" {font} fill="{AXIS}">{day.day}</text>')
    parts.append(f'<text x="{W / 2}" y="{H - 8}" text-anchor="middle" {font} fill="{AXIS}">Days</text>')
    parts.append(f'<text x="16" y="{TOP + ph / 2}" text-anchor="middle" {font} fill="{AXIS}" transform="rotate(-90 16 {TOP + ph / 2})">Contributions</text>')

    curve = smooth([(x(i), y(c)) for i, (_, c) in enumerate(points)])
    parts.append(f'<path d="M{LEFT},{y(0):.1f} L{curve[1:]} L{W - RIGHT},{y(0):.1f} Z" fill="url(#fill)"/>')
    parts.append(f'<path d="{curve}" fill="none" stroke="{LINE}" stroke-width="2.5" stroke-linejoin="round"/>')
    for i, (day, c) in enumerate(points):
        parts.append(f'<circle cx="{x(i):.1f}" cy="{y(c):.1f}" r="3.5" fill="{POINT}"><title>{day}: {c}</title></circle>')
    parts.append("</svg>")
    return "\n".join(parts) + "\n"


def main() -> None:
    end = date.today()
    start = end - timedelta(days=DAYS - 1)
    counts = json.loads(Path(sys.argv[1]).read_text()) if len(sys.argv) > 1 else fetch(start, end)
    points = [(start + timedelta(days=i), counts.get(str(start + timedelta(days=i)), 0)) for i in range(DAYS)]
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(render(points))
    print(f"Wrote {OUT} ({sum(c for _, c in points)} contributions in {DAYS} days).")


if __name__ == "__main__":
    main()
