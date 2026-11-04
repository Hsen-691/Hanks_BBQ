"""Shared rate limiter (slowapi), keyed by client IP.

default_limits is the GLOBAL limit applied to every request from one IP. The
login and signup routes add their own, stricter limits on top.

Note: behind a reverse proxy (nginx), run uvicorn with --proxy-headers (see
DEPLOYMENT.md) so each visitor is seen by their real IP, not nginx's.
On Vercel the visitor's IP comes from the X-Real-IP header, which Vercel's edge
sets itself (a visitor cannot fake it). The header is only trusted on Vercel.
"""
import os

from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address

ON_VERCEL = bool(os.environ.get("VERCEL"))


def client_ip(request: Request) -> str:
    if ON_VERCEL:
        ip = request.headers.get("x-real-ip") or request.headers.get("x-forwarded-for", "").split(",")[0]
        if ip.strip():
            return ip.strip()
    return get_remote_address(request)


limiter = Limiter(key_func=client_ip, default_limits=["300/minute"])
