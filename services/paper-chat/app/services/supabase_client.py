"""Thin Supabase client wrapper. Reuses the same env vars as other services."""

from functools import lru_cache
import os


@lru_cache(maxsize=1)
def get_supabase():
    """Return a service-role Supabase client. Lazy so missing env doesn't crash startup."""
    from supabase import create_client

    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("SUPABASE_ANON_KEY")
    if not url or not key:
        raise RuntimeError(
            "SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY (or anon) must be set"
        )
    return create_client(url, key)
