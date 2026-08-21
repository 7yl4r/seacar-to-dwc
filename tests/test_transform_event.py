from seacar_to_dwc.transform.event import build_events


def test_one_event_per_location_date_quadrat(sample_df):
    events = build_events(sample_df)
    assert len(events) == 2  # fixture covers GAS01/1998-07-24 and GAS03/2015-09-23, one quadrat each
    assert set(events["eventID"]) == {
        "urn:seacar:event:570:GAS01:1998-07-24:0",
        "urn:seacar:event:570:GAS03:2015-09-23:0",
    }


def test_event_carries_station_level_fields(sample_df):
    events = build_events(sample_df).set_index("eventID")
    gas01 = events.loc["urn:seacar:event:570:GAS01:1998-07-24:0"]
    assert gas01["sampleSizeValue"] == 1.0
    assert gas01["sampleSizeUnit"] == "square metres"
    assert gas01["geodeticDatum"] == "WGS84"
    assert gas01["countryCode"] == "US"
    assert gas01["locality"] == "GAS01"
    assert gas01["year"] == 1998
    assert gas01["month"] == 7
