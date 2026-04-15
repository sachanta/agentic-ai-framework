"""Tests for the shared tool registry."""
import base64
from dataclasses import dataclass, field
from typing import List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.common.tools.registry import (
    CATEGORIES,
    TOOL_REGISTRY,
    _serialize_value,
    execute_tool,
    get_tool,
    tool_def_to_input_schema,
)


# ---------------------------------------------------------------------------
# TestToolRegistryStructure
# ---------------------------------------------------------------------------

@pytest.mark.mcp
class TestToolRegistryStructure:
    """Validate the static TOOL_REGISTRY data."""

    def test_registry_not_empty(self):
        assert len(TOOL_REGISTRY) > 0

    def test_required_fields_present(self):
        required = {"tool_id", "name", "display_name", "category", "platform_id",
                     "service_class", "service_module", "service_factory", "method",
                     "description", "returns", "requires", "parameters"}
        for tool in TOOL_REGISTRY:
            missing = required - set(tool.keys())
            assert not missing, f"Tool {tool.get('tool_id', '?')} missing fields: {missing}"

    def test_unique_tool_ids(self):
        ids = [t["tool_id"] for t in TOOL_REGISTRY]
        assert len(ids) == len(set(ids)), f"Duplicate tool IDs: {[x for x in ids if ids.count(x) > 1]}"

    def test_tool_id_has_category_slash_name(self):
        for tool in TOOL_REGISTRY:
            parts = tool["tool_id"].split("/")
            assert len(parts) == 2, f"tool_id '{tool['tool_id']}' should be category/name"
            assert parts[0] == tool["category"], (
                f"tool_id prefix '{parts[0]}' != category '{tool['category']}'"
            )

    def test_all_categories_covered(self):
        used = {t["category"] for t in TOOL_REGISTRY}
        for cat in CATEGORIES:
            assert cat in used, f"Category '{cat}' declared but not used by any tool"

    def test_parameter_fields(self):
        required_param_fields = {"name", "type", "description", "required"}
        for tool in TOOL_REGISTRY:
            for param in tool["parameters"]:
                missing = required_param_fields - set(param.keys())
                assert not missing, (
                    f"Tool {tool['tool_id']} param '{param.get('name', '?')}' missing: {missing}"
                )

    def test_tool_count(self):
        assert len(TOOL_REGISTRY) == 22

    def test_categories_count(self):
        assert len(CATEGORIES) == 7


# ---------------------------------------------------------------------------
# TestGetTool
# ---------------------------------------------------------------------------

@pytest.mark.mcp
class TestGetTool:
    def test_existing_tool(self):
        tool = get_tool("search/tavily_search_topic")
        assert tool["name"] == "tavily_search_topic"

    def test_nonexistent_raises_key_error(self):
        with pytest.raises(KeyError, match="not found"):
            get_tool("nonexistent/tool")

    def test_returns_correct_structure(self):
        tool = get_tool("llm/generate")
        assert tool["service_class"] == "LLMProvider"
        assert tool["method"] == "generate"


# ---------------------------------------------------------------------------
# TestToolDefToInputSchema
# ---------------------------------------------------------------------------

@pytest.mark.mcp
class TestToolDefToInputSchema:
    def test_basic_schema(self, sample_tool_def):
        schema = tool_def_to_input_schema(sample_tool_def)
        assert schema["type"] == "object"
        assert "input" in schema["properties"]
        assert "count" in schema["properties"]

    def test_required_fields(self, sample_tool_def):
        schema = tool_def_to_input_schema(sample_tool_def)
        assert "input" in schema["required"]
        assert "count" not in schema.get("required", [])

    def test_empty_params(self):
        tool_def = {"parameters": []}
        schema = tool_def_to_input_schema(tool_def)
        assert schema["properties"] == {}
        assert "required" not in schema

    def test_property_types(self, sample_tool_def):
        schema = tool_def_to_input_schema(sample_tool_def)
        assert schema["properties"]["input"]["type"] == "string"
        assert schema["properties"]["count"]["type"] == "integer"


