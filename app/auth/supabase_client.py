from typing import Optional
from supabase import create_client, Client
from ..config import get_settings

_supabase: Optional[Client] = None


def get_supabase() -> Optional[Client]:
    global _supabase
    if _supabase is not None:
        return _supabase

    settings = get_settings()
    if not settings.supabase_url or not settings.supabase_anon_key:
        return None

    _supabase = create_client(str(settings.supabase_url), settings.supabase_anon_key)
    return _supabase


def get_service_supabase() -> Optional[Client]:
    settings = get_settings()
    if not settings.supabase_url or not settings.supabase_service_role_key:
        return None
    return create_client(str(settings.supabase_url), settings.supabase_service_role_key)
