from __future__ import annotations
import logging
from typing import Optional, List, Dict, Any, Literal
from datetime import date, timedelta
from pydantic import BaseModel, Field
import httpx

from app.tools.base import BaseTool
from app.core.config import settings

logger = logging.getLogger(__name__)


class ERPActionInput(BaseModel):
    action: Literal[
        "get_inventory",
        "get_purchase_order",
        "get_invoices",
        "get_shipments",
        "create_po_draft",
    ] = Field(..., description="Aksi ERP yang akan dipanggil")
    
    # Query parameters
    po_number: Optional[str] = Field(None, description="Nomor PO (e.g. 'PO-2026-0089')")
    stockpile_id: Optional[int] = Field(None, description="ID stockpile")
    grade: Optional[str] = Field(None, description="Kalori batubara (e.g. 'GAR 4200')")
    customer_code: Optional[str] = Field(None, description="Kode customer (e.g. 'CUST-PLN-01')")
    overdue_only: Optional[bool] = Field(False, description="Filter hanya invoice overdue")
    status: Optional[str] = Field(None, description="Filter status operasional")

    # Write action parameters (create_po_draft)
    supplier_code: Optional[str] = Field(None, description="Kode supplier tambang (e.g. 'SUP-KPC-01')")
    supplier_name: Optional[str] = Field(None, description="Nama supplier tambang")
    delivery_jetty: Optional[str] = Field(None, description="Jetty tujuan bongkar muat")
    quantity_mt: Optional[float] = Field(None, description="Kuantitas batubara dalam MT")
    unit_price_usd: Optional[float] = Field(None, description="Harga per MT dalam USD")
    target_delivery_date: Optional[str] = Field(None, description="Target tanggal pengiriman (YYYY-MM-DD)")
    notes: Optional[str] = Field(None, description="Catatan operasional PO")
    user_role: Optional[str] = Field("staff", description="Peran user pemanggil ('staff' atau 'manager')")


