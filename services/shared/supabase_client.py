"""Supabase client factories — anon (respects RLS) and service-role (bypasses)."""

from functools import lru_cache

from supabase import create_client, Client

from .config import settings


@lru_cache(maxsize=1)
def get_supabase() -> Client:
    """Anon-key client — respects Row Level Security."""
    if not settings.supabase_url or not settings.supabase_anon_key:
        raise RuntimeError("SUPABASE_URL and SUPABASE_ANON_KEY must be set")
    return create_client(settings.supabase_url, settings.supabase_anon_key)


@lru_cache(maxsize=1)
def get_supabase_admin() -> Client:
    """Service-role client — bypasses RLS. Use for server-side writes."""
    if not settings.supabase_url or not settings.supabase_service_role_key:
        raise RuntimeError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set")
    return create_client(settings.supabase_url, settings.supabase_service_role_key)
