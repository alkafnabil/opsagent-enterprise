import pytest
from app.tools.erp_tool import ERPTool


@pytest.mark.asyncio
async def test_erp_tool_get_inventory():
    tool = ERPTool()
    res = await tool.execute(action="get_inventory", grade="4200")
    assert res.is_success is True
    assert isinstance(res.output, list)
    assert len(res.output) >= 1
    assert any("4200" in item.get("grade", "") for item in res.output)


@pytest.mark.asyncio
async def test_erp_tool_get_invoices():
    tool = ERPTool()
    res = await tool.execute(action="get_invoices", overdue_only=True)
    assert res.is_success is True
    assert isinstance(res.output, list)
    assert len(res.output) >= 1
    for inv in res.output:
        assert inv["payment_status"] == "OVERDUE"


@pytest.mark.asyncio
async def test_erp_tool_create_po_draft_flags_approval():
    tool = ERPTool()
    res = await tool.execute(
        action="create_po_draft",
        supplier_code="SUP-KPC-01",
        supplier_name="PT Kaltim Prima Mining Concession",
        delivery_jetty="Palaran Jetty, Samarinda",
        grade="GAR 4200",
        quantity_mt=8000.0,
        unit_price_usd=58.0,
        user_role="staff",
    )
    assert res.is_success is True
    assert isinstance(res.output, dict)
    assert "po_number" in res.output
    assert res.output["status"] == "DRAFT"
    # Crucial check: must flag requires_approval
    assert res.requires_approval is True
    assert res.output["requires_approval"] is True
