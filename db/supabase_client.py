"""Cliente Supabase via requests.

Mantem a tecnologia atual. A migracao para supabase-py deve ocorrer em modulo
paralelo e por flag de ambiente.
"""

from __future__ import annotations

import requests


class SupabaseRestClient:
    def __init__(self, url: str, key: str, timeout: int = 20):
        self.url = (url or "").rstrip("/")
        self.key = key or ""
        self.timeout = timeout

    @property
    def configured(self) -> bool:
        return bool(self.url and self.key)

    @property
    def headers(self) -> dict:
        return {
            "apikey": self.key,
            "Authorization": f"Bearer {self.key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation",
        }

    def request(self, method: str, path: str, **kwargs):
        if not self.configured:
            raise RuntimeError("Supabase nao configurado.")
        endpoint = f"{self.url}/rest/v1/{path.lstrip('/')}"
        response = requests.request(method, endpoint, headers=self.headers, timeout=self.timeout, **kwargs)
        response.raise_for_status()
        if response.text:
            return response.json()
        return None
