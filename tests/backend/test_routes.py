from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from PIL import Image
import io, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../backend"))
from app.main import app

client = TestClient(app)

def _img():
    buf = io.BytesIO()
    Image.new("RGB", (320, 240), (200, 200, 200)).save(buf, format="JPEG")
    return buf.getvalue()

MOCK = {"counts": {}, "total": 0, "detections": [], "severity_summary": {}, "quality_status": "PASS",
        "annotated_image": "b64", "image_width": 320, "image_height": 240}

def test_health():
    assert client.get("/health").status_code == 200

def test_analyze():
    with patch("app.api.routes.analyze_defects", new=AsyncMock(return_value=MOCK)):
        r = client.post("/api/v1/analyze", files={"file": ("t.jpg", _img(), "image/jpeg")})
    assert r.status_code == 200
    assert r.json()["quality_status"] == "PASS"

def test_503():
    import httpx
    with patch("app.api.routes.analyze_defects", new=AsyncMock(side_effect=httpx.ConnectError("x"))):
        r = client.post("/api/v1/analyze", files={"file": ("t.jpg", _img(), "image/jpeg")})
    assert r.status_code == 503
