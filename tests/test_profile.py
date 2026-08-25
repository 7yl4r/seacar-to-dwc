from seacar_to_dwc.profile import raw_data_profile, unmapped_parameter_ids


def test_raw_data_profile_counts(sample_df, species_ref):
    profile = raw_data_profile(sample_df, species_ref)
    assert profile["row_count"] == len(sample_df)
    assert profile["n_program_locations"] == sample_df["ProgramLocationID"].nunique()
    assert profile["sample_date_range"] == {"start": "1998-07-24", "end": "2015-09-23"}


def test_raw_data_profile_flags_non_taxon_species(sample_df, species_ref):
    # 15472 "Total seagrass" is in Ref_Species but has no ScientificName
    profile = raw_data_profile(sample_df, species_ref)
    ids = {s["species_id"] for s in profile["non_taxon_species"]}
    assert 15472 in ids
    assert profile["unresolved_species"] == []


def test_raw_data_profile_flags_species_missing_from_ref_entirely(sample_df, species_ref):
    # a SpeciesID present in the raw data but absent from Ref_Species altogether
    # is a distinct, more concerning case than a recognized non-taxon code --
    # today taxonomy.lookup() treats it the same (silently dropped), so the
    # report needs to be able to call it out separately.
    dropped_ref = species_ref.drop(index=2795)
    profile = raw_data_profile(sample_df, dropped_ref)
    ids = {s["species_id"] for s in profile["unresolved_species"]}
    assert ids == {2795}


def test_unmapped_parameter_ids_empty_when_everything_mapped(sample_df, vocab):
    assert unmapped_parameter_ids(sample_df, vocab) == []


def test_unmapped_parameter_ids_flags_parameters_not_in_vocab(sample_df, vocab):
    vocab_without_bb_score = {"parameters": {k: v for k, v in vocab["parameters"].items() if k != "21"}}
    unmapped = unmapped_parameter_ids(sample_df, vocab_without_bb_score)
    assert [u["parameter_id"] for u in unmapped] == ["21"]
    assert unmapped[0]["parameter_name"] == "Braun Blanquet Score"
