# AWS Deployment Guide — Project CV-19 Defect Detection Manufacturing

---

## AWS Services for Manufacturing Defect Detection

### 1. Ready-to-Use AI (No Model Needed)

| Service                    | What it does                                                                 | When to use                                        |
|----------------------------|------------------------------------------------------------------------------|----------------------------------------------------|
| **Amazon Lookout for Vision** | Detect product defects, anomalies, and quality issues — purpose-built for manufacturing | Replace your YOLOv8 defect detection pipeline |
| **Amazon Rekognition Custom** | Train custom defect detector on your labelled product images              | When you need custom defect categories             |
| **Amazon Bedrock**         | Claude Vision for defect analysis and quality assessment via prompt          | When you need flexible defect understanding        |

> **Amazon Lookout for Vision** is purpose-built for manufacturing defect detection. It detects surface defects, cracks, scratches, and anomalies — no custom model training needed.

### 2. Host Your Own Model (Keep Current Stack)

| Service                    | What it does                                                        | When to use                                           |
|----------------------------|---------------------------------------------------------------------|-------------------------------------------------------|
| **AWS App Runner**         | Run backend container — simplest, no VPC or cluster needed          | Quickest path to production                           |
| **Amazon ECS Fargate**     | Run backend + cv-service containers in a private VPC                | Best match for your current microservice architecture |
| **Amazon ECR**             | Store your Docker images                                            | Used with App Runner, ECS, or EKS                     |

### 3. Supporting Services

| Service                  | Purpose                                                                   |
|--------------------------|---------------------------------------------------------------------------|
| **Amazon S3**            | Store product images and defect detection results                         |
| **Amazon DynamoDB**      | Store defect logs, quality metrics, and production records                |
| **AWS Secrets Manager**  | Store API keys and connection strings instead of .env files               |
| **Amazon CloudWatch**    | Track detection latency, defect rates, pass/fail ratios                   |

---

## Recommended Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  S3 + CloudFront — React Frontend                           │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTPS
┌──────────────────────▼──────────────────────────────────────┐
│  AWS App Runner / ECS Fargate — Backend (FastAPI :8000)     │
└──────────────────────┬──────────────────────────────────────┘
                       │ Internal
        ┌──────────────┴──────────────┐
        │ Option A                    │ Option B
        ▼                             ▼
┌───────────────────┐    ┌────────────────────────────────────┐
│ ECS Fargate       │    │ Amazon Lookout for Vision          │
│ CV Service :8001  │    │ Manufacturing defect detection     │
│ YOLOv8+OpenCV     │    │ No model training needed           │
└───────────────────┘    └────────────────────────────────────┘
```

---

## Prerequisites

```bash
aws configure
AWS_REGION=eu-west-2
AWS_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
```

---

## Step 1 — Create ECR and Push Images

```bash
aws ecr create-repository --repository-name defectdetect/cv-service --region $AWS_REGION
aws ecr create-repository --repository-name defectdetect/backend --region $AWS_REGION
ECR=$AWS_ACCOUNT.dkr.ecr.$AWS_REGION.amazonaws.com
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR
docker build -f docker/Dockerfile.cv-service -t $ECR/defectdetect/cv-service:latest ./cv-service
docker push $ECR/defectdetect/cv-service:latest
docker build -f docker/Dockerfile.backend -t $ECR/defectdetect/backend:latest ./backend
docker push $ECR/defectdetect/backend:latest
```

---

## Step 2 — Deploy with App Runner

```bash
aws apprunner create-service \
  --service-name defectdetect-backend \
  --source-configuration '{
    "ImageRepository": {
      "ImageIdentifier": "'$ECR'/defectdetect/backend:latest",
      "ImageRepositoryType": "ECR",
      "ImageConfiguration": {
        "Port": "8000",
        "RuntimeEnvironmentVariables": {
          "CV_SERVICE_URL": "http://cv-service:8001"
        }
      }
    }
  }' \
  --instance-configuration '{"Cpu": "1 vCPU", "Memory": "2 GB"}' \
  --region $AWS_REGION
```

---

## Option B — Use Amazon Lookout for Vision

```python
import boto3

lookout = boto3.client("lookoutvision", region_name="eu-west-2")

def detect_defects(project_name: str, model_version: str, image_bytes: bytes) -> dict:
    response = lookout.detect_anomalies(
        ProjectName=project_name,
        ModelVersion=model_version,
        Body=image_bytes,
        ContentType="image/jpeg"
    )
    result = response["DetectAnomalyResult"]
    status = "fail" if result["IsAnomalous"] else "pass"
    return {
        "status": status,
        "is_defective": result["IsAnomalous"],
        "confidence": round(result["Confidence"] * 100, 2),
        "defects": [{"type": a["Name"], "area_pct": round(a["PixelAnomaly"]["TotalPercentageArea"] * 100, 2)} for a in result.get("Anomalies", [])],
        "quality_verdict": "PASS" if not result["IsAnomalous"] else "FAIL"
    }
```

---

## Estimated Monthly Cost

| Service                    | Tier              | Est. Cost          |
|----------------------------|-------------------|--------------------|
| App Runner (backend)       | 1 vCPU / 2 GB     | ~$20–25/month      |
| App Runner (cv-service)    | 1 vCPU / 2 GB     | ~$20–25/month      |
| ECR + S3 + CloudFront      | Standard          | ~$3–7/month        |
| Lookout for Vision         | Pay per image     | ~$4/1000 images    |
| **Total (Option A)**       |                   | **~$43–57/month**  |
| **Total (Option B)**       |                   | **~$23–32/month**  |

For exact estimates → https://calculator.aws

---

## Teardown

```bash
aws ecr delete-repository --repository-name defectdetect/backend --force
aws ecr delete-repository --repository-name defectdetect/cv-service --force
```
