from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from PIL import Image
import io, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../cv-service"))
from app.main import app

client = TestClient(app)

def _img():
    buf = io.BytesIO()
    Image.new("RGB", (640, 480), (200, 200, 200)).save(buf, format="JPEG")
    return buf.getvalue()

def test_health():
    assert client.get("/health").status_code == 200

def test_detect_pass():
    mock_result = MagicMock()
    mock_result.boxes = []
    mock_model = MagicMock()
    mock_model.names = {}
    mock_model.return_value = [mock_result]
    with patch("app.core.detector._get_model", return_value=mock_model):
        r = client.post("/api/v1/cv/detect", files={"file": ("t.jpg", _img(), "image/jpeg")})
    assert r.status_code == 200
    assert r.json()["quality_status"] == "PASS"

def test_unsupported_format():
    r = client.post("/api/v1/cv/detect", files={"file": ("t.gif", b"GIF89a", "image/gif")})
    assert r.status_code == 400

def test_empty_file():
    r = client.post("/api/v1/cv/detect", files={"file": ("t.jpg", b"", "image/jpeg")})
    assert r.status_code == 400
