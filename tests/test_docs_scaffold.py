from seacar_to_dwc.docs_scaffold import ensure_dataset_docs
from seacar_to_dwc.reviewable_docs import read_reviewable_doc


def test_creates_the_three_writeup_files(tmp_path):
    dataset_dir = ensure_dataset_docs("999", tmp_path)
    assert dataset_dir == tmp_path / "999"
    assert (dataset_dir / "summary.md").exists()
    assert (dataset_dir / "transform_notes.md").exists()
    assert (dataset_dir / "archive_summary.md").exists()


def test_scaffolded_files_carry_instructions_in_their_own_front_matter(tmp_path):
    # no separate *.instructions.md sibling -- everything a newcomer needs is
    # in the one file, so datasets/<id>/ stays small and self-explanatory
    dataset_dir = ensure_dataset_docs("999", tmp_path)
    front_matter, body = read_reviewable_doc(dataset_dir / "summary.md")
    assert "raw" in front_matter["instructions"].lower()
    assert front_matter["generated_by"] is None
    assert front_matter["reviewed"] is False
    assert body == ""


def test_summary_carries_dataset_identity_what_dataset_yaml_used_to(tmp_path):
    # --all discovers datasets by globbing datasets/*/summary.md and reading
    # program_id out of its front matter -- no separate dataset.yaml
    dataset_dir = ensure_dataset_docs("999", tmp_path)
    front_matter, _ = read_reviewable_doc(dataset_dir / "summary.md")
    assert front_matter["program_id"] == "999"  # pre-filled: the caller already knows it
    assert front_matter["habitat"] is None      # left for a human to fill in
    assert front_matter["description"] is None


def test_only_summary_carries_identity_fields(tmp_path):
    dataset_dir = ensure_dataset_docs("999", tmp_path)
    for filename in ["transform_notes.md", "archive_summary.md"]:
        front_matter, _ = read_reviewable_doc(dataset_dir / filename)
        assert "program_id" not in front_matter


def test_never_overwrites_an_existing_file(tmp_path):
    ensure_dataset_docs("999", tmp_path)
    custom_path = tmp_path / "999" / "summary.md"
    custom_path.write_text("a reviewer already customized this")

    ensure_dataset_docs("999", tmp_path)

    assert custom_path.read_text() == "a reviewer already customized this"
