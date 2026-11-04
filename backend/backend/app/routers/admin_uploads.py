"""Admin-only: upload a product/category photo.

Files are saved under the website's img/uploads/ folder and served as static
files, so the returned "/img/uploads/<name>" URL works on the same origin.

SECURITY: the file type is decided from the file's real first bytes ("magic
bytes"), never from the filename or the browser's Content-Type. So a fake PNG,
an HTML page or an SVG (which can carry scripts) is rejected.
"""
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from ..config import UI_DIR
from ..deps import require_admin
from ..models import User
from ..schemas import UploadOut

router = APIRouter(prefix="/admin", tags=["admin"])

UPLOAD_DIR = UI_DIR / "img" / "uploads"
MAX_BYTES = 5 * 1024 * 1024  # 5 MB
_BAD_TYPE = "Please upload a JPG, PNG, WebP, or GIF image."


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


@router.post("/uploads/product-image", response_model=UploadOut)
async def upload_product_image(
    file: UploadFile = File(...),
    admin: User = Depends(require_admin),
) -> dict:
    # Read at most MAX_BYTES + 1 so an oversized file is detected without ever
    # loading more than ~5 MB into memory (the request body itself is also capped
    # at the server edge by BodyLimitMiddleware in main.py).
    data = await file.read(MAX_BYTES + 1)
    if len(data) == 0:
        raise HTTPException(status_code=400, detail="That file is empty.")
    if len(data) > MAX_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="That image is too large. Please use one under 5 MB.",
        )
    ext = sniff_image_extension(data)
    if ext is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=_BAD_TYPE)

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    name = f"{uuid.uuid4().hex}{ext}"  # our own name; the client's filename is ignored
    (UPLOAD_DIR / name).write_bytes(data)

    return {"image_url": f"/img/uploads/{name}"}
