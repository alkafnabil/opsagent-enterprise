import pytest
from app.agent.orchestrator import AgentOrchestrator
from app.core.audit import AuditService


@pytest.mark.asyncio
async def test_orchestrator_sql_stream_flow():
    orchestrator = AgentOrchestrator()
    events = []
    tokens = []

    async for evt in orchestrator.run_query_stream(
        user_query="Cek sisa stok batubara di Stockpile Palaran",
        user_role="staff",
        user_id="USR-TEST-01",
    ):
        events.append(evt["event"])
        if evt["event"] == "token":
            tokens.append(evt["data"])
        elif evt["event"] == "done":
            done_state = evt["data"]

    assert "trace_init" in events
    assert "router_step" in events
    assert "tool_call" in events
    assert "tool_result" in events
    assert "token" in events
    assert "done" in events
    assert len(tokens) >= 5

    assert done_state["routed_intent"] == "sql_query"
    assert done_state["execution_status"] == "SUCCESS"
    assert done_state["total_tokens"] > 0
    assert "router" in done_state["step_latencies"]


@pytest.mark.asyncio
async def test_orchestrator_approval_flow_on_write():
    orchestrator = AgentOrchestrator()
    events = []
    approval_data = None

    async for evt in orchestrator.run_query_stream(
        user_query="Tolong buat PO batubara 7500 MT ke supplier KPC",
        user_role="staff",
    ):
        events.append(evt["event"])
        if evt["event"] == "approval_required":
            approval_data = evt["data"]
        elif evt["event"] == "done":
            done_state = evt["data"]

    assert "approval_required" in events
    assert approval_data is not None
    assert approval_data["action_type"] == "CREATE_PURCHASE_ORDER"
    assert done_state["requires_approval"] is True
    assert done_state["execution_status"] == "PENDING_APPROVAL"


@pytest.mark.asyncio
async def test_orchestrator_out_of_scope_rejection():
    orchestrator = AgentOrchestrator()
    events = []

    async for evt in orchestrator.run_query_stream(
        user_query="Apa resep membuat rendang Padang?",
    ):
        events.append(evt["event"])
        if evt["event"] == "done":
            done_state = evt["data"]

    assert "router_step" in events
    assert "done" in events
    assert done_state["routed_intent"] == "out_of_scope"
    assert done_state["execution_status"] == "REJECTED"
    assert done_state["is_flagged"] is True
