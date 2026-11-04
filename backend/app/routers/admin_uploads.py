"""Admin-only: upload a product/category photo.

Locally, files are saved under the website's img/uploads/ folder and served as
static files, so the returned "/img/uploads/<name>" URL works on the same origin.
On Vercel (where the disk is read-only) BLOB_READ_WRITE_TOKEN is set, and the
photo is stored in Vercel Blob instead; the returned URL is its https:// link.

SECURITY: the file type is decided from the file's real first bytes ("magic
bytes"), never from the filename or the browser's Content-Type. So a fake PNG,
an HTML page or an SVG (which can carry scripts) is rejected.
"""
import json
import os
import urllib.error
import urllib.parse
import urllib.request
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.concurrency import run_in_threadpool

from ..config import UI_DIR
from ..deps import require_admin
from ..models import User
from ..schemas import UploadOut

router = APIRouter(prefix="/admin", tags=["admin"])

UPLOAD_DIR = UI_DIR / "img" / "uploads"
MAX_BYTES = 4 * 1024 * 1024  # 4 MB (Vercel rejects requests over 4.5 MB)
_BAD_TYPE = "Please upload a JPG, PNG, WebP, or GIF image."
_CONTENT_TYPES = {".jpg": "image/jpeg", ".png": "image/png", ".gif": "image/gif", ".webp": "image/webp"}
_BLOB_API = "https://vercel.com/api/blob/"


def sniff_image_extension(data: bytes) -> str | None:
    """Return the file extension for a real JPG/PNG/GIF/WebP, else None."""
    if data.startswith(b"\xff\xd8\xff"):
        return ".jpg"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return ".png"
    if data.startswith((b"GIF87a", b"GIF89a")):
        return ".gif"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return ".webp"
    return None


def _put_blob(token: str, name: str, data: bytes, ext: str) -> str:
    """Store the photo in Vercel Blob and return its public https:// URL."""
    req = urllib.request.Request(
        _BLOB_API + "?" + urllib.parse.urlencode({"pathname": f"uploads/{name}"}),
        data=data,
        method="PUT",
        headers={
            "authorization": f"Bearer {token}",
            "x-api-version": "13",
            # The token looks like vercel_blob_rw_<storeId>_<secret>
            "x-vercel-blob-store-id": (token.split("_") + [""] * 4)[3],
            "x-vercel-blob-access": "public",
            "x-content-type": _CONTENT_TYPES[ext],
            "x-add-random-suffix": "0",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)["url"]


@router.post("/uploads/product-image", response_model=UploadOut)
async def upload_product_image(
    file: UploadFile = File(...),
    admin: User = Depends(require_admin),
) -> dict:
    # Read at most MAX_BYTES + 1 so an oversized file is detected without ever
    # loading more than ~4 MB into memory (the request body itself is also capped
    # at the server edge by BodyLimitMiddleware in main.py).
    data = await file.read(MAX_BYTES + 1)
    if len(data) == 0:
        raise HTTPException(status_code=400, detail="That file is empty.")
    if len(data) > MAX_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="That image is too large. Please use one under 4 MB.",
        )
    ext = sniff_image_extension(data)
    if ext is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=_BAD_TYPE)

    name = f"{uuid.uuid4().hex}{ext}"  # our own name; the client's filename is ignored

    token = os.environ.get("BLOB_READ_WRITE_TOKEN")
    if token:
        try:
            return {"image_url": await run_in_threadpool(_put_blob, token, name, data, ext)}
        except (urllib.error.URLError, KeyError, ValueError) as exc:
            print(f"Vercel Blob upload failed: {exc!r}")
            raise HTTPException(status_code=502, detail="Could not save the photo. Please try again.")

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    (UPLOAD_DIR / name).write_bytes(data)

    return {"image_url": f"/img/uploads/{name}"}
