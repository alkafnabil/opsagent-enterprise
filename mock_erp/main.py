from __future__ import annotations
import os
import time
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Query, Header, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .models import (
    InventoryItem,
    PurchaseOrderCreate,
    PurchaseOrderResponse,
    PurchaseOrderApprove,
    InvoiceResponse,
    ShipmentResponse,
)
from .database import (
    get_all_inventory,
    get_all_purchase_orders,
    get_purchase_order_by_number,
    create_draft_purchase_order,
    approve_purchase_order,
    get_all_invoices,
    get_invoice_by_number,
    get_all_shipments,
)

app = FastAPI(
    title="PT Nusantara Coal Operations - Mock ERP API",
    description="Stand-alone mock ERP service providing Purchase Order, Inventory, Invoice, and Shipment endpoints for OpsAgent.",
    version="1.0.0",
)

# Enable CORS for local development and backend/frontend containers
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ERP_API_KEY = os.getenv("ERP_API_KEY", "mock-erp-secret-key-2026")


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.perf_counter()
    response = await call_next(request)
    process_time = (time.perf_counter() - start_time) * 1000.0
    response.headers["X-Process-Time-Ms"] = f"{process_time:.2f}"
    return response


# ==============================================================================
# Health Check Endpoint
# ==============================================================================
@app.get("/health", tags=["System"])
async def health_check():
    return {
        "status": "ok",
        "service": "mock_erp",
        "version": "1.0.0",
        "environment": os.getenv("APP_ENV", "development"),
    }


# ==============================================================================
# Inventory Endpoints
# ==============================================================================
@app.get("/api/v1/inventory", response_model=List[InventoryItem], tags=["Inventory"])
async def list_inventory(
    stockpile_id: Optional[int] = Query(None, description="Filter by stockpile ID"),
    grade: Optional[str] = Query(None, description="Filter by coal grade (e.g. 'GAR 4200')"),
    min_tonnage: Optional[float] = Query(None, description="Minimum available tonnage MT"),
):
    """Retrieve operational coal inventory across all stockpiles and jetties."""
    items = get_all_inventory(stockpile_id=stockpile_id, grade=grade, min_tonnage=min_tonnage)
    return items


@app.get("/api/v1/inventory/{stockpile_id}", response_model=List[InventoryItem], tags=["Inventory"])
async def get_inventory_by_stockpile(stockpile_id: int):
    """Retrieve all inventory batches for a specific stockpile ID."""
    items = get_all_inventory(stockpile_id=stockpile_id)
    if not items:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Data inventory untuk stockpile ID {stockpile_id} tidak ditemukan.",
        )
    return items


# ==============================================================================
# Purchase Orders Endpoints
# ==============================================================================
@app.get("/api/v1/purchase-orders", response_model=List[PurchaseOrderResponse], tags=["Purchase Orders"])
async def list_purchase_orders(
    status_filter: Optional[str] = Query(None, alias="status", description="Filter status: DRAFT, APPROVED, FULFILLED"),
    supplier_code: Optional[str] = Query(None, description="Filter by supplier code (e.g. SUP-KPC-01)"),
):
    """List purchase orders with optional filtering."""
    return get_all_purchase_orders(status=status_filter, supplier_code=supplier_code)


@app.get("/api/v1/purchase-orders/{po_number}", response_model=PurchaseOrderResponse, tags=["Purchase Orders"])
async def get_purchase_order(po_number: str):
    """Retrieve single purchase order details by PO number."""
    po = get_purchase_order_by_number(po_number)
    if not po:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Purchase Order dengan nomor '{po_number}' tidak ditemukan.",
        )
    return po


@app.post(
    "/api/v1/purchase-orders",
    response_model=PurchaseOrderResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Purchase Orders"],
)
async def create_purchase_order(data: PurchaseOrderCreate):
    """
    Create a new DRAFT Purchase Order.
    Per operational SOP-PROC-003, newly created POs are always set to DRAFT
    and must be approved by a Manager before becoming legally binding.
    """
    new_po = create_draft_purchase_order(data)
    return new_po


@app.post(
    "/api/v1/purchase-orders/{po_number}/approve",
    response_model=PurchaseOrderResponse,
    tags=["Purchase Orders"],
)
async def approve_po_endpoint(po_number: str, approval_data: PurchaseOrderApprove):
    """
    Approve a DRAFT Purchase Order (Manager role action).
    Changes status to APPROVED and records the approver metadata.
    """
    po = get_purchase_order_by_number(po_number)
    if not po:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Purchase Order '{po_number}' tidak ditemukan.",
        )
    if po.status == "APPROVED":
        return po

    updated_po = approve_purchase_order(
        po_number=po_number,
        approved_by=approval_data.approved_by,
        notes=approval_data.approval_notes,
    )
    return updated_po


# ==============================================================================
# Invoices Endpoints
# ==============================================================================
@app.get("/api/v1/invoices", response_model=List[InvoiceResponse], tags=["Invoices"])
async def list_invoices(
    payment_status: Optional[str] = Query(None, description="Filter status: UNPAID, PAID, OVERDUE"),
    customer_code: Optional[str] = Query(None, description="Filter by customer code (e.g. CUST-SMN-01)"),
    overdue_only: bool = Query(False, description="Filter only overdue invoices"),
):
    """List customer sales invoices."""
    return get_all_invoices(
        payment_status=payment_status,
        customer_code=customer_code,
        overdue_only=overdue_only,
    )


@app.get("/api/v1/invoices/{invoice_number}", response_model=InvoiceResponse, tags=["Invoices"])
async def get_invoice(invoice_number: str):
    """Get single invoice details by invoice number."""
    inv = get_invoice_by_number(invoice_number)
    if not inv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invoice dengan nomor '{invoice_number}' tidak ditemukan.",
        )
    return inv


# ==============================================================================
# Shipments Endpoints
# ==============================================================================
@app.get("/api/v1/shipments", response_model=List[ShipmentResponse], tags=["Shipments"])
async def list_shipments(
    status_filter: Optional[str] = Query(None, alias="status", description="Filter status: SAILING, LOADING, COMPLETED"),
    customer_name: Optional[str] = Query(None, description="Filter by customer name"),
):
    """List operational barge shipments and marine transit status."""
    return get_all_shipments(status=status_filter, customer_name=customer_name)


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("MOCK_ERP_PORT", 8001))
    uvicorn.run("mock_erp.main:app", host="0.0.0.0", port=port, reload=True)
