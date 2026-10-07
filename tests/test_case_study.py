from seacar_to_dwc.case_study import assemble_case_study

REPORT_META = {
    "title": "Charlotte Harbor Seagrass Monitoring",
    "organization": "Florida DEP",
    "managed_areas": ["Gasparilla Sound-Charlotte Harbor AP"],
    "source_url": "https://data.florida-seacar.org/programs/details/570",
    "citation": "FDEP (2025). Test citation.",
    "record_counts": {"events": 2, "occurrences": 3, "measurementOrFacts": 5},
    "archive_filename": "seacar-570-dwca.zip",
}

RAW_PROFILE = {
    "row_count": 10,
    "n_program_locations": 2,
    "n_species_ids": 3,
    "sample_date_range": {"start": "1998-07-24", "end": "2015-09-23"},
    "non_taxon_species": [{"species_id": 15472, "common_identifier": "Total seagrass"}],
    "unresolved_species": [],
    "parameter_counts": {"69": 5, "21": 5},
    "qaqc_flag_counts": {"7Q": 10},
}

VOCAB = {
    "69": {"parameter_name": "Presence/Absence", "role": "occurrence_status"},
    "21": {"parameter_name": "Braun Blanquet Score", "role": "measurement", "measurementType": "Percent Cover"},
}

MAPPING_TEXT = "**Grain.** One Event = one quadrat read at one station on one date."


def _reviewed_doc(reviewed: bool, by: str = "A Reviewer", at: str = "2026-01-01") -> str:
    return (
        "---\n"
        'generated_by: "Claude, 2026-01-01"\n'
        f"reviewed: {str(reviewed).lower()}\n"
        f'reviewed_by: "{by}"\n'
        f'reviewed_at: "{at}"\n'
        "---\n\nSome write-up text.\n"
    )


def test_includes_all_sections_even_when_nothing_drafted(tmp_path):
    text = assemble_case_study("570", tmp_path, REPORT_META, RAW_PROFILE, VOCAB, MAPPING_TEXT)
    for heading in ["## Raw Data", "## Transformation", "## Final Darwin Core Archive", "## Human Review & Sign-off"]:
        assert heading in text
    assert "Not yet drafted" in text
    assert text.count("_(nothing drafted yet)_") == 3


def test_overall_reviewed_false_unless_all_three_writeups_are(tmp_path):
    (tmp_path / "summary.md").write_text(_reviewed_doc(True))
    (tmp_path / "transform_notes.md").write_text(_reviewed_doc(True))
    (tmp_path / "archive_summary.md").write_text(_reviewed_doc(False))

    text = assemble_case_study("570", tmp_path, REPORT_META, RAW_PROFILE, VOCAB, MAPPING_TEXT)
    assert "reviewed: false" in text.splitlines()[4]  # the case_study.md's own front matter

    (tmp_path / "archive_summary.md").write_text(_reviewed_doc(True))
    text = assemble_case_study("570", tmp_path, REPORT_META, RAW_PROFILE, VOCAB, MAPPING_TEXT)
    assert "reviewed: true" in text.splitlines()[4]


def test_applied_vocab_table_flags_unmapped_parameter(tmp_path):
    profile_with_extra = {**RAW_PROFILE, "parameter_counts": {**RAW_PROFILE["parameter_counts"], "99": 2}}
    text = assemble_case_study("570", tmp_path, REPORT_META, profile_with_extra, VOCAB, MAPPING_TEXT)
    assert "UNMAPPED" in text
    assert "| 99 |" in text


def test_flags_unresolved_species(tmp_path):
    profile_with_unresolved = {
        **RAW_PROFILE,
        "unresolved_species": [{"species_id": 4242, "common_identifier": "Mystery weed"}],
    }
    text = assemble_case_study("570", tmp_path, REPORT_META, profile_with_unresolved, VOCAB, MAPPING_TEXT)
    assert "missing from Ref_Species entirely" in text
    assert "4242" in text


def test_sign_off_table_lists_all_three_writeups(tmp_path):
    (tmp_path / "summary.md").write_text(_reviewed_doc(True, by="Jane"))
    text = assemble_case_study("570", tmp_path, REPORT_META, RAW_PROFILE, VOCAB, MAPPING_TEXT)
    assert "summary.md" in text
    assert "transform_notes.md" in text
    assert "archive_summary.md" in text
    assert "Jane" in text
