"""Shared Python utilities across all ML microservices."""

from .config import settings
from .supabase_client import get_supabase, get_supabase_admin

__all__ = ["settings", "get_supabase", "get_supabase_admin"]
