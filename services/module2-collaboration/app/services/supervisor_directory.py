"""Unified supervisor directory.

Combines two sources:
  1. SLIIT supervisors loaded from `data/sliit_supervisors.json` (74 records)
  2. System users with `role = 'supervisor'` from the `profiles` table

Used by the feedback dropdown, the effectiveness list, and any other UI that
needs "all supervisors a student can rate / contact".

Each entry has a uniform shape:
    {
      "key":         str,    # "sliit:1" or "system:<uuid>"
      "source":      "sliit" | "system",
      "id":          int|str,
      "name":        str,
      "email":       str | None,
      "department":  str | None,
      "research_areas": list[str],
      "availability": bool | None,
      "current_students": int | None,
      "max_students": int | None,
    }
"""

from __future__ import annotations

import json
import logging
from functools import lru_cache
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

SERVICE_ROOT = Path(__file__).resolve().parent.parent.parent
SLIIT_DATA_PATH = SERVICE_ROOT / "data" / "sliit_supervisors.json"


@lru_cache(maxsize=1)
def _load_sliit() -> list[dict[str, Any]]:
    if not SLIIT_DATA_PATH.exists():
        logger.warning("[supervisor_directory] SLIIT data not found at %s", SLIIT_DATA_PATH)
        return []
    try:
        with open(SLIIT_DATA_PATH, encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error("[supervisor_directory] failed to load SLIIT data: %s", e)
        return []


def _from_sliit(rec: dict[str, Any]) -> dict[str, Any]:
    return {
        "key": f"sliit:{rec.get('id')}",
        "source": "sliit",
        "id": rec.get("id"),
        "name": rec.get("name", ""),
        "email": rec.get("email"),
        "department": rec.get("department"),
        "research_cluster": rec.get("research_cluster"),
        "research_areas": rec.get("research_interests") or [],
        "rank": rec.get("rank"),
        "level": rec.get("level"),
        "availability": rec.get("availability"),
        "current_students": rec.get("current_students"),
        "max_students": rec.get("max_students"),
    }


def _from_system(profile: dict[str, Any], sup_row: dict[str, Any] | None) -> dict[str, Any]:
    sup_row = sup_row or {}
    return {
        "key": f"system:{profile.get('id')}",
        "source": "system",
        "id": profile.get("id"),
        "name": profile.get("full_name") or "(unnamed)",
        "email": profile.get("email"),
        "department": profile.get("department"),
        "research_cluster": None,
        "research_areas": sup_row.get("research_areas") or profile.get("research_interests") or [],
        "rank": None,
        "level": None,
        "availability": sup_row.get("availability"),
        "current_students": sup_row.get("current_students"),
        "max_students": sup_row.get("max_students"),
    }


def list_all() -> list[dict[str, Any]]:
    """Return SLIIT + system supervisors as a single sorted list."""
    out: list[dict[str, Any]] = [_from_sliit(r) for r in _load_sliit() if r.get("name")]

    # System supervisors (best-effort — db may be unreachable in dev)
    try:
        from shared.supabase_client import get_supabase_admin
        sb = get_supabase_admin()
        # Pull supervisor profiles (joined with the user profile for name+email)
        profiles_res = sb.table("profiles").select("id,full_name,email,department,research_interests,role").eq("role", "supervisor").execute()
        profiles = profiles_res.data or []
        sup_res = sb.table("supervisor_profiles").select("*").execute()
        sup_by_user = {row.get("user_id"): row for row in (sup_res.data or [])}
        for p in profiles:
            out.append(_from_system(p, sup_by_user.get(p.get("id"))))
    except Exception as e:
        logger.info("[supervisor_directory] no system supervisors available: %s", e)

    out.sort(key=lambda x: (x.get("source") != "sliit", (x.get("name") or "").lower()))
    return out


def get_one(key: str) -> dict[str, Any] | None:
    """Look up a single supervisor by composite key 'sliit:<id>' or 'system:<uuid>'."""
    if not key or ":" not in key:
        return None
    src, ident = key.split(":", 1)
    if src == "sliit":
        try:
            target = int(ident)
        except ValueError:
            return None
        for rec in _load_sliit():
            if rec.get("id") == target:
                return _from_sliit(rec)
        return None
    if src == "system":
        try:
            from shared.supabase_client import get_supabase_admin
            sb = get_supabase_admin()
            p_res = sb.table("profiles").select("id,full_name,email,department,research_interests,role").eq("id", ident).limit(1).execute()
            profiles = p_res.data or []
            if not profiles:
                return None
            sup_res = sb.table("supervisor_profiles").select("*").eq("user_id", ident).limit(1).execute()
            sup_rows = sup_res.data or []
            return _from_system(profiles[0], sup_rows[0] if sup_rows else None)
        except Exception as e:
            logger.warning("[supervisor_directory] system lookup failed: %s", e)
            return None
    return None
