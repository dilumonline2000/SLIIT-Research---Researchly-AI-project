"""Peer Connect — research group formation.

Three flows:
  POST /peers/groups               – create a new group with open slots
  GET  /peers/groups               – list groups (filterable by status)
  GET  /peers/groups/{group_id}    – fetch one group
  POST /peers/groups/{group_id}/join-request – express interest in joining

The legacy `/peers` SBERT-based peer matcher is kept for backwards compat.
"""

from __future__ import annotations

import logging
import os
import re
import sys
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter()
logger = logging.getLogger(__name__)

_services_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
sys.path.insert(0, _services_root)

# Lightweight email format check — avoids the email-validator dependency
# that pydantic.EmailStr requires.
_EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def _validate_email(value: str, field: str = "email") -> str:
    v = (value or "").strip()
    if not v or not _EMAIL_RE.match(v):
        raise HTTPException(status_code=400, detail=f"{field} is not a valid email address")
    return v


# ─── Schemas ──────────────────────────────────────────────────────────────


class CreateGroupRequest(BaseModel):
    leader_id: Optional[str] = None  # auth.uid from gateway, optional during dev
    leader_name: Optional[str] = None
    project_title: str = Field(..., min_length=1, max_length=200)
    project_description: str = Field(..., min_length=1, max_length=4000)
    research_area: Optional[str] = None
    current_members: list[str] = Field(default_factory=list)
    slots_needed: int = Field(..., ge=1, le=10)
    contact_email: str  # validated in handler


class PeerGroup(BaseModel):
    id: str
    leader_id: Optional[str] = None
    project_title: str
    project_description: str = ""
    research_area: Optional[str] = None
    current_members: list[str] = []
    current_member_count: int = 1
    slots_needed: int = 1
    contact_email: str
    status: str = "open"
    created_at: Optional[str] = None


class GroupListResponse(BaseModel):
    groups: list[PeerGroup]
    total: int


class JoinRequest(BaseModel):
    requester_id: Optional[str] = None
    requester_name: str = Field(..., min_length=1, max_length=200)
    requester_email: str  # validated in handler
    message: Optional[str] = Field(default=None, max_length=1000)


class JoinResponse(BaseModel):
    request_id: str
    group_id: str
    leader_email: str
    mailto_url: str
    email_subject: str
    email_body: str
    note: str = "Email sending is not configured server-side. Open the mailto_url to send via your client."


# ─── Helpers ──────────────────────────────────────────────────────────────


def _supabase():
    try:
        from shared.supabase_client import get_supabase_admin
        return get_supabase_admin()
    except Exception as e:
        logger.error("Supabase admin client unavailable: %s", e)
        return None


def _row_to_group(row: dict) -> PeerGroup:
    return PeerGroup(
        id=str(row.get("id", "")),
        leader_id=str(row.get("leader_id")) if row.get("leader_id") else None,
        project_title=row.get("project_title", ""),
        project_description=row.get("project_description") or "",
        research_area=row.get("research_area"),
        current_members=row.get("current_members") or [],
        current_member_count=int(row.get("current_member_count") or 1),
        slots_needed=int(row.get("slots_needed") or 1),
        contact_email=row.get("contact_email") or "",
        status=row.get("status", "open"),
        created_at=row.get("created_at"),
    )


# ─── Group endpoints ──────────────────────────────────────────────────────


