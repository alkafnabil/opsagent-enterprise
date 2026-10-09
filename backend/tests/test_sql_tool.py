import pytest
from app.tools.sql_tool import SQLQueryTool, SQLValidationException


@pytest.mark.asyncio
async def test_sql_tool_valid_select():
    tool = SQLQueryTool()
    res = await tool.execute(query="SELECT * FROM stockpiles")
    assert res.is_success is True
    assert isinstance(res.output, list)
    assert len(res.output) >= 1
    assert "stockpile_name" in res.output[0]


@pytest.mark.asyncio
async def test_sql_tool_limit_injection():
    tool = SQLQueryTool()
    # Query without limit
    sanitized = tool.validate_and_sanitize_query("SELECT stockpile_name FROM stockpiles")
    assert "LIMIT 50" in sanitized

    # Query with excessive limit clamped to 50
    sanitized2 = tool.validate_and_sanitize_query("SELECT stockpile_name FROM stockpiles LIMIT 500")
    assert "LIMIT 50" in sanitized2


@pytest.mark.asyncio
async def test_sql_tool_rejects_mutation_and_ddl():
    tool = SQLQueryTool()
    
    # Prohibit DROP
    res_drop = await tool.execute(query="DROP TABLE stockpiles")
    assert res_drop.is_success is False
    assert "Hanya query dengan perintah 'SELECT'" in res_drop.error_message or "terlarang" in res_drop.error_message

    # Prohibit DELETE
    res_del = await tool.execute(query="DELETE FROM customers WHERE id=1")
    assert res_del.is_success is False

    # Prohibit INSERT
    res_ins = await tool.execute(query="INSERT INTO barges VALUES (1, 'BG-999')")
    assert res_ins.is_success is False


@pytest.mark.asyncio
async def test_sql_tool_rejects_non_allowlisted_tables():
    tool = SQLQueryTool()
    # Attempt to query non-allowlisted system table
    res = await tool.execute(query="SELECT * FROM pg_user")
    assert res.is_success is False
    assert "allowlist" in res.error_message.lower()


@pytest.mark.asyncio
async def test_sql_tool_rejects_multi_statements():
    tool = SQLQueryTool()
    # Multiple statements separated by semicolon
    res = await tool.execute(query="SELECT * FROM stockpiles; SELECT * FROM customers")
    assert res.is_success is False
    assert "Multi-statement" in res.error_message
