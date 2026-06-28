#!/usr/bin/env python3
"""Update the profile README's bio + PR-type breakdown from real merged-PR data."""

import json
import os
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from datetime import datetime

_TYPE_EMOJI = {
    "fix": "🐛",
    "feat": "✨",
    "test": "🧪",
    "docs": "📝",
    "perf": "⚡",
    "chore": "🔧",
}


def classify_pr_type(title: str) -> str:
    """Classify a PR title by its conventional-commit-style prefix, if present."""
    prefix = title.split(":", 1)[0].strip().lower()
    # Strip a parenthesized scope, e.g. "fix(uptime)" -> "fix".
    prefix = prefix.split("(", 1)[0].strip()
    return prefix if prefix in _TYPE_EMOJI else "other"


def compute_span_days(merged_dates: list[datetime]) -> int:
    """Days between the earliest and latest merge, floored at 1 if any exist."""
    if not merged_dates:
        return 0
    return max((max(merged_dates) - min(merged_dates)).days, 1)


def build_bio_line(total: int, repo_count: int, span_days: int) -> str:
    return (
        f"{total} external merged PRs across {repo_count} repositories "
        f"in {span_days} days. Self-taught, building entirely from Android/Termux."
    )


def build_breakdown_line(type_counts: Counter) -> str:
    """Render a one-line emoji breakdown, ordered by count descending, ties by name."""
    parts = [
        f"{_TYPE_EMOJI[t]} {n} {t}"
        for t, n in sorted(type_counts.items(), key=lambda kv: (-kv[1], kv[0]))
        if t in _TYPE_EMOJI and n > 0
    ]
    return "  ".join(parts)


def update_readme_content(content: str, bio_line: str, breakdown_line: str) -> str:
    """Replace the bio line under '# Jack Hawkins', and the breakdown line under it.

    Layout maintained:
        # Jack Hawkins

        <bio line>
        <breakdown line>

        <rest of file unchanged>
    """
    lines = content.splitlines(keepends=True)
    for i, line in enumerate(lines):
        if line.strip() == "# Jack Hawkins":
            # Find the next non-blank line (bio) and the one after it (breakdown,
            # if present) — replace both, inserting the breakdown line if it
            # doesn't exist yet.
            j = i + 1
            while j < len(lines) and not lines[j].strip():
                j += 1
            if j >= len(lines):
                break
            lines[j] = bio_line + "\n"
            # Is the next line already a breakdown line (starts with an emoji
            # we own) or something else (blank line / new section)?
            k = j + 1
            if k < len(lines) and lines[k].strip() and not lines[k].strip().startswith("#"):
                lines[k] = breakdown_line + "\n"
            else:
                lines.insert(k, breakdown_line + "\n")
            break
    return "".join(lines)


def fetch_merged_prs(token: str) -> list[dict]:
    query = "author:1HazyOne707 type:pr is:merged -repo:1HazyOne707/Codex-2"
    url = f"https://api.github.com/search/issues?q={urllib.parse.quote(query)}&per_page=50"
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github+json",
        },
    )
    with urllib.request.urlopen(req) as r:
        return json.load(r)["items"]


def main() -> None:
    token = os.environ["GH_TOKEN"]
    prs = fetch_merged_prs(token)

    repos: dict[str, list[str]] = defaultdict(list)
    merged_dates: list[datetime] = []
    type_counts: Counter = Counter()

    for pr in prs:
        repo = pr["repository_url"].split("/")[-2] + "/" + pr["repository_url"].split("/")[-1]
        repos[repo].append(pr["title"])
        type_counts[classify_pr_type(pr["title"])] += 1

        merged_at = pr.get("pull_request", {}).get("merged_at")
        if merged_at:
            merged_dates.append(datetime.fromisoformat(merged_at.replace("Z", "+00:00")))

    total = sum(len(v) for v in repos.values())
    span_days = compute_span_days(merged_dates)

    bio_line = build_bio_line(total, len(repos), span_days)
    breakdown_line = build_breakdown_line(type_counts)

    with open("README.md") as f:
        content = f.read()

    new_content = update_readme_content(content, bio_line, breakdown_line)

    with open("README.md", "w") as f:
        f.write(new_content)

    print(f"Updated: {total} PRs across {len(repos)} repos, spanning {span_days} days")
    print(f"Breakdown: {breakdown_line}")


if __name__ == "__main__":
    main()