@router.post("/groups", response_model=PeerGroup)
async def create_group(req: CreateGroupRequest) -> PeerGroup:
    """Register a new research group with open slots."""
    sb = _supabase()
    if sb is None:
        raise HTTPException(status_code=503, detail="Database unavailable")

    contact = _validate_email(req.contact_email, "contact_email")
    members = [m.strip() for m in (req.current_members or []) if m.strip()]
    if req.leader_name and req.leader_name not in members:
        members.insert(0, req.leader_name)

    # Drop leader_id if it doesn't have a profiles row (avoids FK violation)
    leader_id: Optional[str] = req.leader_id
    if leader_id:
        try:
            chk = sb.table("profiles").select("id").eq("id", leader_id).limit(1).execute()
            if not (chk.data or []):
                logger.info("leader_id %s has no profiles row; storing as null", leader_id)
                leader_id = None
        except Exception as e:
            logger.warning("Could not verify leader_id, storing as null: %s", e)
            leader_id = None

    payload = {
        "leader_id": leader_id,
        "project_title": req.project_title.strip(),
        "project_description": req.project_description.strip(),
        "research_area": (req.research_area or "").strip() or None,
        "current_members": members,
        "current_member_count": max(1, len(members)),
        "slots_needed": req.slots_needed,
        "contact_email": contact,
        "status": "open",
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    try:
        result = sb.table("peer_groups").insert(payload).execute()
        rows = result.data or []
        if not rows:
            raise RuntimeError("Insert returned no rows")
        return _row_to_group(rows[0])
    except Exception as e:
        logger.error("Failed to create peer group: %s", e)
        raise HTTPException(status_code=500, detail=f"Could not create group: {e}")


@router.get("/groups", response_model=GroupListResponse)
async def list_groups(status: str = "open", limit: int = 50) -> GroupListResponse:
    """List peer groups. Default filter: only open groups."""
    sb = _supabase()
    if sb is None:
        return GroupListResponse(groups=[], total=0)
    try:
        q = sb.table("peer_groups").select("*").order("created_at", desc=True).limit(limit)
        if status and status != "all":
            q = q.eq("status", status)
        result = q.execute()
        rows = result.data or []
        groups = [_row_to_group(r) for r in rows]
        return GroupListResponse(groups=groups, total=len(groups))
    except Exception as e:
        logger.warning("Could not list groups: %s", e)
        return GroupListResponse(groups=[], total=0)


@router.get("/groups/{group_id}", response_model=PeerGroup)
async def get_group(group_id: str) -> PeerGroup:
    sb = _supabase()
    if sb is None:
        raise HTTPException(status_code=503, detail="Database unavailable")
    try:
        result = sb.table("peer_groups").select("*").eq("id", group_id).limit(1).execute()
        rows = result.data or []
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    if not rows:
        raise HTTPException(status_code=404, detail="Group not found")
    return _row_to_group(rows[0])


@router.post("/groups/{group_id}/join-request", response_model=JoinResponse)
async def request_to_join(group_id: str, req: JoinRequest) -> JoinResponse:
    """Record a join request and build a mailto URL for the requester to send.

    The frontend opens `mailto_url` in a new tab so the email goes from the
    requester's actual mailbox — no SMTP server needed on our side.
    """
    sb = _supabase()
    if sb is None:
        raise HTTPException(status_code=503, detail="Database unavailable")

    requester_email = _validate_email(req.requester_email, "requester_email")

    # Fetch group
    try:
        result = sb.table("peer_groups").select("*").eq("id", group_id).limit(1).execute()
        rows = result.data or []
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    if not rows:
        raise HTTPException(status_code=404, detail="Group not found")
    group = rows[0]

    if group.get("status") != "open":
        raise HTTPException(status_code=400, detail="This group is no longer accepting members.")

    # Drop requester_id if it doesn't have a profiles row
    requester_id: Optional[str] = req.requester_id
    if requester_id:
        try:
            chk = sb.table("profiles").select("id").eq("id", requester_id).limit(1).execute()
            if not (chk.data or []):
                requester_id = None
        except Exception:
            requester_id = None

    # Persist the request
    rec_id = ""
    try:
        ins = sb.table("peer_group_join_requests").insert({
            "group_id": group_id,
            "requester_id": requester_id,
            "requester_name": req.requester_name,
            "requester_email": requester_email,
            "message": req.message,
            "status": "pending",
        }).execute()
        if ins.data:
            rec_id = str(ins.data[0].get("id", ""))
    except Exception as e:
        logger.warning("Could not persist join request: %s", e)

    # Build mailto URL for the requester to fire from their own mail client
    leader_email = group.get("contact_email") or ""
    project = group.get("project_title") or "your research group"
    subject = f"Interested in joining your research group: {project}"
    body_lines = [
        f"Hi,",
        "",
        f"My name is {req.requester_name} and I'd like to join your research group "
        f"\"{project}\" on Researchly AI.",
        "",
    ]
    if req.message:
        body_lines += ["A note from me:", req.message, ""]
    body_lines += [
        "Could you let me know the next steps?",
        "",
        "Best regards,",
        req.requester_name,
        f"({requester_email})",
    ]
    body = "\n".join(body_lines)

    from urllib.parse import quote
    mailto = f"mailto:{leader_email}?subject={quote(subject)}&body={quote(body)}"

    return JoinResponse(
        request_id=rec_id,
        group_id=group_id,
        leader_email=leader_email,
        mailto_url=mailto,
        email_subject=subject,
        email_body=body,
    )


# ─── Legacy SBERT peer matcher (kept) ─────────────────────────────────────


class MatchPeersRequest(BaseModel):
    student_id: str
    top_k: int = 10


class PeerMatch(BaseModel):
    peer_id: str
    similarity_score: float
    shared_interests: list[str] = []
    complementary_skills: list[str] = []
    recommendation_type: str


class MatchPeersResponse(BaseModel):
    matches: list[PeerMatch]


@router.post("/peers", response_model=MatchPeersResponse)
async def match_peers(req: MatchPeersRequest) -> MatchPeersResponse:
    """Recommend peer collaborators using content-based SBERT matching."""
    try:
        from shared.embedding_utils import embed
        from shared.supabase_client import get_supabase_admin
    except ImportError:
        return MatchPeersResponse(matches=[])

    sb = get_supabase_admin()
    try:
        profile_result = sb.table("profiles").select("*").eq("id", req.student_id).limit(1).execute()
        rows = profile_result.data or []
        student = rows[0] if rows else None
    except Exception as e:
        logger.warning("Could not fetch student profile: %s", e)
        return MatchPeersResponse(matches=[])
    if not student:
        return MatchPeersResponse(matches=[])

    interests = student.get("research_interests") or []
    department = student.get("department") or ""
    query_text = ". ".join(interests) if interests else department
    if not query_text:
        return MatchPeersResponse(matches=[])

    query_vec = embed(query_text).tolist()
    try:
        result = sb.rpc(
            "match_peers",
            {"query_embedding": query_vec, "match_count": req.top_k * 2, "match_threshold": 0.3},
        ).execute()
        candidates = result.data or []
    except Exception as e:
        logger.warning("Peer matching RPC failed: %s", e)
        candidates = []

    matches: list[PeerMatch] = []
    student_interests = set(i.lower() for i in interests)
    for cand in candidates:
        peer_id = str(cand.get("id", ""))
        if peer_id == req.student_id:
            continue
        sim = float(cand.get("similarity", 0))
        peer_interests = set(i.lower() for i in (cand.get("research_interests") or []))
        shared = list(student_interests & peer_interests)
        complementary = list(peer_interests - student_interests)
        matches.append(PeerMatch(
            peer_id=peer_id, similarity_score=round(sim, 4),
            shared_interests=shared[:5], complementary_skills=complementary[:5],
            recommendation_type="content_based",
        ))
    matches.sort(key=lambda m: m.similarity_score, reverse=True)
    return MatchPeersResponse(matches=matches[: req.top_k])