# ---------------------------------------------------------------------------
# TestSerializeValue
# ---------------------------------------------------------------------------

@pytest.mark.mcp
class TestSerializeValue:
    def test_primitives(self):
        assert _serialize_value(None) is None
        assert _serialize_value(42) == 42
        assert _serialize_value("hello") == "hello"
        assert _serialize_value(True) is True

    def test_pydantic_model(self):
        mock_model = MagicMock()
        mock_model.model_dump.return_value = {"key": "val"}
        assert _serialize_value(mock_model) == {"key": "val"}

    def test_dataclass(self):
        @dataclass
        class Inner:
            x: int = 1

        @dataclass
        class Outer:
            inner: Inner = None
            items: list = field(default_factory=list)

        result = _serialize_value(Outer(inner=Inner(x=5), items=[Inner(x=10)]))
        assert result["inner"]["x"] == 5
        assert result["items"][0]["x"] == 10

    def test_tuple_to_list(self):
        result = _serialize_value(("text", 3))
        assert result == ["text", 3]

    def test_dict_recursive(self):
        @dataclass
        class D:
            v: int = 0

        result = _serialize_value({"a": D(v=7)})
        assert result == {"a": {"v": 7}}


# ---------------------------------------------------------------------------
# TestExecuteTool
# ---------------------------------------------------------------------------

@pytest.mark.mcp
class TestExecuteTool:
    @pytest.fixture
    def mock_service(self):
        svc = MagicMock()
        svc.do_thing = AsyncMock(return_value="result")
        return svc

    @pytest.fixture
    def mock_module(self, mock_service):
        mod = MagicMock()
        mod.get_sample_service.return_value = mock_service
        return mod

    async def test_calls_service_method(self, sample_tool_def, mock_module, mock_service):
        with patch("app.common.tools.registry.importlib.import_module", return_value=mock_module):
            await execute_tool(sample_tool_def, {"input": "hi"})
        mock_service.do_thing.assert_called_once_with(input="hi")

    async def test_passes_params(self, sample_tool_def, mock_module, mock_service):
        with patch("app.common.tools.registry.importlib.import_module", return_value=mock_module):
            await execute_tool(sample_tool_def, {"input": "hi", "count": 3})
        mock_service.do_thing.assert_called_once_with(input="hi", count=3)

    async def test_serializes_pydantic(self, sample_tool_def, mock_module, mock_service):
        pydantic_result = MagicMock()
        pydantic_result.model_dump.return_value = {"status": "ok"}
        mock_service.do_thing = AsyncMock(return_value=pydantic_result)

        with patch("app.common.tools.registry.importlib.import_module", return_value=mock_module):
            result = await execute_tool(sample_tool_def, {"input": "hi"})
        assert result == {"status": "ok"}

    async def test_serializes_dataclass(self, sample_tool_def, mock_module, mock_service):
        @dataclass
        class Result:
            value: str = "ok"
            count: int = 5

        mock_service.do_thing = AsyncMock(return_value=Result())

        with patch("app.common.tools.registry.importlib.import_module", return_value=mock_module):
            result = await execute_tool(sample_tool_def, {"input": "hi"})
        assert result == {"value": "ok", "count": 5}

    async def test_handles_memory_service_cache_type(self):
        """MemoryService cache_type string is converted to CacheType enum."""
        import sys

        mock_svc = MagicMock()
        mock_svc.set = AsyncMock(return_value=True)
        mock_mod = MagicMock()
        mock_mod.get_memory_service.return_value = mock_svc

        tool_def = get_tool("cache/memory_set")

        mock_cache_enum = MagicMock()
        mock_cache_enum.return_value = "converted_enum_value"

        # Inject a fake module into sys.modules so the local import resolves
        fake_memory_mod = MagicMock()
        fake_memory_mod.CacheType = mock_cache_enum
        saved = sys.modules.get("app.platforms.newsletter.services.memory")
        sys.modules["app.platforms.newsletter.services.memory"] = fake_memory_mod

        try:
            with patch("app.common.tools.registry.importlib.import_module", return_value=mock_mod):
                await execute_tool(tool_def, {
                    "user_id": "u1", "cache_type": "preferences",
                    "key": "k", "value": {"a": 1},
                })
            mock_cache_enum.assert_called_once_with("preferences")
        finally:
            if saved is not None:
                sys.modules["app.platforms.newsletter.services.memory"] = saved
            else:
                sys.modules.pop("app.platforms.newsletter.services.memory", None)

    async def test_base64_decode_for_pdf_processor(self):
        """PDFProcessor content param is decoded from base64 to bytes."""
        raw = b"fake-pdf-bytes"
        encoded = base64.b64encode(raw).decode()

        mock_svc = MagicMock()
        mock_svc.extract_text = AsyncMock(return_value=("extracted text", 3))
        mock_mod = MagicMock()
        mock_mod.get_pdf_processor.return_value = mock_svc

        tool_def = get_tool("document/pdf_extract_text")

        with patch("app.common.tools.registry.importlib.import_module", return_value=mock_mod):
            result = await execute_tool(tool_def, {"content": encoded})

        mock_svc.extract_text.assert_called_once_with(content=raw)
        # Tuple should be converted to list
        assert result == ["extracted text", 3]

    async def test_tuple_serialization(self, sample_tool_def, mock_module, mock_service):
        """Tuple results are converted to lists."""
        mock_service.do_thing = AsyncMock(return_value=("a", 1))

        with patch("app.common.tools.registry.importlib.import_module", return_value=mock_module):
            result = await execute_tool(sample_tool_def, {"input": "hi"})
        assert result == ["a", 1]


