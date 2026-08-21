import json

from seacar_to_dwc import worms


class _FakeResponse:
    def __init__(self, status_code=200, payload=None):
        self.status_code = status_code
        self._payload = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self._payload


class _FakeSession:
    def __init__(self, responses: dict):
        self.responses = responses  # name -> _FakeResponse
        self.calls = []

    def get(self, url, params, timeout):
        name = params["scientificnames[]"]
        self.calls.append(name)
        return self.responses[name]


def test_resolve_lsids_picks_accepted_match(tmp_path):
    session = _FakeSession({
        "Halodule wrightii": _FakeResponse(payload=[[
            {"status": "accepted", "lsid": "urn:lsid:marinespecies.org:taxname:208925"},
        ]]),
    })
    result = worms.resolve_lsids({"Halodule wrightii"}, tmp_path / "cache.json", session=session)
    assert result["Halodule wrightii"] == "urn:lsid:marinespecies.org:taxname:208925"


def test_resolve_lsids_returns_none_for_no_match(tmp_path):
    session = _FakeSession({"Nonexistent taxon": _FakeResponse(status_code=204, payload=None)})
    result = worms.resolve_lsids({"Nonexistent taxon"}, tmp_path / "cache.json", session=session)
    assert result["Nonexistent taxon"] is None


def test_resolve_lsids_is_cached_to_disk_and_not_requeried(tmp_path):
    cache_path = tmp_path / "cache.json"
    session = _FakeSession({
        "Halodule wrightii": _FakeResponse(payload=[[
            {"status": "accepted", "lsid": "urn:lsid:marinespecies.org:taxname:208925"},
        ]]),
    })
    worms.resolve_lsids({"Halodule wrightii"}, cache_path, session=session)
    assert session.calls == ["Halodule wrightii"]
    assert json.loads(cache_path.read_text()) == {"Halodule wrightii": "urn:lsid:marinespecies.org:taxname:208925"}

    # second call for the same name must not hit the network again
    session2 = _FakeSession({})
    result = worms.resolve_lsids({"Halodule wrightii"}, cache_path, session=session2)
    assert session2.calls == []
    assert result["Halodule wrightii"] == "urn:lsid:marinespecies.org:taxname:208925"


def test_resolve_lsids_prefers_accepted_over_synonym_match(tmp_path):
    session = _FakeSession({
        "Foo bar": _FakeResponse(payload=[[
            {"status": "unaccepted", "lsid": "urn:lsid:marinespecies.org:taxname:1"},
            {"status": "accepted", "lsid": "urn:lsid:marinespecies.org:taxname:2"},
        ]]),
    })
    result = worms.resolve_lsids({"Foo bar"}, tmp_path / "cache.json", session=session)
    assert result["Foo bar"] == "urn:lsid:marinespecies.org:taxname:2"


def test_lookup_failure_is_non_fatal(tmp_path):
    class _RaisingSession:
        def get(self, *a, **k):
            raise ConnectionError("no network")

    result = worms.resolve_lsids({"Halodule wrightii"}, tmp_path / "cache.json", session=_RaisingSession())
    assert result["Halodule wrightii"] is None
