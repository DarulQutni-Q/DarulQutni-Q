#!/usr/bin/env python3
"""Regenerate darulqutni-profile.svg from template.svg.

Fills in a live uptime (counted from birth date) and GitHub stats
(repos / stars / followers / following) pulled from the GitHub API.

Inspired by Andrew6rant's profile generator. Runs daily via GitHub Actions.
"""

import os
from datetime import datetime, timezone

import requests

USERNAME = "DarulQutni-Q"
BIRTH = datetime(2007, 10, 17, tzinfo=timezone.utc)
TEMPLATE = "template.svg"
OUTPUT = "darulqutni-profile.svg"


def uptime(birth: datetime) -> str:
    """Human-readable 'X years, Y months, Z days' since birth."""
    now = datetime.now(timezone.utc)
    years = now.year - birth.year
    months = now.month - birth.month
    days = now.day - birth.day

    if days < 0:
        months -= 1
        # days in the previous month relative to `now`
        prev_month = now.month - 1 or 12
        prev_year = now.year if now.month != 1 else now.year - 1
        if prev_month == 2:
            leap = prev_year % 4 == 0 and (prev_year % 100 != 0 or prev_year % 400 == 0)
            dim = 29 if leap else 28
        elif prev_month in (1, 3, 5, 7, 8, 10, 12):
            dim = 31
        else:
            dim = 30
        days += dim
    if months < 0:
        years -= 1
        months += 12

    def plural(n, unit):
        return f"{n} {unit}" + ("s" if n != 1 else "")

    return ", ".join([plural(years, "year"), plural(months, "month"), plural(days, "day")])


def github_stats(username: str) -> dict:
    """Fetch repos / stars / followers / following. Degrades gracefully."""
    token = os.environ.get("ACCESS_TOKEN") or os.environ.get("GITHUB_TOKEN")
    headers = {"Authorization": f"token {token}"} if token else {}
    stats = {"repos": "0", "stars": "0", "followers": "0", "following": "0"}
    try:
        user = requests.get(
            f"https://api.github.com/users/{username}", headers=headers, timeout=20
        ).json()
        stats["repos"] = str(user.get("public_repos", 0))
        stats["followers"] = str(user.get("followers", 0))
        stats["following"] = str(user.get("following", 0))

        stars, page = 0, 1
        while True:
            resp = requests.get(
                f"https://api.github.com/users/{username}/repos",
                headers=headers,
                params={"per_page": 100, "page": page},
                timeout=20,
            ).json()
            if not isinstance(resp, list) or not resp:
                break
            stars += sum(r.get("stargazers_count", 0) for r in resp)
            if len(resp) < 100:
                break
            page += 1
        stats["stars"] = str(stars)
    except Exception as exc:  # noqa: BLE001 - never fail the build on API hiccups
        print(f"[warn] GitHub API failed, using zeros: {exc}")
    return stats


def main() -> None:
    with open(TEMPLATE, encoding="utf-8") as fh:
        svg = fh.read()

    values = {"uptime": uptime(BIRTH), **github_stats(USERNAME)}
    for key, val in values.items():
        svg = svg.replace("{" + key + "}", val)

    with open(OUTPUT, "w", encoding="utf-8") as fh:
        fh.write(svg)

    print(f"Generated {OUTPUT}: {values}")


if __name__ == "__main__":
    main()