# ---------------------------------------------------------------------------
# TestDocumentTools
# ---------------------------------------------------------------------------

@pytest.mark.mcp
class TestDocumentTools:
    def test_category_exists(self):
        assert "document" in CATEGORIES

    def test_tools_exist(self):
        ids = {t["tool_id"] for t in TOOL_REGISTRY}
        assert "document/pdf_extract_text" in ids
        assert "document/pdf_chunk_text" in ids
        assert "document/pdf_process" in ids

    def test_base64_content_documented(self):
        tool = get_tool("document/pdf_extract_text")
        content_param = [p for p in tool["parameters"] if p["name"] == "content"][0]
        assert "base64" in content_param["description"].lower()

    async def test_execute_decodes_base64(self):
        raw = b"pdf-content"
        encoded = base64.b64encode(raw).decode()

        @dataclass
        class FakeResult:
            success: bool = True
            text: str = "hello"
            page_count: int = 1
            chunks: list = field(default_factory=list)
            error: str = None

        mock_svc = MagicMock()
        mock_svc.process = AsyncMock(return_value=FakeResult())
        mock_mod = MagicMock()
        mock_mod.get_pdf_processor.return_value = mock_svc

        tool_def = get_tool("document/pdf_process")

        with patch("app.common.tools.registry.importlib.import_module", return_value=mock_mod):
            result = await execute_tool(tool_def, {"content": encoded})

        mock_svc.process.assert_called_once_with(content=raw)
        assert result["success"] is True


# ---------------------------------------------------------------------------
# TestEmbeddingsTools
# ---------------------------------------------------------------------------

@pytest.mark.mcp
class TestEmbeddingsTools:
    def test_category_exists(self):
        assert "embeddings" in CATEGORIES

    def test_all_three_tools_exist(self):
        ids = {t["tool_id"] for t in TOOL_REGISTRY}
        assert "embeddings/embed_text" in ids
        assert "embeddings/embed_texts" in ids
        assert "embeddings/health_check" in ids
