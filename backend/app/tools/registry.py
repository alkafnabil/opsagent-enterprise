from __future__ import annotations
from typing import Dict, List, Any, Optional
from app.tools.base import BaseTool, ToolResult
from app.tools.sql_tool import SQLQueryTool
from app.tools.erp_tool import ERPTool
from app.tools.m365_tool import M365Tool
from app.tools.rag_tool import SearchDocsTool


class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}
        # Register standard 4 tools
        self.register(SQLQueryTool())
        self.register(ERPTool())
        self.register(M365Tool())
        self.register(SearchDocsTool())

    def register(self, tool: BaseTool) -> None:
        self._tools[tool.name] = tool

    def get_tool(self, name: str) -> Optional[BaseTool]:
        return self._tools.get(name)

    def get_all_tools(self) -> List[BaseTool]:
        return list(self._tools.values())

    def get_tools_schemas(self) -> List[Dict[str, Any]]:
        """Returns JSON schemas for LLM native tool calling."""
        return [tool.get_json_schema() for tool in self._tools.values()]


_default_registry = ToolRegistry()


def get_tool_registry() -> ToolRegistry:
    return _default_registry
