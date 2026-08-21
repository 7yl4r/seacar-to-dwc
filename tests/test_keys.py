from seacar_to_dwc.keys import event_id, measurement_id, occurrence_id


def test_event_id_is_natural_key():
    eid = event_id("570", "GAS01", "1998-07-24", "0")
    assert eid == "urn:seacar:event:570:GAS01:1998-07-24:0"


def test_event_id_strips_time_component():
    assert event_id("570", "GAS01", "1998-07-24 00:00:00.000", "0") == event_id("570", "GAS01", "1998-07-24", "0")


def test_occurrence_id_nests_under_event_id():
    occ = occurrence_id("570", "GAS01", "1998-07-24", "0", "2795")
    assert occ == "urn:seacar:occ:570:GAS01:1998-07-24:0:2795"


def test_occurrence_id_distinct_per_species():
    a = occurrence_id("570", "GAS01", "1998-07-24", "0", "2795")
    b = occurrence_id("570", "GAS01", "1998-07-24", "0", "15472")
    assert a != b


def test_measurement_id_nests_under_its_parent():
    eid = event_id("570", "GAS01", "1998-07-24", "0")
    occ = occurrence_id("570", "GAS01", "1998-07-24", "0", "2795")
    event_level = measurement_id(eid, "69")
    occ_level = measurement_id(occ, "69")
    assert event_level == "urn:seacar:mof:570:GAS01:1998-07-24:0:69"
    assert occ_level == "urn:seacar:mof:570:GAS01:1998-07-24:0:2795:69"
    assert event_level != occ_level
