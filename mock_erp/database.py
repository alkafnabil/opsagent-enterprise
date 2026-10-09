from __future__ import annotations
from datetime import datetime, date, timedelta, timezone
from typing import List, Optional, Dict
import threading
from .models import (
    InventoryItem,
    PurchaseOrderCreate,
    PurchaseOrderResponse,
    PurchaseOrderItem,
    InvoiceResponse,
    ShipmentResponse,
)

# Thread lock for mock database mutations
_lock = threading.Lock()

# Initial Seed Data
_INVENTORY_DB: List[InventoryItem] = [
    InventoryItem(
        id=1,
        stockpile_id=1,
        stockpile_code="STK-PLR-01",
        stockpile_name="Stockpile Palaran Jetty",
        location="Palaran, Samarinda",
        grade="GAR 4200",
        gar_kcal=4210,
        tonnage_available_mt=42500.0,
        reserved_mt=5000.0,
        total_moisture_pct=34.2,
        total_sulfur_pct=0.42,
        unit_price_usd_per_mt=58.50,
        status="AVAILABLE",
        updated_at=datetime.now(timezone.utc) - timedelta(hours=2),
    ),
    InventoryItem(
        id=2,
        stockpile_id=1,
        stockpile_code="STK-PLR-01",
        stockpile_name="Stockpile Palaran Jetty",
        location="Palaran, Samarinda",
        grade="GAR 5000",
        gar_kcal=5025,
        tonnage_available_mt=42000.0,
        reserved_mt=0.0,
        total_moisture_pct=26.5,
        total_sulfur_pct=0.65,
        unit_price_usd_per_mt=76.00,
        status="AVAILABLE",
        updated_at=datetime.now(timezone.utc) - timedelta(hours=3),
    ),
    InventoryItem(
        id=3,
        stockpile_id=2,
        stockpile_code="STK-KRG-02",
        stockpile_name="Stockpile Kariangau Interport",
        location="Kariangau, Balikpapan",
        grade="GAR 3800",
        gar_kcal=3820,
        tonnage_available_mt=95000.0,
        reserved_mt=15000.0,
        total_moisture_pct=38.0,
        total_sulfur_pct=0.35,
        unit_price_usd_per_mt=49.00,
        status="AVAILABLE",
        updated_at=datetime.now(timezone.utc) - timedelta(hours=5),
    ),
    InventoryItem(
        id=4,
        stockpile_id=2,
        stockpile_code="STK-KRG-02",
        stockpile_name="Stockpile Kariangau Interport",
        location="Kariangau, Balikpapan",
        grade="GAR 4200",
        gar_kcal=4190,
        tonnage_available_mt=97000.0,
        reserved_mt=20000.0,
        total_moisture_pct=34.8,
        total_sulfur_pct=0.38,
        unit_price_usd_per_mt=59.00,
        status="AVAILABLE",
        updated_at=datetime.now(timezone.utc) - timedelta(hours=1),
    ),
    InventoryItem(
        id=5,
        stockpile_id=3,
        stockpile_code="STK-TSK-03",
        stockpile_name="Stockpile Trisakti Port",
        location="Trisakti, Banjarmasin",
        grade="GAR 4200",
        gar_kcal=4220,
        tonnage_available_mt=37200.0,
        reserved_mt=0.0,
        total_moisture_pct=33.9,
        total_sulfur_pct=0.45,
        unit_price_usd_per_mt=58.00,
        status="AVAILABLE",
        updated_at=datetime.now(timezone.utc) - timedelta(hours=4),
    ),
    InventoryItem(
        id=6,
        stockpile_id=4,
        stockpile_code="STK-MTW-04",
        stockpile_name="Stockpile Muara Teweh Riverbank",
        location="Muara Teweh, Barito Utara",
        grade="GAR 3800",
        gar_kcal=3790,
        tonnage_available_mt=31800.0,
        reserved_mt=0.0,
        total_moisture_pct=38.5,
        total_sulfur_pct=0.30,
        unit_price_usd_per_mt=47.50,
        status="AVAILABLE",
        updated_at=datetime.now(timezone.utc) - timedelta(hours=6),
    ),
    InventoryItem(
        id=7,
        stockpile_id=5,
        stockpile_code="STK-TBN-05",
        stockpile_name="Taboneo Transhipment Anchorage",
        location="Perairan Taboneo, Kalsel",
        grade="GAR 4200",
        gar_kcal=4205,
        tonnage_available_mt=180500.0,
        reserved_mt=45000.0,
        total_moisture_pct=34.0,
        total_sulfur_pct=0.40,
        unit_price_usd_per_mt=60.00,
        status="AVAILABLE",
        updated_at=datetime.now(timezone.utc) - timedelta(minutes=45),
    ),
]

