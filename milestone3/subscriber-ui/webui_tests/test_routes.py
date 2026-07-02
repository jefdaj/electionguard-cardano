import pytest
from egc.webui import create_app

@pytest.fixture
def app():
    return create_app({"TESTING": True})

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.mark.asyncio
async def test_index(client):
    resp = await client.get("/")
    assert resp.status_code == 200
