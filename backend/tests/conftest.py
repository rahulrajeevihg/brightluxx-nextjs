import pytest
import os

@pytest.fixture(scope="session")
def base_url():
    return os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
