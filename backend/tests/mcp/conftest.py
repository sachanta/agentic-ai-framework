"""Fixtures and markers for MCP tests."""
import pytest


def pytest_configure(config):
    config.addinivalue_line("markers", "mcp: marks tests as MCP-related")


@pytest.fixture
def sample_tool_def():
    """Minimal tool definition for isolated testing."""
    return {
        "tool_id": "test/sample_tool",
        "name": "sample_tool",
        "display_name": "Sample Tool",
        "category": "test",
        "platform_id": "test",
        "service_class": "SampleService",
        "service_module": "test.mock_module",
        "service_factory": "get_sample_service",
        "method": "do_thing",
        "description": "A sample tool for testing.",
        "returns": "str",
        "requires": [],
        "parameters": [
            {"name": "input", "type": "string", "description": "Input text", "required": True},
            {"name": "count", "type": "integer", "description": "Repeat count", "required": False, "default": 1},
        ],
    }
