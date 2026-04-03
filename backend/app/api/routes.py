from fastapi import APIRouter, HTTPException, UploadFile, File
from app.core.service import analyze_defects
import httpx

router = APIRouter(prefix="/api/v1", tags=["defect-detection"])

def _handle(e):
    if isinstance(e, httpx.ConnectError):
        raise HTTPException(status_code=503, detail="CV service unavailable")
    if isinstance(e, httpx.HTTPStatusError):
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text)
    raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze")
async def analyze(file: UploadFile = File(...)):
    try:
        content = await file.read()
        return await analyze_defects(file.filename, content, file.content_type or "image/jpeg")
    except Exception as e:
        _handle(e)
