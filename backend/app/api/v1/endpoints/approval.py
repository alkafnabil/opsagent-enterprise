from __future__ import annotations
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, status
from app.guardrails.models import (
    ApprovalAction,
    ApprovalDecisionRequest,
    ApprovalDecisionResponse,
)
from app.guardrails.approval_manager import get_approval_manager

router = APIRouter(prefix="/v1/approvals", tags=["Human-in-the-Loop Approvals"])


@router.get("", response_model=List[ApprovalAction])
async def list_approvals(pending_only: bool = Query(True, description="Filter hanya yang berstatus PENDING")):
    """List pending approval requests requiring Manager authorization."""
    mgr = get_approval_manager()
    if pending_only:
        return mgr.list_pending_approvals()
    return mgr.list_all_approvals()


@router.get("/{approval_id}", response_model=ApprovalAction)
async def get_approval_detail(approval_id: str):
    """Get details of a specific approval request."""
    mgr = get_approval_manager()
    item = mgr.get_approval(approval_id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Permintaan persetujuan '{approval_id}' tidak ditemukan.",
        )
    return item


@router.post("/{approval_id}/decision", response_model=ApprovalDecisionResponse)
async def submit_approval_decision(approval_id: str, req: ApprovalDecisionRequest):
    """
    Submit decision ('APPROVE' or 'REJECT') for a pending write action.
    Strictly restricted to users with role 'manager'.
    """
    mgr = get_approval_manager()
    try:
        response = await mgr.resolve_approval(
            approval_id=approval_id,
            decision=req.decision,
            decided_by=req.decided_by,
            user_role=req.user_role,
            manager_notes=req.manager_notes,
        )
        return response
    except PermissionError as perm_err:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(perm_err),
        )
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(val_err),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Gagal memproses persetujuan: {str(exc)}",
        )
