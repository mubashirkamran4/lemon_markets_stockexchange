import pytest
from fastapi.testclient import TestClient

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent)) 


from app.api import app

@pytest.fixture
def client():
    return TestClient(app)