from seacar_to_dwc.docs_scaffold import ensure_dataset_docs


def test_creates_default_instructions_files(tmp_path):
    dataset_dir = ensure_dataset_docs("999", tmp_path)
    assert dataset_dir == tmp_path / "datasets" / "999"
    assert (dataset_dir / "summary.instructions.md").exists()
    assert (dataset_dir / "transform_notes.instructions.md").exists()


def test_never_overwrites_an_existing_instructions_file(tmp_path):
    ensure_dataset_docs("999", tmp_path)
    custom_path = tmp_path / "datasets" / "999" / "summary.instructions.md"
    custom_path.write_text("a reviewer already customized this")

    ensure_dataset_docs("999", tmp_path)

    assert custom_path.read_text() == "a reviewer already customized this"


def test_never_creates_summary_or_transform_notes(tmp_path):
    # those have to be actually drafted (by a human or an AI reading the
    # instructions + raw_data_profile.json), not stamped out as empty stubs
    # that could be mistaken for "reviewed and genuinely empty"
    dataset_dir = ensure_dataset_docs("999", tmp_path)
    assert not (dataset_dir / "summary.md").exists()
    assert not (dataset_dir / "transform_notes.md").exists()
