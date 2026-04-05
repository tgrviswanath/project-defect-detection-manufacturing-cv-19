# GCP Deployment Guide — Project CV-19 Defect Detection Manufacturing

---

## GCP Services for Manufacturing Defect Detection

### 1. Ready-to-Use AI (No Model Needed)

| Service                              | What it does                                                                 | When to use                                        |
|--------------------------------------|------------------------------------------------------------------------------|----------------------------------------------------|
| **Vertex AI AutoML Vision**          | Train custom defect detector on your labelled product images                 | Replace your YOLOv8 defect detection pipeline      |
| **Cloud Vision API**                 | Detect objects and anomalies in product images                               | When you need general defect detection             |
| **Vertex AI Gemini Vision**          | Gemini Pro Vision for defect analysis and quality assessment via prompt      | When you need flexible defect understanding        |

> **Vertex AI AutoML Vision** trained on your defect images is the direct replacement for your YOLOv8 pipeline. Upload labelled defect images → train → deploy endpoint — no code needed.

### 2. Host Your Own Model (Keep Current Stack)

| Service                    | What it does                                                        | When to use                                           |
|----------------------------|---------------------------------------------------------------------|-------------------------------------------------------|
| **Cloud Run**              | Run backend + cv-service containers — serverless, scales to zero    | Best match for your current microservice architecture |
| **Artifact Registry**      | Store your Docker images                                            | Used with Cloud Run or GKE                            |

### 3. Supporting Services

| Service                        | Purpose                                                                   |
|--------------------------------|---------------------------------------------------------------------------|
| **Cloud Storage**              | Store product images and defect detection results                         |
| **Firestore**                  | Store defect logs, quality metrics, and production records                |
| **Secret Manager**             | Store API keys and connection strings instead of .env files               |
| **Cloud Monitoring + Logging** | Track detection latency, defect rates, pass/fail ratios                   |

---

## Recommended Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Firebase Hosting — React Frontend                          │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTPS
┌──────────────────────▼──────────────────────────────────────┐
│  Cloud Run — Backend (FastAPI :8000)                        │
└──────────────────────┬──────────────────────────────────────┘
                       │ Internal HTTPS
        ┌──────────────┴──────────────┐
        │ Option A                    │ Option B
        ▼                             ▼
┌───────────────────┐    ┌────────────────────────────────────┐
│ Cloud Run         │    │ Vertex AI AutoML Vision            │
│ CV Service :8001  │    │ Manufacturing defect detection     │
│ YOLOv8+OpenCV     │    │ No model training needed           │
└───────────────────┘    └────────────────────────────────────┘
```

---

## Prerequisites

```bash
gcloud auth login
gcloud projects create defectdetect-cv-project --name="Defect Detection Manufacturing"
gcloud config set project defectdetect-cv-project
gcloud services enable run.googleapis.com artifactregistry.googleapis.com \
  secretmanager.googleapis.com aiplatform.googleapis.com vision.googleapis.com \
  firestore.googleapis.com storage.googleapis.com cloudbuild.googleapis.com
```

---

## Step 1 — Create Artifact Registry and Push Images

```bash
GCP_REGION=europe-west2
gcloud artifacts repositories create defectdetect-repo \
  --repository-format=docker --location=$GCP_REGION
gcloud auth configure-docker $GCP_REGION-docker.pkg.dev
AR=$GCP_REGION-docker.pkg.dev/defectdetect-cv-project/defectdetect-repo
docker build -f docker/Dockerfile.cv-service -t $AR/cv-service:latest ./cv-service
docker push $AR/cv-service:latest
docker build -f docker/Dockerfile.backend -t $AR/backend:latest ./backend
docker push $AR/backend:latest
```

---

## Step 2 — Deploy to Cloud Run

```bash
gcloud run deploy cv-service \
  --image $AR/cv-service:latest --region $GCP_REGION \
  --port 8001 --no-allow-unauthenticated \
  --min-instances 1 --max-instances 3 --memory 2Gi --cpu 1

CV_URL=$(gcloud run services describe cv-service --region $GCP_REGION --format "value(status.url)")

gcloud run deploy backend \
  --image $AR/backend:latest --region $GCP_REGION \
  --port 8000 --allow-unauthenticated \
  --min-instances 1 --max-instances 5 --memory 1Gi --cpu 1 \
  --set-env-vars CV_SERVICE_URL=$CV_URL
```

---

## Option B — Use Vertex AI AutoML Vision

```python
from google.cloud import aiplatform
import base64

aiplatform.init(project="defectdetect-cv-project", location="europe-west2")
endpoint = aiplatform.Endpoint("projects/defectdetect-cv-project/locations/europe-west2/endpoints/<endpoint-id>")

def detect_defects(image_bytes: bytes) -> dict:
    instances = [{"content": base64.b64encode(image_bytes).decode()}]
    prediction = endpoint.predict(instances=instances)
    result = prediction.predictions[0]
    defects = []
    for i, label in enumerate(result.get("displayNames", [])):
        confidence = result.get("confidences", [])[i] if i < len(result.get("confidences", [])) else 0
        if confidence > 0.4:
            defects.append({"type": label, "confidence": round(confidence * 100, 2)})
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

| Service                    | Tier                  | Est. Cost          |
|----------------------------|-----------------------|--------------------|
| Cloud Run (backend)        | 1 vCPU / 1 GB         | ~$10–15/month      |
| Cloud Run (cv-service)     | 1 vCPU / 2 GB         | ~$12–18/month      |
| Artifact Registry          | Storage               | ~$1–2/month        |
| Firebase Hosting           | Free tier             | $0                 |
| Vertex AI AutoML           | Pay per node hour     | Pay per use        |
| **Total (Option A)**       |                       | **~$23–35/month**  |
| **Total (Option B)**       |                       | **~$12–18/month + training cost** |

For exact estimates → https://cloud.google.com/products/calculator

---

## Teardown

```bash
gcloud run services delete backend --region $GCP_REGION --quiet
gcloud run services delete cv-service --region $GCP_REGION --quiet
gcloud artifacts repositories delete defectdetect-repo --location=$GCP_REGION --quiet
gcloud projects delete defectdetect-cv-project
```
