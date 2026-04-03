import httpx
from app.core.config import settings

CV_URL = settings.CV_SERVICE_URL

async def analyze_defects(filename: str, content: bytes, content_type: str) -> dict:
    async with httpx.AsyncClient() as client:
        r = await client.post(f"{CV_URL}/api/v1/cv/detect",
                              files={"file": (filename, content, content_type)}, timeout=60.0)
        r.raise_for_status()
        return r.json()
