"""Shared fixtures for tests. Collector tests use credentials, sample API response, minimal blob."""

import pytest


@pytest.fixture
def credentials():
    """Minimal credentials dict for Power BI API (client credentials)."""
    return {
        "tenant_id": "test-tenant",
        "client_id": "test-client",
        "client_secret": "test-secret",
    }


@pytest.fixture
def sample_list_response():
    """Sample API response for list reports (Power BI shape)."""
    return {
        "value": [
            {"id": "r1", "name": "Report 1", "datasetId": "d1"},
            {"id": "r2", "name": "Report 2", "datasetId": "d2"},
        ]
    }


@pytest.fixture
def workspace_id():
    """Sample workspace (group) id."""
    return "ws-123"
