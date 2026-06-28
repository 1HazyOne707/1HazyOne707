"""Unit tests for the README update script's pure logic (no network calls)."""

import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from update_readme import (
    build_bio_line,
    build_breakdown_line,
    classify_pr_type,
    compute_span_days,
    update_readme_content,
)


def test_classify_pr_type_simple_prefix():
    assert classify_pr_type("fix: bound request lengths") == "fix"
    assert classify_pr_type("feat: add diff --name-only") == "feat"


def test_classify_pr_type_with_scope():
    assert classify_pr_type("fix(uptime): unverified TLS cert read") == "fix"


def test_classify_pr_type_unknown_prefix_is_other():
    assert classify_pr_type("Add TLS certificate expiry tracking") == "other"


def test_compute_span_days_empty():
    assert compute_span_days([]) == 0


def test_compute_span_days_single_date_floors_to_one():
    d = datetime(2026, 6, 20, tzinfo=timezone.utc)
    assert compute_span_days([d]) == 1


def test_compute_span_days_real_range():
    d1 = datetime(2026, 6, 17, tzinfo=timezone.utc)
    d2 = datetime(2026, 6, 26, tzinfo=timezone.utc)
    assert compute_span_days([d1, d2]) == 9


def test_build_bio_line_format():
    line = build_bio_line(12, 4, 9)
    assert "12 external merged PRs across 4 repositories" in line
    assert "in 9 days" in line


def test_build_breakdown_line_orders_by_count_descending():
    counts = Counter({"fix": 6, "feat": 3, "test": 2, "docs": 1})
    line = build_breakdown_line(counts)
    assert line.index("🐛 6 fix") < line.index("✨ 3 feat") < line.index("🧪 2 test") < line.index("📝 1 docs")


def test_build_breakdown_line_skips_other_and_zero_counts():
    counts = Counter({"fix": 2, "other": 5, "feat": 0})
    line = build_breakdown_line(counts)
    assert "other" not in line
    assert "feat" not in line
    assert "🐛 2 fix" in line


def test_update_readme_content_replaces_bio_and_inserts_breakdown():
    original = "# Jack Hawkins\n\n13 external merged PRs across 4 repositories in 11 days. Old bio.\n\n## Stack\n"
    result = update_readme_content(original, "12 external merged PRs across 4 repositories in 9 days.", "🐛 6 fix  ✨ 3 feat")
    assert "12 external merged PRs" in result
    assert "🐛 6 fix" in result
    assert "## Stack" in result
    assert "13 external merged" not in result
