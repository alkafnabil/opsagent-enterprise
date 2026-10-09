from __future__ import annotations
import asyncio
import time
import logging
from typing import Any, Dict, Optional, Type
from pydantic import BaseModel, Field, ConfigDict

logger = logging.getLogger(__name__)


class ToolResult(BaseModel):
    tool_name: str
    arguments: Dict[str, Any]
    output: Any
    is_success: bool = True
    error_message: Optional[str] = None
    latency_ms: float = 0.0
    summary: str = ""
    requires_approval: bool = False
    pending_approval_data: Optional[Dict[str, Any]] = None


class BaseTool(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: str = Field(..., description="Tool unique name identifier")
    description: str = Field(..., description="Description for LLM tool selection")
    args_schema: Type[BaseModel] = Field(..., description="Pydantic model defining argument schema")
    timeout_seconds: float = Field(10.0, description="Execution timeout in seconds")
    max_retries: int = Field(2, description="Maximum number of retries on network/transient failure")

    def get_json_schema(self) -> Dict[str, Any]:
        """Generate JSON schema format standard for LLM tool calling (OpenAI/Groq compatible)."""
        properties = {}
        required = []
        schema = self.args_schema.model_json_schema()

        for field_name, field_info in schema.get("properties", {}).items():
            properties[field_name] = {
                "type": field_info.get("type", "string"),
                "description": field_info.get("description", ""),
            }
            if "enum" in field_info:
                properties[field_name]["enum"] = field_info["enum"]

        required = schema.get("required", [])

        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required,
                },
            },
        }

    async def execute(self, **kwargs) -> ToolResult:
        """Execute the tool with validation, timeout, retry, and latency measurement."""
        start_time = time.perf_counter()
        
        # 1. Pydantic validation of arguments
        try:
            validated_args = self.args_schema(**kwargs)
        except Exception as val_err:
            latency = (time.perf_counter() - start_time) * 1000.0
            logger.error(f"Validation error in tool '{self.name}': {val_err}")
            return ToolResult(
                tool_name=self.name,
                arguments=kwargs,
                output=None,
                is_success=False,
                error_message=f"Validasi argumen gagal: {str(val_err)}",
                latency_ms=round(latency, 2),
                summary="Gagal validasi parameter input.",
            )

        # 2. Execution with retry and timeout
        attempt = 0
        last_error = None
        while attempt <= self.max_retries:
            attempt += 1
            try:
                output = await asyncio.wait_for(
                    self._run(validated_args),
                    timeout=self.timeout_seconds,
                )
                latency = (time.perf_counter() - start_time) * 1000.0

                summary = self._summarize_output(output)
                req_approval = False
                if isinstance(output, dict):
                    req_approval = bool(output.get("requires_approval", False))
                elif hasattr(output, "requires_approval"):
                    req_approval = bool(getattr(output, "requires_approval", False))
                
                return ToolResult(
                    tool_name=self.name,
                    arguments=kwargs,
                    output=output,
                    is_success=True,
                    latency_ms=round(latency, 2),
                    summary=summary,
                    requires_approval=req_approval,
                )
            except asyncio.TimeoutError:
                last_error = f"Timeout ({self.timeout_seconds}s) terlampaui saat memanggil tool '{self.name}'."
                logger.warning(f"Attempt {attempt} timed out for tool '{self.name}'")
            except Exception as exc:
                last_error = str(exc)
                logger.warning(f"Attempt {attempt} failed for tool '{self.name}': {exc}")

            if attempt <= self.max_retries:
                await asyncio.sleep(0.5 * attempt)

        latency = (time.perf_counter() - start_time) * 1000.0
        return ToolResult(
            tool_name=self.name,
            arguments=kwargs,
            output=None,
            is_success=False,
            error_message=f"Eksekusi gagal setelah {attempt} percobaan: {last_error}",
            latency_ms=round(latency, 2),
            summary=f"Gagal memanggil {self.name}: {last_error}",
        )

    async def _run(self, args: Any) -> Any:
        raise NotImplementedError("Subclass must implement _run method.")

    def _summarize_output(self, output: Any) -> str:
        """Create a short, human-readable summary of tool execution for the audit log & UI trace."""
        if isinstance(output, list):
            return f"Berhasil mendapatkan {len(output)} rekaman data."
        elif isinstance(output, dict):
            return f"Berhasil memproses data: {list(output.keys())[:3]}"
        return str(output)[:120]
