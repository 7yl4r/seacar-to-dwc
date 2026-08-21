from seacar_to_dwc.taxonomy import lookup


def test_real_species_is_taxon(species_ref):
    t = lookup(species_ref, "2795")  # Halodule wrightii
    assert t["is_taxon"] is True
    assert t["scientificName"] == "Halodule wrightii"
    assert t["genus"] == "Halodule"
    assert t["kingdom"] == "Plantae"
    assert t["taxonRank"] == "species"


def test_genus_level_identification_is_taxon_at_genus_rank(species_ref):
    t = lookup(species_ref, "5573")  # Caulerpa spp.
    assert t["is_taxon"] is True
    assert t["taxonRank"] == "genus"
    assert t["genus"] == "Caulerpa"


def test_aggregate_code_is_not_a_taxon(species_ref):
    t = lookup(species_ref, "15472")  # Total seagrass
    assert t["is_taxon"] is False


def test_no_grass_placeholder_is_not_a_taxon(species_ref):
    t = lookup(species_ref, "3681")  # No grass in quadrat
    assert t["is_taxon"] is False


def test_unknown_species_id_is_not_a_taxon(species_ref):
    t = lookup(species_ref, "999999999")
    assert t["is_taxon"] is False
