"""Shared rate limiter (slowapi), keyed by client IP.

default_limits is the GLOBAL limit applied to every request from one IP. The
login and signup routes add their own, stricter limits on top.

Note: behind a reverse proxy (nginx), run uvicorn with --proxy-headers (see
DEPLOYMENT.md) so each visitor is seen by their real IP, not nginx's.
"""
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address, default_limits=["300/minute"])
