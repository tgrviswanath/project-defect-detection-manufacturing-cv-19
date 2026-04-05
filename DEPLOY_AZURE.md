# Azure Deployment Guide — Project CV-19 Defect Detection Manufacturing

---

## Azure Services for Manufacturing Defect Detection

### 1. Ready-to-Use AI (No Model Needed)

| Service                              | What it does                                                                 | When to use                                        |
|--------------------------------------|------------------------------------------------------------------------------|----------------------------------------------------|
| **Azure Custom Vision**              | Train custom defect detector on your labelled product images                 | Replace your YOLOv8 defect detection pipeline      |
| **Azure AI Vision**                  | Detect anomalies and objects in product images                               | When you need general defect detection             |
| **Azure OpenAI Vision**              | GPT-4V for defect analysis and quality assessment via prompt                 | When you need flexible defect understanding        |

> **Azure Custom Vision** trained on your defect images is the direct replacement for your YOLOv8 pipeline. Upload labelled defect images → train → deploy endpoint — no code needed.

### 2. Host Your Own Model (Keep Current Stack)

| Service                        | What it does                                                        | When to use                                           |
|--------------------------------|---------------------------------------------------------------------|-------------------------------------------------------|
| **Azure Container Apps**       | Run your 3 Docker containers (frontend, backend, cv-service)        | Best match for your current microservice architecture |
| **Azure Container Registry**   | Store your Docker images                                            | Used with Container Apps or AKS                       |

### 3. Supporting Services

| Service                       | Purpose                                                                  |
|-------------------------------|--------------------------------------------------------------------------|
| **Azure Blob Storage**        | Store product images and defect detection results                        |
| **Azure Cosmos DB**           | Store defect logs, quality metrics, and production records               |
| **Azure Key Vault**           | Store API keys and connection strings instead of .env files              |
| **Azure Monitor + App Insights** | Track detection latency, defect rates, pass/fail ratios              |

---

## Recommended Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Azure Static Web Apps — React Frontend                     │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTPS
┌──────────────────────▼──────────────────────────────────────┐
│  Azure Container Apps — Backend (FastAPI :8000)             │
└──────────────────────┬──────────────────────────────────────┘
                       │ Internal
        ┌──────────────┴──────────────┐
        │ Option A                    │ Option B
        ▼                             ▼
┌───────────────────┐    ┌────────────────────────────────────┐
│ Container Apps    │    │ Azure Custom Vision                │
│ CV Service :8001  │    │ Manufacturing defect detection     │
│ YOLOv8+OpenCV     │    │ No model training needed           │
└───────────────────┘    └────────────────────────────────────┘
```

---

## Prerequisites

```bash
az login
az group create --name rg-defect-detection --location uksouth
az extension add --name containerapp --upgrade
```

---

## Step 1 — Create Container Registry and Push Images

```bash
az acr create --resource-group rg-defect-detection --name defectdetectacr --sku Basic --admin-enabled true
az acr login --name defectdetectacr
ACR=defectdetectacr.azurecr.io
docker build -f docker/Dockerfile.cv-service -t $ACR/cv-service:latest ./cv-service
docker push $ACR/cv-service:latest
docker build -f docker/Dockerfile.backend -t $ACR/backend:latest ./backend
docker push $ACR/backend:latest
```

---

## Step 2 — Deploy Container Apps

```bash
az containerapp env create --name defectdetect-env --resource-group rg-defect-detection --location uksouth

az containerapp create \
  --name cv-service --resource-group rg-defect-detection \
  --environment defectdetect-env --image $ACR/cv-service:latest \
  --registry-server $ACR --target-port 8001 --ingress internal \
  --min-replicas 1 --max-replicas 3 --cpu 1 --memory 2.0Gi

az containerapp create \
  --name backend --resource-group rg-defect-detection \
  --environment defectdetect-env --image $ACR/backend:latest \
  --registry-server $ACR --target-port 8000 --ingress external \
  --min-replicas 1 --max-replicas 5 --cpu 0.5 --memory 1.0Gi \
  --env-vars CV_SERVICE_URL=http://cv-service:8001
```

---

## Option B — Use Azure Custom Vision Object Detection

```python
from azure.cognitiveservices.vision.customvision.prediction import CustomVisionPredictionClient
from msrest.authentication import ApiKeyCredentials

credentials = ApiKeyCredentials(in_headers={"Prediction-key": os.getenv("CUSTOM_VISION_KEY")})
predictor = CustomVisionPredictionClient(os.getenv("CUSTOM_VISION_ENDPOINT"), credentials)

def detect_defects(image_bytes: bytes) -> dict:
    result = predictor.detect_image(
        project_id=os.getenv("CUSTOM_VISION_PROJECT_ID"),
        published_name="production",
        image_data=image_bytes
    )
    defects = [{"type": p.tag_name, "confidence": round(p.probability * 100, 2),
                "bounding_box": {"left": p.bounding_box.left, "top": p.bounding_box.top,
                                 "width": p.bounding_box.width, "height": p.bounding_box.height}}
               for p in result.predictions if p.probability > 0.4]
    is_defective = len(defects) > 0
    return {
        "status": "fail" if is_defective else "pass",
        "is_defective": is_defective,
        "defects": defects,
        "quality_verdict": "FAIL" if is_defective else "PASS"
    }
```

---

## Estimated Monthly Cost

| Service                  | Tier      | Est. Cost         |
|--------------------------|-----------|-------------------|
| Container Apps (backend) | 0.5 vCPU  | ~$10–15/month     |
| Container Apps (cv-svc)  | 1 vCPU    | ~$15–20/month     |
| Container Registry       | Basic     | ~$5/month         |
| Static Web Apps          | Free      | $0                |
| Azure Custom Vision      | S0 tier   | Pay per prediction|
| **Total (Option A)**     |           | **~$30–40/month** |
| **Total (Option B)**     |           | **~$15–25/month** |

For exact estimates → https://calculator.azure.com

---

## Teardown

```bash
az group delete --name rg-defect-detection --yes --no-wait
```
