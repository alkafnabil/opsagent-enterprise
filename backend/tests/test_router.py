import pytest
from app.agent.router import IntentRouter
from app.agent.llm_provider import LLMProvider


@pytest.mark.asyncio
async def test_router_classification_and_latency():
    router = IntentRouter(LLMProvider())

    # 1. SQL Query intent
    intent_sql, conf_sql, lat_sql = await router.route_query("Berapa tonase sisa batubara di Stockpile Palaran?")
    assert intent_sql == "sql_query"
    assert conf_sql >= 0.8
    assert lat_sql < 350.0  # Ultra-fast routing check

    # 2. ERP API intent
    intent_erp, _, _ = await router.route_query("Tolong buat draft PO batubara 5000 MT untuk PT Kaltim Prima")
    assert intent_erp == "erp_api"

    # 3. M365 intent
    intent_m365, _, _ = await router.route_query("Cek jadwal kosong kalender untuk rapat koordinasi sandar kapal")
    assert intent_m365 == "m365"

    # 4. Search Docs SOP intent
    intent_sop, _, _ = await router.route_query("Bagaimana prosedur SOP mitigasi jika batubara mengeluarkan asap?")
    assert intent_sop == "search_docs"

    # 5. Out of scope intent
    intent_out, _, _ = await router.route_query("Bagikan resep memasak rendang daging sapi khas Padang")
    assert intent_out == "out_of_scope"
