# Deployment Guide - Healthcare AI Agent

> **Production deployment guide with Docker, Kubernetes, and cloud platforms**

## Table of Contents

- [Deployment Overview](#deployment-overview)
- [Docker Deployment](#docker-deployment)
- [Kubernetes Deployment](#kubernetes-deployment)
- [Cloud Platform Deployment](#cloud-platform-deployment)
- [Environment Configuration](#environment-configuration)
- [Monitoring & Logging](#monitoring--logging)
- [Security Hardening](#security-hardening)
- [Backup & Recovery](#backup--recovery)

## Deployment Overview

Healthcare AI Agent supports multiple deployment strategies:

1. **Docker Compose** - Single server deployment
2. **Kubernetes** - Container orchestration
3. **Google Cloud Platform** - Managed cloud services
4. **AWS** - Alternative cloud deployment
5. **Azure** - Microsoft cloud platform

### Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Load Balancer │    │   Frontend      │    │   Backend APIs  │
│   (Nginx/ALB)   │◄──►│   (Next.js)     │◄──►│   (Flask)       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   CDN           │    │   Database      │    │   External APIs │
│   (CloudFlare)  │    │   (Firebase)    │    │   (Groq/Maps)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Docker Deployment

### 1. Create Dockerfiles

**Frontend Dockerfile**:
```dockerfile
# Dockerfile.frontend
FROM node:18-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production

COPY . .
RUN npm run build

FROM node:18-alpine AS runner
WORKDIR /app

ENV NODE_ENV production
RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs
EXPOSE 3000
ENV PORT 3000

CMD ["node", "server.js"]
```**Bac
kend Dockerfile**:
```dockerfile
# Dockerfile.backend
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd --create-home --shell /bin/bash app
RUN chown -R app:app /app
USER app

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

EXPOSE 5000
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "app:app"]
```

### 2. Docker Compose Configuration

**docker-compose.yml**:
```yaml
version: '3.8'

services:
  # Frontend Service
  frontend:
    build:
      context: .
      dockerfile: Dockerfile.frontend
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=production
      - NEXT_PUBLIC_API_URL=http://nginx:80
    depends_on:
      - nginx
    restart: unless-stopped

  # Backend Services
  ambulance-service:
    build:
      context: .
      dockerfile: Dockerfile.backend
    environment:
      - FLASK_APP=ambulance.py
      - PORT=5001
    volumes:
      - ./config:/app/config:ro
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5001/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  chatbot-service:
    build:
      context: .
      dockerfile: Dockerfile.backend
    environment:
      - FLASK_APP=chatbot.py
      - PORT=5002
    volumes:
      - ./config:/app/config:ro
    restart: unless-stopped

  document-service:
    build:
      context: .
      dockerfile: Dockerfile.backend
    environment:
      - FLASK_APP=document.py
      - PORT=5003
    volumes:
      - ./config:/app/config:ro
      - document-uploads:/app/uploads
    restart: unless-stopped

  location-service:
    build:
      context: .
      dockerfile: Dockerfile.backend
    environment:
      - FLASK_APP=location.py
      - PORT=5004
    volumes:
      - ./config:/app/config:ro
    restart: unless-stopped

  yoga-service:
    build:
      context: .
      dockerfile: Dockerfile.backend
    environment:
      - FLASK_APP=yoga.py
      - PORT=5005
    volumes:
      - ./config:/app/config:ro
    restart: unless-stopped

  # Load Balancer
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - ambulance-service
      - chatbot-service
      - document-service
      - location-service
      - yoga-service
    restart: unless-stopped

  # Redis Cache
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    command: redis-server --appendonly yes
    restart: unless-stopped

  # Monitoring
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - prometheus-data:/prometheus
    restart: unless-stopped

  grafana:
    image: grafana/grafana
    ports:
      - "3001:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin123
    volumes:
      - grafana-data:/var/lib/grafana
    restart: unless-stopped

volumes:
  redis-data:
  prometheus-data:
  grafana-data:
  document-uploads:

networks:
  default:
    driver: bridge
```

### 3. Nginx Configuration

**nginx.conf**:
```nginx
events {
    worker_connections 1024;
}

http {
    upstream backend {
        least_conn;
        server ambulance-service:5001;
        server chatbot-service:5002;
        server document-service:5003;
        server location-service:5004;
        server yoga-service:5005;
    }

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=login:10m rate=1r/s;

    server {
        listen 80;
        server_name healthcare-ai-agent.com;

        # Redirect HTTP to HTTPS
        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl http2;
        server_name healthcare-ai-agent.com;

        # SSL Configuration
        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;

        # Security Headers
        add_header X-Frame-Options DENY;
        add_header X-Content-Type-Options nosniff;
        add_header X-XSS-Protection "1; mode=block";
        add_header Strict-Transport-Security "max-age=31536000; includeSubDomains";

        # Frontend
        location / {
            proxy_pass http://frontend:3000;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # API Routes
        location /api/ {
            limit_req zone=api burst=20 nodelay;
            
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # CORS Headers
            add_header Access-Control-Allow-Origin *;
            add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS";
            add_header Access-Control-Allow-Headers "Authorization, Content-Type";
        }

        # Health Checks
        location /health {
            access_log off;
            return 200 "healthy\n";
            add_header Content-Type text/plain;
        }
    }
}
```

### 4. Deploy with Docker Compose

```bash
# Production deployment
docker-compose -f docker-compose.yml up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f

# Scale services
docker-compose up -d --scale chatbot-service=3

# Update services
docker-compose pull
docker-compose up -d --no-deps --build <service-name>
```

## Kubernetes Deployment

### 1. Namespace and ConfigMap

**namespace.yaml**:
```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: healthcare-ai-agent
  labels:
    name: healthcare-ai-agent
```

**configmap.yaml**:
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
  namespace: healthcare-ai-agent
data:
  NODE_ENV: "production"
  API_BASE_URL: "https://api.healthcare-ai-agent.com"
  REDIS_URL: "redis://redis-service:6379"
  LOG_LEVEL: "info"
```

### 2. Secrets Management

**secrets.yaml**:
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: app-secrets
  namespace: healthcare-ai-agent
type: Opaque
data:
  GROQ_API_KEY: <base64-encoded-key>
  GOOGLE_MAPS_API_KEY: <base64-encoded-key>
  JWT_SECRET: <base64-encoded-secret>
  FIREBASE_ADMIN_SDK: <base64-encoded-json>
```

### 3. Deployments

**frontend-deployment.yaml**:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: frontend
  namespace: healthcare-ai-agent
spec:
  replicas: 3
  selector:
    matchLabels:
      app: frontend
  template:
    metadata:
      labels:
        app: frontend
    spec:
      containers:
      - name: frontend
        image: healthcare/frontend:latest
        ports:
        - containerPort: 3000
        env:
        - name: NODE_ENV
          valueFrom:
            configMapKeyRef:
              name: app-config
              key: NODE_ENV
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 3000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 3000
          initialDelaySeconds: 5
          periodSeconds: 5
```

**backend-deployment.yaml**:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: chatbot-service
  namespace: healthcare-ai-agent
spec:
  replicas: 3
  selector:
    matchLabels:
      app: chatbot-service
  template:
    metadata:
      labels:
        app: chatbot-service
    spec:
      containers:
      - name: chatbot-service
        image: healthcare/backend:latest
        ports:
        - containerPort: 5002
        env:
        - name: FLASK_APP
          value: "chatbot.py"
        - name: PORT
          value: "5002"
        - name: GROQ_API_KEY
          valueFrom:
            secretKeyRef:
              name: app-secrets
              key: GROQ_API_KEY
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 5002
          initialDelaySeconds: 30
          periodSeconds: 10
```

### 4. Services and Ingress

**services.yaml**:
```yaml
apiVersion: v1
kind: Service
metadata:
  name: frontend-service
  namespace: healthcare-ai-agent
spec:
  selector:
    app: frontend
  ports:
  - port: 80
    targetPort: 3000
  type: ClusterIP

---
apiVersion: v1
kind: Service
metadata:
  name: chatbot-service
  namespace: healthcare-ai-agent
spec:
  selector:
    app: chatbot-service
  ports:
  - port: 5002
    targetPort: 5002
  type: ClusterIP
```

**ingress.yaml**:
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: healthcare-ingress
  namespace: healthcare-ai-agent
  annotations:
    kubernetes.io/ingress.class: "nginx"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
    nginx.ingress.kubernetes.io/rate-limit: "100"
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
spec:
  tls:
  - hosts:
    - healthcare-ai-agent.com
    - api.healthcare-ai-agent.com
    secretName: healthcare-tls
  rules:
  - host: healthcare-ai-agent.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: frontend-service
            port:
              number: 80
  - host: api.healthcare-ai-agent.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: chatbot-service
            port:
              number: 5002
```

### 5. Deploy to Kubernetes

```bash
# Apply configurations
kubectl apply -f namespace.yaml
kubectl apply -f configmap.yaml
kubectl apply -f secrets.yaml
kubectl apply -f frontend-deployment.yaml
kubectl apply -f backend-deployment.yaml
kubectl apply -f services.yaml
kubectl apply -f ingress.yaml

# Check deployment status
kubectl get pods -n healthcare-ai-agent
kubectl get services -n healthcare-ai-agent
kubectl get ingress -n healthcare-ai-agent

# Scale deployments
kubectl scale deployment chatbot-service --replicas=5 -n healthcare-ai-agent

# Rolling update
kubectl set image deployment/frontend frontend=healthcare/frontend:v2.0 -n healthcare-ai-agent

# Check rollout status
kubectl rollout status deployment/frontend -n healthcare-ai-agent
```

## Cloud Platform Deployment

### 1. Google Cloud Platform (GCP)

**Deploy to Google Kubernetes Engine (GKE)**:

```bash
# Create GKE cluster
gcloud container clusters create healthcare-cluster \
    --zone=us-central1-a \
    --num-nodes=3 \
    --enable-autoscaling \
    --min-nodes=1 \
    --max-nodes=10 \
    --machine-type=e2-standard-4

# Get credentials
gcloud container clusters get-credentials healthcare-cluster --zone=us-central1-a

# Deploy application
kubectl apply -f k8s/
```

**Cloud Run Deployment**:
```bash
# Build and push images
gcloud builds submit --tag gcr.io/PROJECT_ID/healthcare-frontend
gcloud builds submit --tag gcr.io/PROJECT_ID/healthcare-backend

# Deploy to Cloud Run
gcloud run deploy healthcare-frontend \
    --image gcr.io/PROJECT_ID/healthcare-frontend \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated

gcloud run deploy healthcare-backend \
    --image gcr.io/PROJECT_ID/healthcare-backend \
    --platform managed \
    --region us-central1 \
    --set-env-vars GROQ_API_KEY=$GROQ_API_KEY
```

### 2. Amazon Web Services (AWS)

**Deploy to EKS**:
```bash
# Create EKS cluster
eksctl create cluster --name healthcare-cluster --region us-west-2 --nodes 3

# Deploy application
kubectl apply -f k8s/
```

**Deploy to ECS with Fargate**:
```json
{
  "family": "healthcare-ai-agent",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "executionRoleArn": "arn:aws:iam::ACCOUNT:role/ecsTaskExecutionRole",
  "containerDefinitions": [
    {
      "name": "frontend",
      "image": "healthcare/frontend:latest",
      "portMappings": [
        {
          "containerPort": 3000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "NODE_ENV",
          "value": "production"
        }
      ]
    }
  ]
}
```

## Environment Configuration

### 1. Production Environment Variables

```bash
# Application Configuration
NODE_ENV=production
PORT=3000
API_BASE_URL=https://api.healthcare-ai-agent.com

# Database Configuration
FIREBASE_PROJECT_ID=healthcare-ai-prod
FIREBASE_API_KEY=your_production_firebase_key
REDIS_URL=redis://redis-cluster:6379

# External APIs
GROQ_API_KEY=your_production_groq_key
GOOGLE_MAPS_API_KEY=your_production_maps_key

# Security
JWT_SECRET=your_production_jwt_secret
ENCRYPTION_KEY=your_production_encryption_key

# Monitoring
SENTRY_DSN=your_sentry_dsn
LOG_LEVEL=info
ENABLE_METRICS=true

# Performance
CACHE_TTL=3600
MAX_UPLOAD_SIZE=10485760
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=3600
```

### 2. Configuration Management

**Using Kubernetes ConfigMaps and Secrets**:
```bash
# Create from files
kubectl create configmap app-config --from-env-file=.env.production
kubectl create secret generic app-secrets --from-env-file=.env.secrets

# Create from literals
kubectl create secret generic api-keys \
    --from-literal=groq-api-key='your-key' \
    --from-literal=maps-api-key='your-key'
```

## Monitoring & Logging

### 1. Prometheus Configuration

**prometheus.yml**:
```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'healthcare-ai-agent'
    static_configs:
      - targets: ['frontend:3000', 'chatbot-service:5002']
    metrics_path: /metrics
    scrape_interval: 30s

  - job_name: 'kubernetes-pods'
    kubernetes_sd_configs:
      - role: pod
    relabel_configs:
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
        action: keep
        regex: true
```

### 2. Grafana Dashboards

**Application Metrics Dashboard**:
- Request rate and response time
- Error rate and status codes
- CPU and memory usage
- Database connection pool
- Cache hit/miss ratio

### 3. Centralized Logging

**Fluentd Configuration**:
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: fluentd-config
data:
  fluent.conf: |
    <source>
      @type tail
      path /var/log/containers/*.log
      pos_file /var/log/fluentd-containers.log.pos
      tag kubernetes.*
      format json
    </source>
    
    <match kubernetes.**>
      @type elasticsearch
      host elasticsearch.logging.svc.cluster.local
      port 9200
      index_name healthcare-logs
    </match>
```

## Security Hardening

### 1. Container Security

```dockerfile
# Use non-root user
RUN useradd --create-home --shell /bin/bash app
USER app

# Remove unnecessary packages
RUN apt-get remove -y gcc g++ && apt-get autoremove -y

# Set read-only filesystem
VOLUME ["/tmp"]
```

### 2. Network Security

**Network Policies**:
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: healthcare-network-policy
spec:
  podSelector:
    matchLabels:
      app: chatbot-service
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: frontend
    ports:
    - protocol: TCP
      port: 5002
```

### 3. Security Scanning

```bash
# Scan container images
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
    aquasec/trivy image healthcare/frontend:latest

# Kubernetes security scanning
kubectl run --rm -it --restart=Never kube-bench \
    --image=aquasec/kube-bench:latest -- --version 1.20
```

## Backup & Recovery

### 1. Database Backup

```bash
# Firebase backup (using Cloud Functions)
gcloud functions deploy backup-firestore \
    --runtime python39 \
    --trigger-topic backup-schedule \
    --entry-point backup_firestore

# Schedule backups
gcloud scheduler jobs create pubsub backup-job \
    --schedule="0 2 * * *" \
    --topic=backup-schedule \
    --message-body="{}"
```

### 2. Application State Backup

```yaml
# Kubernetes CronJob for backups
apiVersion: batch/v1
kind: CronJob
metadata:
  name: backup-job
spec:
  schedule: "0 2 * * *"
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: backup
            image: healthcare/backup:latest
            command:
            - /bin/sh
            - -c
            - |
              kubectl get all -o yaml > /backup/k8s-backup-$(date +%Y%m%d).yaml
              gsutil cp /backup/* gs://healthcare-backups/
          restartPolicy: OnFailure
```

### 3. Disaster Recovery Plan

1. **RTO (Recovery Time Objective)**: 4 hours
2. **RPO (Recovery Point Objective)**: 1 hour
3. **Backup Frequency**: Daily automated backups
4. **Multi-region deployment** for high availability
5. **Automated failover** using health checks

---

**Deployment Checklist**:
- [ ] Environment variables configured
- [ ] SSL certificates installed
- [ ] Database migrations completed
- [ ] Health checks passing
- [ ] Monitoring configured
- [ ] Backup strategy implemented
- [ ] Security scanning completed
- [ ] Load testing performed
- [ ] Documentation updated