from seacar_to_dwc import parse


def test_parse_drops_exact_duplicate_rows(sample_txt_path):
    df = parse.parse(sample_txt_path)
    # fixture has 11 raw rows, one is an exact duplicate (RowID 99999999 duplicates 353638)
    assert len(df) == 10


def test_parse_coerces_types(sample_df):
    assert sample_df["ResultValue"].dtype.kind == "f"
    assert str(sample_df["SampleDate"].dtype).startswith("datetime64")


def test_parse_missing_column_raises(tmp_path):
    bad = tmp_path / "bad.txt"
    bad.write_text("RowID|ProgramID\n1|570\n")
    try:
        parse.parse(bad)
        assert False, "expected ValueError"
    except ValueError as e:
        assert "missing expected columns" in str(e)
