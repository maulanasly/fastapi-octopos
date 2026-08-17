"""Product image processing.

Uploads are validated by magic bytes (Pillow), stripped of EXIF, downscaled
to a sane maximum dimension and re-encoded as WebP. A small thumbnail is
generated alongside the original so mobile clients can render catalog grids
without downloading full-resolution files.
"""
import io
from pathlib import Path
from typing import Optional

from fastapi import HTTPException
from PIL import Image, UnidentifiedImageError

from app.core.config import settings

_MAX_IMAGE_BYTES = 5 * 1024 * 1024
_ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
_ORIGINAL_MAX_DIMENSION = 1600
_THUMBNAIL_MAX_DIMENSION = 480
_WEBP_QUALITY = 80


def media_dir() -> Path:
    path = Path(settings.MEDIA_DIR).resolve()
    path.mkdir(parents=True, exist_ok=True)
    return path


def product_media_dir(tenant_id: int) -> Path:
    path = media_dir() / str(tenant_id) / "products"
    path.mkdir(parents=True, exist_ok=True)
    return path


def delete_media_file(relative_url: Optional[str]) -> None:
    """Delete a stored media file, guarding against path traversal."""
    if not relative_url or not relative_url.startswith("/media/"):
        return
    try:
        file_path = (media_dir() / relative_url.removeprefix("/media/")).resolve()
        if file_path.is_file() and file_path.is_relative_to(media_dir()):
            file_path.unlink()
    except OSError:
        pass


def _encode_webp(image: Image.Image) -> bytes:
    buffer = io.BytesIO()
    image.save(buffer, format="WEBP", quality=_WEBP_QUALITY, method=4)
    return buffer.getvalue()


def process_product_image(content: bytes) -> tuple[bytes, bytes]:
    """Validate an uploaded product photo.

    Returns (original_bytes, thumbnail_bytes) both WebP-encoded and
    downscaled for mobile bandwidth. Raises 413 on oversized uploads and
    415 when the bytes are not a decodable image (magic-byte verification).
    """
    if len(content) > _MAX_IMAGE_BYTES:
        raise HTTPException(status_code=413, detail="Image exceeds 5 MB limit")

    try:
        with Image.open(io.BytesIO(content)) as img:
            img.load()
    except (UnidentifiedImageError, OSError, ValueError):
        raise HTTPException(
            status_code=415, detail="Uploaded file is not a valid image"
        )

    # Flatten palette/greyscale/CMYK and keep alpha; drops EXIF along the way.
    if img.mode not in ("RGB", "RGBA"):
        img = img.convert("RGBA" if "A" in img.mode else "RGB")

    original = img.copy()
    if max(original.size) > _ORIGINAL_MAX_DIMENSION:
        original.thumbnail((_ORIGINAL_MAX_DIMENSION, _ORIGINAL_MAX_DIMENSION))
    thumbnail = original.copy()
    thumbnail.thumbnail((_THUMBNAIL_MAX_DIMENSION, _THUMBNAIL_MAX_DIMENSION))

    return _encode_webp(original), _encode_webp(thumbnail)
