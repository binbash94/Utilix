# app/services/http_client.py
from __future__ import annotations
import os
import socket
import contextlib
import httpx
import certifi

# ---------- Tunables via env ----------
ESRI_CONNECT_TIMEOUT = float(os.getenv("ESRI_CONNECT_TIMEOUT", "10"))
ESRI_READ_TIMEOUT    = float(os.getenv("ESRI_READ_TIMEOUT", "30"))
ESRI_WRITE_TIMEOUT   = float(os.getenv("ESRI_WRITE_TIMEOUT", "10"))
ESRI_POOL_TIMEOUT    = float(os.getenv("ESRI_POOL_TIMEOUT", "60"))
ESRI_RETRIES         = int(os.getenv("ESRI_RETRIES", "3"))
ESRI_FORCE_IPV4_DNS  = os.getenv("ESRI_FORCE_IPV4_DNS", "false").lower() in {"1","true","yes"}
ESRI_TRUST_ENV       = os.getenv("ESRI_TRUST_ENV", "false").lower() in {"1","true","yes"}  # default off (avoid proxy/IPv6 surprises)

# ---------- curl-like headers ----------
DEFAULT_HEADERS = {
    "User-Agent": "curl/8.5.0",   # mirrors your working curl UA
    "Accept": "application/json",
    # You can leave keep-alive (default). If you ever see odd stalls, flip this via env and add 'Connection': 'close'
}

# ---------- Force IPv4 DNS (like curl -4) ----------
@contextlib.contextmanager
def force_ipv4_dns(enabled: bool):
    """Temporarily filter DNS results to AF_INET only."""
    if not enabled:
        yield
        return
    orig = socket.getaddrinfo
    def v4_only(host, port, family=0, type=0, proto=0, flags=0):
        results = orig(host, port, family, type, proto, flags)
        v4 = [r for r in results if r[0] == socket.AF_INET]
        return v4 or results
    try:
        socket.getaddrinfo = v4_only  # type: ignore[assignment]
        yield
    finally:
        socket.getaddrinfo = orig  # type: ignore[assignment]

# ---------- Singleton AsyncClient ----------
_esri_client: httpx.AsyncClient | None = None

def build_esri_client() -> httpx.AsyncClient:
    return httpx.AsyncClient(
        verify=certifi.where(),  # stable CA bundle
        trust_env=ESRI_TRUST_ENV,
        headers=DEFAULT_HEADERS,
        timeout=httpx.Timeout(
            connect=ESRI_CONNECT_TIMEOUT,
            read=ESRI_READ_TIMEOUT,
            write=ESRI_WRITE_TIMEOUT,
            pool=ESRI_POOL_TIMEOUT,
        ),
        transport=httpx.AsyncHTTPTransport(retries=ESRI_RETRIES),
        follow_redirects=True,
    )

async def init_http_clients() -> None:
    global _esri_client
    if _esri_client is None:
        _esri_client = build_esri_client()

async def close_http_clients() -> None:
    global _esri_client
    if _esri_client is not None:
        await _esri_client.aclose()
        _esri_client = None

def esri_client() -> httpx.AsyncClient:
    assert _esri_client is not None, "HTTP client not initialized; call init_http_clients() at startup."
    return _esri_client

def esri_ipv4_guard():
    """Context manager you can 'with' around GETs to mimic curl -4."""
    return force_ipv4_dns(ESRI_FORCE_IPV4_DNS)
