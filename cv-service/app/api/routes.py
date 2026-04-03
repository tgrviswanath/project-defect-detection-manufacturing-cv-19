from fastapi import APIRouter, HTTPException, UploadFile, File
from app.core.detector import detect

router = APIRouter(prefix="/api/v1/cv", tags=["defect-detection"])
ALLOWED = {"jpg", "jpeg", "png", "bmp", "webp"}

def _validate(filename: str):
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ALLOWED:
        raise HTTPException(status_code=400, detail=f"Unsupported format: .{ext}")

@router.post("/detect")
async def detect_defects(file: UploadFile = File(...)):
    _validate(file.filename)
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty file")
    return detect(content)
