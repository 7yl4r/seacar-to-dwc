from seacar_to_dwc.transform.occurrence import build_occurrences


def test_only_real_taxa_become_occurrences(sample_df, species_ref, vocab):
    occ = build_occurrences(sample_df, species_ref, vocab)
    # 2795 (Halodule wrightii) appears in both events, 5573 (Caulerpa spp.) only in the second;
    # 15472 (Total seagrass, not a real taxon) must be excluded from both
    assert len(occ) == 3
    assert set(occ["scientificName"]) == {"Halodule wrightii", "Caulerpa spp."}


def test_occurrence_id_nests_under_its_event(sample_df, species_ref, vocab):
    occ = build_occurrences(sample_df, species_ref, vocab).set_index("occurrenceID")
    row = occ.loc["urn:seacar:occ:570:GAS01:1998-07-24:0:2795"]
    assert row["eventID"] == "urn:seacar:event:570:GAS01:1998-07-24:0"


def test_occurrence_status_present_from_presence_absence_row(sample_df, species_ref, vocab):
    occ = build_occurrences(sample_df, species_ref, vocab)
    assert (occ["occurrenceStatus"] == "present").all()


def test_genus_rank_occurrence_has_no_species_epithet_in_name(sample_df, species_ref, vocab):
    occ = build_occurrences(sample_df, species_ref, vocab)
    caulerpa = occ[occ["scientificName"] == "Caulerpa spp."].iloc[0]
    assert caulerpa["taxonRank"] == "genus"
    assert caulerpa["genus"] == "Caulerpa"


def test_occurrence_carries_higher_taxonomy(sample_df, species_ref, vocab):
    occ = build_occurrences(sample_df, species_ref, vocab)
    halodule = occ[occ["scientificName"] == "Halodule wrightii"].iloc[0]
    assert halodule["kingdom"] == "Plantae"
    assert halodule["family"] == "Cymodoceaceae"
    assert halodule["basisOfRecord"] == "HumanObservation"