_PURCHASE_ORDERS_DB: Dict[str, PurchaseOrderResponse] = {
    "PO-2026-0089": PurchaseOrderResponse(
        po_number="PO-2026-0089",
        supplier_code="SUP-KPC-01",
        supplier_name="PT Kaltim Prima Mining Concession",
        delivery_jetty="Palaran Jetty, Samarinda",
        target_delivery_date=date.today() + timedelta(days=7),
        items=[
            PurchaseOrderItem(
                item_id="ITM-01",
                grade="GAR 4200",
                quantity_mt=15000.0,
                unit_price_usd=56.0,
                total_amount_usd=840000.0,
            )
        ],
        total_tonnage_mt=15000.0,
        total_amount_usd=840000.0,
        status="APPROVED",
        requires_approval=True,
        approval_status="APPROVED",
        approved_by="MGR-HENDRA",
        approved_at=datetime.now(timezone.utc) - timedelta(days=2),
        notes="Pengadaan rutin pasokan PLTU Suralaya kuartal II",
        created_by="staff_dimas",
        created_at=datetime.now(timezone.utc) - timedelta(days=3),
    ),
    "PO-2026-0090": PurchaseOrderResponse(
        po_number="PO-2026-0090",
        supplier_code="SUP-BRU-02",
        supplier_name="PT Berau Coal Perkasa",
        delivery_jetty="Kariangau Interport, Balikpapan",
        target_delivery_date=date.today() + timedelta(days=12),
        items=[
            PurchaseOrderItem(
                item_id="ITM-02",
                grade="GAR 5000",
                quantity_mt=10000.0,
                unit_price_usd=73.5,
                total_amount_usd=735000.0,
            )
        ],
        total_tonnage_mt=10000.0,
        total_amount_usd=735000.0,
        status="DRAFT",
        requires_approval=True,
        approval_status="PENDING",
        approved_by=None,
        approved_at=None,
        notes="Menunggu COA validasi lab dari pit central Lati",
        created_by="staff_dimas",
        created_at=datetime.now(timezone.utc) - timedelta(hours=4),
    ),
}

