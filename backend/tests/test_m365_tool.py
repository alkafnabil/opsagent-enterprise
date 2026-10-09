import pytest
from app.tools.m365_tool import M365Tool


@pytest.mark.asyncio
async def test_m365_tool_check_availability():
    tool = M365Tool()
    res = await tool.execute(action="check_availability", user_email="ops@nusantaracoal.com")
    assert res.is_success is True
    assert isinstance(res.output, dict)
    assert "available_slots" in res.output
    assert len(res.output["available_slots"]) >= 1


@pytest.mark.asyncio
async def test_m365_tool_create_event():
    tool = M365Tool()
    res = await tool.execute(
        action="create_calendar_event",
        event_subject="Koordinasi Laycan Tongkang Palaran",
        location="Jetty Palaran Room A",
    )
    assert res.is_success is True
    assert res.output["status"] == "SUCCESS"
    assert "event" in res.output
    assert "EVT-" in res.output["event"]["event_id"]


@pytest.mark.asyncio
async def test_m365_tool_draft_email():
    tool = M365Tool()
    res = await tool.execute(
        action="draft_email",
        subject="Shipping Advice Tongkang BG Trans Coal 301",
        to_recipients=["buyer@plnepi.co.id"],
        body_text="Tongkang telah selesai loading 7.850 MT batubara GAR 4200.",
    )
    assert res.is_success is True
    assert res.output["status"] == "SUCCESS"
    assert "draft" in res.output
    assert res.output["draft"]["status"] == "DRAFT_SAVED"
