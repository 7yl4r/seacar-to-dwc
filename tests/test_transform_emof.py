from seacar_to_dwc.transform.emof import build_emof


def test_presence_absence_of_a_real_taxon_is_not_duplicated_as_a_measurement(sample_df, species_ref, vocab):
    # 2795's Presence/Absence rows become dwc:occurrenceStatus (see test_transform_occurrence),
    # not a MeasurementOrFact row -- would otherwise say the same thing twice.
    emof = build_emof(sample_df, species_ref, vocab)
    taxon_pa = emof[(emof["occurrenceID"].notna()) & (emof["measurementType"] == "Presence/Absence")]
    assert len(taxon_pa) == 0


def test_non_taxon_presence_absence_is_dropped_entirely(sample_df, species_ref, vocab):
    # 15472 "Total seagrass" has no Occurrence to attach an occurrenceStatus to,
    # but that reading is still what occurrenceStatus is *for* -- it's dropped
    # from eMoF rather than reintroduced as a plain measurement.
    emof = build_emof(sample_df, species_ref, vocab)
    assert len(emof[emof["measurementType"] == "Presence/Absence"]) == 0


def test_braun_blanquet_score_is_occurrence_level_for_real_taxa(sample_df, species_ref, vocab):
    emof = build_emof(sample_df, species_ref, vocab)
    row = emof[
        (emof["occurrenceID"] == "urn:seacar:occ:570:GAS01:1998-07-24:0:2795")
        & (emof["measurementType"].str.contains("Braun-Blanquet"))
    ]
    assert len(row) == 1
    assert row.iloc[0]["measurementValue"] == 4.0


def test_every_row_has_an_event_id(sample_df, species_ref, vocab):
    emof = build_emof(sample_df, species_ref, vocab)
    assert emof["eventID"].notna().all()


def test_total_measurement_count(sample_df, species_ref, vocab):
    # 10 source rows minus all 5 Presence/Absence rows (dropped regardless of
    # taxon status -- 2795 x2, 5573, and 15472 x2) leaves the 5 Braun Blanquet
    # Score rows.
    emof = build_emof(sample_df, species_ref, vocab)
    assert len(emof) == 5
