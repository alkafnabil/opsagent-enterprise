from __future__ import annotations
import uuid
from datetime import datetime, date, timedelta, timezone
from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field
import httpx

from app.tools.base import BaseTool
from app.core.config import settings


class M365ActionInput(BaseModel):
    action: Literal[
        "check_availability",
        "create_calendar_event",
        "draft_email",
    ] = Field(..., description="Aksi Microsoft 365 yang dipanggil")

    # Calendar Availability check
    user_email: Optional[str] = Field(None, description="Email user / PIC untuk dicek ketersediaan jadwalnya")
    target_date: Optional[str] = Field(None, description="Tanggal pengecekan jadwal (YYYY-MM-DD)")

    # Create Calendar Event
    event_subject: Optional[str] = Field(None, description="Judul rapat / agenda koordinasi")
    start_time: Optional[str] = Field(None, description="Waktu mulai format ISO8601 (YYYY-MM-DDTHH:MM:SS)")
    end_time: Optional[str] = Field(None, description="Waktu selesai format ISO8601 (YYYY-MM-DDTHH:MM:SS)")
    location: Optional[str] = Field("Jetty Control Room / Microsoft Teams", description="Lokasi rapat / link online")
    attendees: Optional[List[str]] = Field(default_factory=list, description="Daftar alamat email peserta")

    # Draft Email
    to_recipients: Optional[List[str]] = Field(default_factory=list, description="Daftar penerima email")
    subject: Optional[str] = Field(None, description="Subjek email")
    body_text: Optional[str] = Field(None, description="Konten isi pesan email")
    importance: Optional[Literal["low", "normal", "high"]] = Field("normal", description="Tingkat kepentingan email")


# Mock M365 In-Memory Store
_MOCK_EVENTS: List[Dict[str, Any]] = [
    {
        "event_id": "EVT-2026-001",
        "subject": "Rapat Koordinasi Laycan Tongkang BG Trans Coal 301",
        "start": f"{date.today()}T09:00:00",
        "end": f"{date.today()}T10:00:00",
        "location": "Jetty Palaran Room A",
        "attendees": ["loading.master@nusantaracoal.com", "surveyor@carsurin.com"],
    },
    {
        "event_id": "EVT-2026-002",
        "subject": "Joint Inspection Draught Survey Palaran",
        "start": f"{date.today()}T14:00:00",
        "end": f"{date.today()}T15:30:00",
        "location": "Dermaga Jetty Palaran",
        "attendees": ["chief.officer@transcoal.com"],
    },
]

_MOCK_DRAFT_EMAILS: List[Dict[str, Any]] = []


