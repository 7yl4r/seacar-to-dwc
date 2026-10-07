from seacar_to_dwc.reviewable_docs import read_reviewable_doc, review_badge


def test_missing_file_returns_empty(tmp_path):
    front_matter, body = read_reviewable_doc(tmp_path / "summary.md")
    assert front_matter == {}
    assert body == ""


def test_parses_front_matter_and_body(tmp_path):
    path = tmp_path / "summary.md"
    path.write_text('---\nreviewed: true\nreviewed_by: "Jane"\n---\n\nBody text here.\n')
    front_matter, body = read_reviewable_doc(path)
    assert front_matter == {"reviewed": True, "reviewed_by": "Jane"}
    assert body == "Body text here."


def test_malformed_front_matter_falls_back_to_raw_text(tmp_path):
    path = tmp_path / "summary.md"
    path.write_text("---\nreviewed: true\n(missing closing delimiter)\n")
    front_matter, body = read_reviewable_doc(path)
    assert front_matter == {}
    assert "missing closing delimiter" in body


def test_review_badge_not_drafted_when_file_missing():
    assert "Not yet drafted" in review_badge({})


def test_review_badge_not_drafted_when_scaffolded_but_empty():
    # docs_scaffold.py writes generated_by: null up front -- front matter
    # exists (it has `instructions`/`reviewed`/etc.) but nobody has drafted
    # the body yet, which must still read as "not drafted", not "reviewed: false"
    badge = review_badge({"instructions": "...", "generated_by": None, "reviewed": False})
    assert "Not yet drafted" in badge


def test_review_badge_not_reviewed():
    badge = review_badge({"generated_by": "Claude"})
    assert "Not yet reviewed" in badge
    assert "Claude" in badge


def test_review_badge_reviewed():
    badge = review_badge({"generated_by": "Claude", "reviewed": True, "reviewed_by": "Jane", "reviewed_at": "2026-01-01"})
    assert "Reviewed by Jane" in badge
    assert "2026-01-01" in badge
