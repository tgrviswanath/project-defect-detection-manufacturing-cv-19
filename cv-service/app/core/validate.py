"""
Shared upload validation utilities.
- File size limit (default 10MB)
- MIME type / extension check
- Max image resolution guard
"""
from fastapi import HTTPException, UploadFile
from PIL import Image
import io

MAX_FILE_BYTES = 10 * 1024 * 1024   # 10 MB
MAX_DIMENSION  = 4096                # pixels per side
ALLOWED_IMAGE_EXTS = {"jpg", "jpeg", "png", "bmp", "webp"}
ALLOWED_VIDEO_EXTS = {"mp4", "avi", "mov", "webm", "mkv"}


def validate_image(file: UploadFile, content: bytes) -> None:
    """Raise HTTPException if the upload fails any image guard."""
    _check_ext(file.filename, ALLOWED_IMAGE_EXTS)
    _check_size(content)
    _check_resolution(content)


def validate_video(file: UploadFile, content: bytes) -> None:
    """Raise HTTPException if the upload fails any video guard."""
    _check_ext(file.filename, ALLOWED_VIDEO_EXTS)
    _check_size(content, limit=200 * 1024 * 1024)   # 200 MB for video


def _check_ext(filename: str, allowed: set) -> None:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format '.{ext}'. Allowed: {sorted(allowed)}"
        )


def _check_size(content: bytes, limit: int = MAX_FILE_BYTES) -> None:
    if len(content) > limit:
        mb = limit // (1024 * 1024)
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum allowed size is {mb} MB."
        )


def _check_resolution(content: bytes) -> None:
    try:
        img = Image.open(io.BytesIO(content))
        w, h = img.size
        if w > MAX_DIMENSION or h > MAX_DIMENSION:
            raise HTTPException(
                status_code=400,
                detail=f"Image resolution {w}×{h} exceeds maximum {MAX_DIMENSION}×{MAX_DIMENSION}."
            )
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=400, detail="Cannot read image file. Ensure it is a valid image.")