_INVOICES_DB: List[InvoiceResponse] = [
    InvoiceResponse(
        invoice_number="INV-2026-0045",
        customer_code="CUST-PLN-01",
        customer_name="PT PLN Energi Primer Indonesia",
        po_reference="PO-PLN-2026-Q1-01",
        shipment_number="SHP-2026-0390",
        coal_grade="GAR 4200",
        tonnage_mt=7800.0,
        subtotal_usd=456300.0,
        tax_usd=50193.0,
        total_amount_usd=506493.0,
        issue_date=date.today() - timedelta(days=20),
        due_date=date.today() + timedelta(days=25),
        payment_status="UNPAID",
        days_overdue=0,
        notes="Pengiriman ke PLTU Suralaya",
    ),
    InvoiceResponse(
        invoice_number="INV-2026-0038",
        customer_code="CUST-SMN-01",
        customer_name="PT Semen Indonesia (Persero) Tbk",
        po_reference="PO-SIG-2026-FEB-10",
        shipment_number="SHP-2026-0382",
        coal_grade="GAR 5000",
        tonnage_mt=6500.0,
        subtotal_usd=494000.0,
        tax_usd=54340.0,
        total_amount_usd=548340.0,
        issue_date=date.today() - timedelta(days=45),
        due_date=date.today() - timedelta(days=15),
        payment_status="OVERDUE",
        days_overdue=15,
        notes="SP-1 telah dikirim ke Keuangan SIG Tuban per SOP-FIN-004",
    ),
    InvoiceResponse(
        invoice_number="INV-2026-0032",
        customer_code="CUST-NCK-01",
        customer_name="PT Gunbuster Nickel Industry",
        po_reference="PO-GNI-2026-FEB-01",
        shipment_number="SHP-2026-0370",
        coal_grade="GAR 4200",
        tonnage_mt=8200.0,
        subtotal_usd=479700.0,
        tax_usd=52767.0,
        total_amount_usd=532467.0,
        issue_date=date.today() - timedelta(days=35),
        due_date=date.today() - timedelta(days=21),
        payment_status="PAID",
        days_overdue=0,
        paid_at=datetime.now(timezone.utc) - timedelta(days=20),
        notes="Lunas via SKBDN Mandiri",
    ),
    InvoiceResponse(
        invoice_number="INV-2026-0048",
        customer_code="CUST-NCK-02",
        customer_name="PT Huadi Nickel-Alloy Indonesia",
        po_reference="PO-HND-2026-MAR-05",
        shipment_number="SHP-2026-0398",
        coal_grade="GAR 4200",
        tonnage_mt=7950.0,
        subtotal_usd=469050.0,
        tax_usd=51595.5,
        total_amount_usd=520645.5,
        issue_date=date.today() - timedelta(days=10),
        due_date=date.today() + timedelta(days=4),
        payment_status="UNPAID",
        days_overdue=0,
        notes="Bantaeng Jetty shipment",
    ),
]

_SHIPMENTS_DB: List[ShipmentResponse] = [
    ShipmentResponse(
        shipment_number="SHP-2026-0401",
        barge_code="BG-301",
        barge_name="BG Trans Coal 301",
        tugboat_name="TB Rajawali 08",
        customer_name="PT PLN Energi Primer Indonesia",
        coal_grade="GAR 4200",
        tonnage_loaded_mt=7850.0,
        origin_jetty="Palaran Jetty, Samarinda",
        destination_port="Pelabuhan PLTU Suralaya, Banten",
        status="SAILING",
        etd=datetime.now(timezone.utc) - timedelta(days=3),
        eta=datetime.now(timezone.utc) + timedelta(days=2),
        surveyor_company="PT Carsurin",
    ),
    ShipmentResponse(
        shipment_number="SHP-2026-0402",
        barge_code="BG-330",
        barge_name="BG Nusantara 330",
        tugboat_name="TB Mega Marine 02",
        customer_name="PT Pembangkitan Jawa Bali (PJB)",
        coal_grade="GAR 5000",
        tonnage_loaded_mt=10200.0,
        origin_jetty="Kariangau Interport, Balikpapan",
        destination_port="Pelabuhan PLTU Paiton, Jawa Timur",
        status="SAILING",
        etd=datetime.now(timezone.utc) - timedelta(days=2),
        eta=datetime.now(timezone.utc) + timedelta(days=3),
        surveyor_company="PT Surveyor Indonesia",
    ),
    ShipmentResponse(
        shipment_number="SHP-2026-0403",
        barge_code="BG-280",
        barge_name="BG Mahakam Jaya 280",
        tugboat_name="TB Borneo Star 05",
        customer_name="PT Semen Indonesia (Persero) Tbk",
        coal_grade="GAR 5000",
        tonnage_loaded_mt=6450.0,
        origin_jetty="Palaran Jetty, Samarinda",
        destination_port="Pelabuhan Khusus Tuban, Jawa Timur",
        status="LOADING",
        etd=datetime.now(timezone.utc) - timedelta(hours=12),
        eta=datetime.now(timezone.utc) + timedelta(days=5),
        surveyor_company="PT Geoservices",
    ),
]


# ==============================================================================
# Helper CRUD Operations
# ==============================================================================
def get_all_inventory(
    stockpile_id: Optional[int] = None,
    grade: Optional[str] = None,
    min_tonnage: Optional[float] = None,
) -> List[InventoryItem]:
    with _lock:
        res = list(_INVENTORY_DB)
        if stockpile_id is not None:
            res = [i for i in res if i.stockpile_id == stockpile_id]
        if grade is not None:
            res = [i for i in res if grade.lower() in i.grade.lower()]
        if min_tonnage is not None:
            res = [i for i in res if i.tonnage_available_mt >= min_tonnage]
        return res