class ERPTool(BaseTool):
    name: str = "erp_api"
    description: str = (
        "Integrasi REST API ke sistem ERP pengadaan batubara. "
        "Mendukung GET status PO, stok inventory, invoice/piutang, posisi tongkang, "
        "dan POST buat draft Purchase Order (memerlukan persetujuan approval)."
    )
    args_schema: type[BaseModel] = ERPActionInput
    timeout_seconds: float = 6.0
    max_retries: int = 2

    async def _run(self, args: ERPActionInput) -> Any:
        base_url = settings.ERP_BASE_URL.rstrip("/")
        headers = {"X-API-Key": settings.ERP_API_KEY}

        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            try:
                if args.action == "get_inventory":
                    params = {}
                    if args.stockpile_id is not None:
                        params["stockpile_id"] = args.stockpile_id
                    if args.grade:
                        params["grade"] = args.grade
                    res = await client.get(f"{base_url}/inventory", params=params, headers=headers)
                    res.raise_for_status()
                    return res.json()

                elif args.action == "get_purchase_order":
                    if args.po_number:
                        res = await client.get(f"{base_url}/purchase-orders/{args.po_number}", headers=headers)
                        res.raise_for_status()
                        return res.json()
                    else:
                        params = {}
                        if args.status:
                            params["status"] = args.status
                        res = await client.get(f"{base_url}/purchase-orders", params=params, headers=headers)
                        res.raise_for_status()
                        return res.json()

                elif args.action == "get_invoices":
                    params = {"overdue_only": str(args.overdue_only).lower()}
                    if args.customer_code:
                        params["customer_code"] = args.customer_code
                    if args.status:
                        params["payment_status"] = args.status
                    res = await client.get(f"{base_url}/invoices", params=params, headers=headers)
                    res.raise_for_status()
                    return res.json()

                elif args.action == "get_shipments":
                    params = {}
                    if args.status:
                        params["status"] = args.status
                    res = await client.get(f"{base_url}/shipments", params=params, headers=headers)
                    res.raise_for_status()
                    return res.json()

                elif args.action == "create_po_draft":
                    # Write action: Creates DRAFT PO and flags for Manager Approval
                    payload = {
                        "supplier_code": args.supplier_code or "SUP-KPC-01",
                        "supplier_name": args.supplier_name or "PT Kaltim Prima Mining Concession",
                        "delivery_jetty": args.delivery_jetty or "Palaran Jetty, Samarinda",
                        "target_delivery_date": args.target_delivery_date or str(date.today() + timedelta(days=7)),
                        "items": [
                            {
                                "item_id": "ITM-01",
                                "grade": args.grade or "GAR 4200",
                                "quantity_mt": args.quantity_mt or 5000.0,
                                "unit_price_usd": args.unit_price_usd or 58.0,
                                "total_amount_usd": (args.quantity_mt or 5000.0) * (args.unit_price_usd or 58.0),
                            }
                        ],
                        "notes": args.notes or "Draft PO dibuat otomatis oleh OpsAgent",
                        "created_by": args.user_role or "staff",
                    }
                    res = await client.post(f"{base_url}/purchase-orders", json=payload, headers=headers)
                    res.raise_for_status()
                    po_data = res.json()
                    po_data["requires_approval"] = True
                    return po_data

            except (httpx.ConnectError, httpx.ConnectTimeout) as conn_err:
                logger.warning(f"Mock ERP HTTP offline ({conn_err}). Menggunakan in-process ERP fallback.")
                return self._run_in_process_fallback(args)

    def _run_in_process_fallback(self, args: ERPActionInput) -> Any:
        """Direct in-memory ERP fallback when external mock server is not running on port 8001."""
        from mock_erp.database import (
            get_all_inventory,
            get_all_purchase_orders,
            get_purchase_order_by_number,
            create_draft_purchase_order,
            get_all_invoices,
            get_all_shipments,
        )
        from mock_erp.models import PurchaseOrderCreate, PurchaseOrderItem

        if args.action == "get_inventory":
            items = get_all_inventory(stockpile_id=args.stockpile_id, grade=args.grade)
            return [i.model_dump() for i in items]

        elif args.action == "get_purchase_order":
            if args.po_number:
                po = get_purchase_order_by_number(args.po_number)
                return po.model_dump() if po else {"detail": "PO tidak ditemukan"}
            else:
                pos = get_all_purchase_orders(status=args.status)
                return [p.model_dump() for p in pos]

        elif args.action == "get_invoices":
            invs = get_all_invoices(customer_code=args.customer_code, overdue_only=args.overdue_only or False)
            return [inv.model_dump() for inv in invs]

        elif args.action == "get_shipments":
            ships = get_all_shipments(status=args.status)
            return [s.model_dump() for s in ships]

        elif args.action == "create_po_draft":
            target_date = date.today() + timedelta(days=7)
            qty = args.quantity_mt or 5000.0
            price = args.unit_price_usd or 58.0
            po_req = PurchaseOrderCreate(
                supplier_code=args.supplier_code or "SUP-KPC-01",
                supplier_name=args.supplier_name or "PT Kaltim Prima Mining Concession",
                delivery_jetty=args.delivery_jetty or "Palaran Jetty, Samarinda",
                target_delivery_date=target_date,
                items=[
                    PurchaseOrderItem(
                        item_id="ITM-AUTO",
                        grade=args.grade or "GAR 4200",
                        quantity_mt=qty,
                        unit_price_usd=price,
                        total_amount_usd=qty * price,
                    )
                ],
                notes=args.notes or "Draft PO dibuat otomatis oleh OpsAgent",
                created_by=args.user_role or "staff",
            )
            created = create_draft_purchase_order(po_req)
            data = created.model_dump()
            data["requires_approval"] = True
            return data

    def _summarize_output(self, output: Any) -> str:
        if isinstance(output, dict) and "po_number" in output:
            status = output.get("status", "DRAFT")
            return f"PO {output['po_number']} berhasil diproses dengan status {status}."
        elif isinstance(output, list):
            return f"ERP API berhasil mengembalikan {len(output)} data entitas."
        return super()._summarize_output(output)
