from __future__ import annotations
from datetime import datetime, date
from typing import List, Optional, Literal
from pydantic import BaseModel, Field, field_validator


# ==============================================================================
# Inventory Models
# ==============================================================================
class InventoryItem(BaseModel):
    id: int
    stockpile_id: int
    stockpile_code: str
    stockpile_name: str
    location: str
    grade: str
    gar_kcal: int
    tonnage_available_mt: float = Field(..., ge=0)
    reserved_mt: float = Field(0.0, ge=0)
    total_moisture_pct: float
    total_sulfur_pct: float
    unit_price_usd_per_mt: float
    status: Literal["AVAILABLE", "RESERVED", "LOW_STOCK"]
    updated_at: datetime


# ==============================================================================
# Purchase Order Models
# ==============================================================================
class PurchaseOrderItem(BaseModel):
    item_id: str
    grade: str = Field(..., description="Coal grade, e.g. 'GAR 4200'")
    quantity_mt: float = Field(..., gt=0, description="Quantity in metric tons")
    unit_price_usd: float = Field(..., gt=0, description="Price per MT in USD")
    total_amount_usd: float = Field(..., gt=0, description="Total amount in USD")

    @field_validator("total_amount_usd", mode="before")
    def calculate_or_validate_total(cls, v, values):
        return v


class PurchaseOrderCreate(BaseModel):
    supplier_code: str = Field(..., min_length=3, description="Kode supplier, e.g. SUP-KPC-01")
    supplier_name: str = Field(..., min_length=3, description="Nama perusahaan supplier tambang")
    delivery_jetty: str = Field(..., min_length=3, description="Jetty bongkar/muat yang dituju")
    target_delivery_date: date = Field(..., description="Target tanggal pengiriman")
    items: List[PurchaseOrderItem] = Field(..., min_length=1, description="Daftar item batubara yang dipesan")
    notes: Optional[str] = Field(None, max_length=500, description="Catatan operasional tambahan")
    created_by: str = Field("staff", description="User pembuat dokumen")


class PurchaseOrderApprove(BaseModel):
    approved_by: str = Field(..., min_length=3, description="Nama / ID manager yang menyetujui")
    approval_notes: Optional[str] = Field(None, description="Catatan verifikasi approval")


class PurchaseOrderResponse(BaseModel):
    po_number: str
    supplier_code: str
    supplier_name: str
    delivery_jetty: str
    target_delivery_date: date
    items: List[PurchaseOrderItem]
    total_tonnage_mt: float
    total_amount_usd: float
    status: Literal["DRAFT", "APPROVED", "IN_DELIVERY", "FULFILLED", "CANCELLED"]
    requires_approval: bool = True
    approval_status: Literal["PENDING", "APPROVED", "REJECTED"]
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    notes: Optional[str] = None
    created_by: str
    created_at: datetime


# ==============================================================================
# Invoice Models
# ==============================================================================
class InvoiceResponse(BaseModel):
    invoice_number: str
    customer_code: str
    customer_name: str
    po_reference: str
    shipment_number: Optional[str] = None
    coal_grade: str
    tonnage_mt: float
    subtotal_usd: float
    tax_usd: float
    total_amount_usd: float
    issue_date: date
    due_date: date
    payment_status: Literal["PAID", "UNPAID", "OVERDUE"]
    days_overdue: int = 0
    paid_at: Optional[datetime] = None
    notes: Optional[str] = None


# ==============================================================================
# Shipment Models
# ==============================================================================
class ShipmentResponse(BaseModel):
    shipment_number: str
    barge_code: str
    barge_name: str
    tugboat_name: str
    customer_name: str
    coal_grade: str
    tonnage_loaded_mt: float
    origin_jetty: str
    destination_port: str
    status: Literal["LOADING", "SAILING", "DISCHARGING", "COMPLETED", "ANCHORED"]
    etd: datetime
    eta: datetime
    surveyor_company: str
