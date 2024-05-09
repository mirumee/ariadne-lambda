import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

TESTS_DIR = Path(__file__).parent.absolute()


def load_data_file(fine_name: str):
    with open(TESTS_DIR / "data" / fine_name) as data_file:
        return json.load(data_file)


@pytest.fixture
def api_gateway_v1_event_payload():
    return load_data_file("api_gateway_v1_event.json")


@pytest.fixture
def api_gateway_v2_event_payload():
    return load_data_file("api_gateway_v2_event.json")


@pytest.fixture
def lambda_context():
    return MagicMock()
