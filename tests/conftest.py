"""Test configuration and fixtures."""

import os
from typing import Optional
import pytest
import pytest_asyncio
from dotenv import load_dotenv

from app_vitals_mcp.servers.toggl.config import TogglConfig
from app_vitals_mcp.servers.toggl.client import TogglClient
from app_vitals_mcp.servers.trello.config import TrelloConfig
from app_vitals_mcp.servers.trello.client import TrelloClient


# Load environment variables from .env file
load_dotenv()


@pytest.fixture
def mock_api_token() -> str:
    """Mock API token for testing."""
    return "test_api_token_123"


@pytest.fixture
def real_api_token() -> Optional[str]:
    """Real API token from environment (if available)."""
    return os.getenv("TOGGL_API_TOKEN")


@pytest.fixture
def test_config(mock_api_token: str) -> TogglConfig:
    """Test configuration with mock API token."""
    return TogglConfig(api_token=mock_api_token, workspace_id=12345)


@pytest.fixture
def real_config(real_api_token: Optional[str]) -> Optional[TogglConfig]:
    """Real configuration from environment (if available)."""
    if not real_api_token:
        return None
    
    workspace_id = os.getenv("TOGGL_WORKSPACE_ID")
    return TogglConfig(
        api_token=real_api_token,
        workspace_id=int(workspace_id) if workspace_id else None
    )


@pytest_asyncio.fixture
async def mock_toggl_client(mock_api_token: str) -> TogglClient:
    """Mock Toggl client for testing."""
    client = TogglClient(mock_api_token)
    yield client
    await client.close()


@pytest_asyncio.fixture
async def real_toggl_client(real_api_token: Optional[str]):
    """Real Toggl client (if API token is available)."""
    if not real_api_token:
        yield None
        return
    
    client = TogglClient(real_api_token)
    yield client
    await client.close()


@pytest.fixture
def mock_trello_config() -> TrelloConfig:
    """Mock Trello configuration for testing."""
    return TrelloConfig(
        api_key="test_api_key",
        token="test_token"
    )


@pytest.fixture
def real_trello_config() -> Optional[TrelloConfig]:
    """Real Trello configuration from environment (if available)."""
    api_key = os.getenv("TRELLO_API_KEY")
    token = os.getenv("TRELLO_TOKEN")
    
    if not api_key or not token:
        return None
    
    return TrelloConfig(api_key=api_key, token=token)


@pytest_asyncio.fixture
async def mock_trello_client(mock_trello_config: TrelloConfig) -> TrelloClient:
    """Mock Trello client for testing."""
    client = TrelloClient(mock_trello_config.api_key, mock_trello_config.token)
    yield client
    await client.close()


@pytest_asyncio.fixture
async def real_trello_client(real_trello_config: Optional[TrelloConfig]):
    """Real Trello client (if credentials are available)."""
    if not real_trello_config:
        yield None
        return
    
    client = TrelloClient(real_trello_config.api_key, real_trello_config.token)
    yield client
    await client.close()


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests (may require API token)"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests (mocked)"
    )