def get_all_purchase_orders(
    status: Optional[str] = None,
    supplier_code: Optional[str] = None,
) -> List[PurchaseOrderResponse]:
    with _lock:
        res = list(_PURCHASE_ORDERS_DB.values())
        if status:
            res = [po for po in res if po.status.upper() == status.upper()]
        if supplier_code:
            res = [po for po in res if po.supplier_code.upper() == supplier_code.upper()]
        return sorted(res, key=lambda x: x.created_at, reverse=True)


def get_purchase_order_by_number(po_number: str) -> Optional[PurchaseOrderResponse]:
    with _lock:
        return _PURCHASE_ORDERS_DB.get(po_number)


def create_draft_purchase_order(data: PurchaseOrderCreate) -> PurchaseOrderResponse:
    with _lock:
        seq = len(_PURCHASE_ORDERS_DB) + 91
        po_number = f"PO-2026-{seq:04d}"
        
        total_tonnage = sum(item.quantity_mt for item in data.items)
        total_amount = sum(item.quantity_mt * item.unit_price_usd for item in data.items)

        # Update each item's total_amount_usd if not set
        for item in data.items:
            item.total_amount_usd = item.quantity_mt * item.unit_price_usd

        po = PurchaseOrderResponse(
            po_number=po_number,
            supplier_code=data.supplier_code,
            supplier_name=data.supplier_name,
            delivery_jetty=data.delivery_jetty,
            target_delivery_date=data.target_delivery_date,
            items=data.items,
            total_tonnage_mt=total_tonnage,
            total_amount_usd=total_amount,
            status="DRAFT",
            requires_approval=True,
            approval_status="PENDING",
            approved_by=None,
            approved_at=None,
            notes=data.notes,
            created_by=data.created_by,
            created_at=datetime.now(timezone.utc),
        )
        _PURCHASE_ORDERS_DB[po_number] = po
        return po


def approve_purchase_order(
    po_number: str,
    approved_by: str,
    notes: Optional[str] = None,
) -> Optional[PurchaseOrderResponse]:
    with _lock:
        po = _PURCHASE_ORDERS_DB.get(po_number)
        if not po:
            return None
        
        updated_notes = f"{po.notes or ''}; Approved by {approved_by}: {notes or ''}".strip("; ")
        updated_po = po.model_copy(
            update={
                "status": "APPROVED",
                "approval_status": "APPROVED",
                "approved_by": approved_by,
                "approved_at": datetime.now(timezone.utc),
                "notes": updated_notes,
            }
        )
        _PURCHASE_ORDERS_DB[po_number] = updated_po
        return updated_po


def get_all_invoices(
    payment_status: Optional[str] = None,
    customer_code: Optional[str] = None,
    overdue_only: bool = False,
) -> List[InvoiceResponse]:
    with _lock:
        res = list(_INVOICES_DB)
        if payment_status:
            res = [inv for inv in res if inv.payment_status.upper() == payment_status.upper()]
        if customer_code:
            res = [inv for inv in res if inv.customer_code.upper() == customer_code.upper()]
        if overdue_only:
            res = [inv for inv in res if inv.payment_status == "OVERDUE"]
        return sorted(res, key=lambda x: x.issue_date, reverse=True)


def get_invoice_by_number(invoice_number: str) -> Optional[InvoiceResponse]:
    with _lock:
        for inv in _INVOICES_DB:
            if inv.invoice_number.upper() == invoice_number.upper():
                return inv
        return None


def get_all_shipments(
    status: Optional[str] = None,
    customer_name: Optional[str] = None,
) -> List[ShipmentResponse]:
    with _lock:
        res = list(_SHIPMENTS_DB)
        if status:
            res = [s for s in res if s.status.upper() == status.upper()]
        if customer_name:
            res = [s for s in res if customer_name.lower() in s.customer_name.lower()]
        return res
