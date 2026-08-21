from pathlib import Path

import pytest
import yaml

from seacar_to_dwc import parse, taxonomy

FIXTURES = Path(__file__).parent / "fixtures"
CONFIG = Path(__file__).parents[1] / "config"


@pytest.fixture
def sample_txt_path() -> Path:
    return FIXTURES / "sample_sav.txt"


@pytest.fixture
def sample_xlsx_path() -> Path:
    return FIXTURES / "SEACAR_Metadata.xlsx"


@pytest.fixture
def sample_df(sample_txt_path):
    return parse.parse(sample_txt_path)


@pytest.fixture
def species_ref(sample_xlsx_path):
    return taxonomy.load_species_reference(sample_xlsx_path)


@pytest.fixture
def vocab():
    with open(CONFIG / "measurement_vocab.yaml") as f:
        return yaml.safe_load(f)