class M365Tool(BaseTool):
    name: str = "m365"
    description: str = (
        "Integrasi Microsoft 365 (Outlook & Calendar). "
        "Dapat memeriksa jadwal kosong staf operasional, menjadwalkan rapat koordinasi jetty, "
        "dan membuat draf email konfirmasi pengapalan atau penagihan invoice."
    )
    args_schema: type[BaseModel] = M365ActionInput
    timeout_seconds: float = 6.0
    max_retries: int = 1

    async def _run(self, args: M365ActionInput) -> Dict[str, Any]:
        if settings.M365_USE_MOCK or not settings.M365_CLIENT_ID or settings.M365_CLIENT_ID.startswith("mock"):
            return self._run_mock_m365(args)
        else:
            return await self._run_graph_api(args)

    def _run_mock_m365(self, args: M365ActionInput) -> Dict[str, Any]:
        check_date = args.target_date or str(date.today())

        if args.action == "check_availability":
            # Return slots not clashing with existing mock events
            free_slots = [
                {"start": f"{check_date}T10:30:00", "end": f"{check_date}T12:00:00", "status": "AVAILABLE"},
                {"start": f"{check_date}T13:00:00", "end": f"{check_date}T14:00:00", "status": "AVAILABLE"},
                {"start": f"{check_date}T16:00:00", "end": f"{check_date}T17:30:00", "status": "AVAILABLE"},
            ]
            busy_events = [e for e in _MOCK_EVENTS if check_date in e["start"]]
            return {
                "target_date": check_date,
                "user_email": args.user_email or "operasional@nusantaracoal.com",
                "available_slots": free_slots,
                "booked_events": busy_events,
                "summary": f"Tersedia 3 slot jadwal kosong pada {check_date}.",
            }

        elif args.action == "create_calendar_event":
            evt_id = f"EVT-{uuid.uuid4().hex[:8].upper()}"
            start_iso = args.start_time or f"{check_date}T10:30:00"
            end_iso = args.end_time or f"{check_date}T11:30:00"
            new_event = {
                "event_id": evt_id,
                "subject": args.event_subject or "Koordinasi Operasional Batubara",
                "start": start_iso,
                "end": end_iso,
                "location": args.location or "Jetty Control Room",
                "attendees": args.attendees or ["loading.master@nusantaracoal.com"],
                "created_at": datetime.now(timezone.utc).isoformat(),
                "status": "CONFIRMED",
            }
            _MOCK_EVENTS.append(new_event)
            return {
                "status": "SUCCESS",
                "message": f"Jadwal acara '{new_event['subject']}' berhasil dibuat di Kalender M365.",
                "event": new_event,
            }

        elif args.action == "draft_email":
            email_id = f"DRAFT-{uuid.uuid4().hex[:8].upper()}"
            draft = {
                "draft_id": email_id,
                "to_recipients": args.to_recipients or ["buyer@plnepi.co.id"],
                "subject": args.subject or "Pemberitahuan Status Muatan Tongkang Batubara",
                "body_preview": args.body_text[:200] if args.body_text else "Draft email operasional.",
                "importance": args.importance or "normal",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "status": "DRAFT_SAVED",
            }
            _MOCK_DRAFT_EMAILS.append(draft)
            return {
                "status": "SUCCESS",
                "message": f"Draf email '{draft['subject']}' berhasil disimpan di folder Drafts Outlook.",
                "draft": draft,
            }

        return {"error": f"Aksi M365 '{args.action}' tidak dikenali."}

    async def _run_graph_api(self, args: M365ActionInput) -> Dict[str, Any]:
        """Real Microsoft Graph API implementation via OAuth2 Client Credentials."""
        # Authenticate via Azure AD token endpoint
        token_url = f"https://login.microsoftonline.com/{settings.M365_TENANT_ID}/oauth2/v2.0/token"
        token_data = {
            "client_id": settings.M365_CLIENT_ID,
            "client_secret": settings.M365_CLIENT_SECRET,
            "scope": "https://graph.microsoft.com/.default",
            "grant_type": "client_credentials",
        }
        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            token_resp = await client.post(token_url, data=token_data)
            token_resp.raise_for_status()
            token = token_resp.json().get("access_token")

            headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
            
            if args.action == "check_availability":
                # Call findMeetingTimes or getSchedule
                sched_resp = await client.post(
                    "https://graph.microsoft.com/v1.0/me/calendar/getSchedule",
                    headers=headers,
                    json={
                        "schedules": [args.user_email or "me"],
                        "startTime": {"dateTime": f"{args.target_date or date.today()}T08:00:00", "timeZone": "Asia/Jakarta"},
                        "endTime": {"dateTime": f"{args.target_date or date.today()}T18:00:00", "timeZone": "Asia/Jakarta"},
                    },
                )
                sched_resp.raise_for_status()
                return sched_resp.json()

            elif args.action == "create_calendar_event":
                event_payload = {
                    "subject": args.event_subject,
                    "start": {"dateTime": args.start_time, "timeZone": "Asia/Jakarta"},
                    "end": {"dateTime": args.end_time, "timeZone": "Asia/Jakarta"},
                    "location": {"displayName": args.location},
                    "attendees": [{"emailAddress": {"address": att}} for att in (args.attendees or [])],
                }
                ev_resp = await client.post("https://graph.microsoft.com/v1.0/me/events", headers=headers, json=event_payload)
                ev_resp.raise_for_status()
                return ev_resp.json()

            elif args.action == "draft_email":
                mail_payload = {
                    "subject": args.subject,
                    "importance": args.importance,
                    "body": {"contentType": "Text", "content": args.body_text},
                    "toRecipients": [{"emailAddress": {"address": r}} for r in (args.to_recipients or [])],
                }
                draft_resp = await client.post("https://graph.microsoft.com/v1.0/me/messages", headers=headers, json=mail_payload)
                draft_resp.raise_for_status()
                return draft_resp.json()

        return {"error": "Aksi tidak didukung."}

    def _summarize_output(self, output: Any) -> str:
        if isinstance(output, dict) and "message" in output:
            return output["message"]
        elif isinstance(output, dict) and "summary" in output:
            return output["summary"]
        return super()._summarize_output(output)
