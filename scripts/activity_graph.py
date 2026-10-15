"""Render profile/activity.svg: daily contributions over the last 31 days.

Fetches the contribution calendar from the GitHub GraphQL API (GH_TOKEN),
or reads a {"YYYY-MM-DD": count} JSON file passed as the first argument.
"""
import json
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


def render(points: list) -> str:
    peak = max(max(c for _, c in points), 1)
    step = max(1, -(-peak // 5))  # ~5 gridlines
    top = step * -(-peak // step)
    pw, ph = W - LEFT - RIGHT, H - TOP - BOTTOM
    x = lambda i: LEFT + pw * i / (len(points) - 1)
    y = lambda c: TOP + ph * (1 - c / top)

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Contribution activity, last {DAYS} days">',
        "<defs><linearGradient id=\"fill\" x1=\"0\" y1=\"0\" x2=\"0\" y2=\"1\">"
        f'<stop offset="0" stop-color="{LINE}" stop-opacity="0.45"/><stop offset="1" stop-color="{LINE}" stop-opacity="0.02"/></linearGradient></defs>',
        f'<rect width="{W}" height="{H}" rx="6" fill="{BG}"/>',
        f'<text x="{W / 2}" y="32" text-anchor="middle" font-family="Segoe UI, Ubuntu, sans-serif" font-size="20" font-weight="600" fill="{TITLE}">Álvaro\'s Contribution Graph</text>',
    ]
    font = 'font-family="Segoe UI, Ubuntu, sans-serif" font-size="11"'
    for value in range(0, top + 1, step):
        parts.append(f'<line x1="{LEFT}" x2="{W - RIGHT}" y1="{y(value):.1f}" y2="{y(value):.1f}" stroke="{GRID}"/>')
        parts.append(f'<text x="{LEFT - 10}" y="{y(value) + 4:.1f}" text-anchor="end" {font} fill="{AXIS}">{value}</text>')
    for i, (day, _) in enumerate(points):
        if i % 2 == 0:
            parts.append(f'<text x="{x(i):.1f}" y="{H - BOTTOM + 20}" text-anchor="middle" {font} fill="{AXIS}">{day.day}</text>')
    parts.append(f'<text x="{W / 2}" y="{H - 8}" text-anchor="middle" {font} fill="{AXIS}">Days</text>')
    parts.append(f'<text x="16" y="{TOP + ph / 2}" text-anchor="middle" {font} fill="{AXIS}" transform="rotate(-90 16 {TOP + ph / 2})">Contributions</text>')

    line = " ".join(f"{x(i):.1f},{y(c):.1f}" for i, (_, c) in enumerate(points))
    parts.append(f'<polygon points="{LEFT},{y(0):.1f} {line} {W - RIGHT},{y(0):.1f}" fill="url(#fill)"/>')
    parts.append(f'<polyline points="{line}" fill="none" stroke="{LINE}" stroke-width="2.5" stroke-linejoin="round"/>')
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
