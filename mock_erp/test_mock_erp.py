from datetime import date, timedelta
import pytest
from fastapi.testclient import TestClient
from mock_erp.main import app

client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "mock_erp"


def test_list_inventory():
    response = client.get("/api/v1/inventory")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 5
    first = data[0]
    assert "stockpile_name" in first
    assert "grade" in first
    assert "tonnage_available_mt" in first


def test_filter_inventory_by_grade():
    response = client.get("/api/v1/inventory?grade=5000")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    for item in data:
        assert "5000" in item["grade"]


def test_get_inventory_by_stockpile_not_found():
    response = client.get("/api/v1/inventory/999")
    assert response.status_code == 404
    assert "tidak ditemukan" in response.json()["detail"]


def test_list_purchase_orders():
    response = client.get("/api/v1/purchase-orders")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2


def test_get_purchase_order_by_number():
    response = client.get("/api/v1/purchase-orders/PO-2026-0089")
    assert response.status_code == 200
    data = response.json()
    assert data["po_number"] == "PO-2026-0089"
    assert data["status"] == "APPROVED"
    assert data["supplier_code"] == "SUP-KPC-01"


def test_create_and_approve_draft_purchase_order():
    # 1. Create draft PO
    payload = {
        "supplier_code": "SUP-MBL-04",
        "supplier_name": "PT Mitra Batubara Kalsel",
        "delivery_jetty": "Trisakti Port, Banjarmasin",
        "target_delivery_date": str(date.today() + timedelta(days=10)),
        "items": [
            {
                "item_id": "ITM-TST-01",
                "grade": "GAR 4200",
                "quantity_mt": 7500.0,
                "unit_price_usd": 57.5,
                "total_amount_usd": 431250.0,
            }
        ],
        "notes": "Testing pembuatan Draft PO untuk alokasi PLN",
        "created_by": "staff_budi",
    }
    create_res = client.post("/api/v1/purchase-orders", json=payload)
    assert create_res.status_code == 201
    created_po = create_res.json()
    po_number = created_po["po_number"]
    assert created_po["status"] == "DRAFT"
    assert created_po["requires_approval"] is True
    assert created_po["approval_status"] == "PENDING"
    assert created_po["total_tonnage_mt"] == 7500.0

    # 2. Approve draft PO
    approval_payload = {
        "approved_by": "MGR-SANTOSO",
        "approval_notes": "Disetujui untuk memenuhi kuota pasokan",
    }
    approve_res = client.post(f"/api/v1/purchase-orders/{po_number}/approve", json=approval_payload)
    assert approve_res.status_code == 200
    approved_po = approve_res.json()
    assert approved_po["status"] == "APPROVED"
    assert approved_po["approval_status"] == "APPROVED"
    assert approved_po["approved_by"] == "MGR-SANTOSO"


def test_list_invoices_and_overdue_filter():
    response = client.get("/api/v1/invoices?overdue_only=true")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    for inv in data:
        assert inv["payment_status"] == "OVERDUE"
        assert inv["days_overdue"] > 0


def test_get_invoice_detail():
    response = client.get("/api/v1/invoices/INV-2026-0045")
    assert response.status_code == 200
    inv = response.json()
    assert inv["invoice_number"] == "INV-2026-0045"
    assert inv["customer_code"] == "CUST-PLN-01"


def test_list_shipments():
    response = client.get("/api/v1/shipments")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2
    first = data[0]
    assert "shipment_number" in first
    assert "barge_name" in first
    assert "status" in first
