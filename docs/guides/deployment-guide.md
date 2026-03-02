# Deployment Guide

> **Last Updated**: 2026-01-11  
> **Production Stack**: Vercel (Frontend) + Google Cloud Run (Backend)

---

## System Overview

```
┌─────────────────┐     HTTPS    ┌─────────────────────────┐
│   React + Vite  │ ──────────▶  │    FastAPI Backend      │
│   (Vercel CDN)  │              │  (Google Cloud Run)     │
│                 │              │  asia-northeast3 (서울)  │
└─────────────────┘              └─────────────────────────┘
```

**Production URLs:**
- **Frontend**: https://ai-cycling-workout-planner.vercel.app
- **Backend**: https://cycling-coach-backend-25085100592.asia-northeast3.run.app
- **API Docs**: Backend URL + `/docs`

---

## Prerequisites

1. **GitHub Repository** (public or private)
2. **Accounts**:
   - [Vercel](https://vercel.com) (free)
   - [Google Cloud Platform](https://console.cloud.google.com) (pay-as-you-go)
   - [Supabase](https://supabase.com) (free tier)
3. **Tools**:
   - Git
   - gcloud CLI (optional, for advanced management)

---

## Part 1: Backend Deployment (Google Cloud Run)

### Step 1: GCP Project Setup

1. Create or use existing project: `gen-lang-client-0043735738`
2. Enable required APIs:
   ```bash
   gcloud services enable run.googleapis.com
   gcloud services enable cloudbuild.googleapis.com
   gcloud services enable containerregistry.googleapis.com
   ```

### Step 2: Create Cloud Build Trigger

1. Go to [Cloud Build Triggers](https://console.cloud.google.com/cloud-build/triggers)
2. Click **"Create Trigger"**
3. Configure:
   - **Name**: `deploy-backend`
   - **Event**: Push to a branch
   - **Source**: Your GitHub repository
   - **Branch**: `^main$`
   - **Configuration**: Cloud Build configuration file
   - **Location**: `/cloudbuild.yaml`
4. Click **"Create"**

### Step 3: Verify cloudbuild.yaml

Ensure this file exists at repository root:

```yaml
steps:
  # Build Docker image
  - name: 'gcr.io/cloud-builders/docker'
    args: [
      'build',
      '-t', 'gcr.io/$PROJECT_ID/cycling-coach-backend:$COMMIT_SHA',
      '-t', 'gcr.io/$PROJECT_ID/cycling-coach-backend:latest',
      '-f', 'Dockerfile.backend',
      '.'
    ]
  
  # Push images
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/$PROJECT_ID/cycling-coach-backend:$COMMIT_SHA']
  
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/$PROJECT_ID/cycling-coach-backend:latest']
  
  # Deploy to Cloud Run
  - name: 'gcr.io/cloud-builders/gcloud'
    args: [
      'run', 'deploy', 'cycling-coach-backend',
      '--image', 'gcr.io/$PROJECT_ID/cycling-coach-backend:$COMMIT_SHA',
      '--region', 'asia-northeast3',
      '--platform', 'managed',
      '--allow-unauthenticated',
      '--min-instances', '1',
      '--max-instances', '10',
      '--cpu', '1',
      '--memory', '512Mi',
      '--timeout', '300s'
    ]

images:
  - 'gcr.io/$PROJECT_ID/cycling-coach-backend:$COMMIT_SHA'
  - 'gcr.io/$PROJECT_ID/cycling-coach-backend:latest'
```

### Step 4: Set Environment Variables

1. Go to [Cloud Run Console](https://console.cloud.google.com/run)
2. Click service: `cycling-coach-backend`
3. Click **"Edit & Deploy New Revision"**
4. Go to **"Variables & Secrets"** tab
5. Add variables:

```bash
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_ANON_KEY=eyJ...
SUPABASE_SERVICE_ROLE_KEY=eyJ...
VERCEL_AI_GATEWAY_API_KEY=xxx
LLM_PROVIDER=vercel-gateway
ADMIN_SECRET=your-secret-key
PORT=8080
```

6. Click **"Deploy"**

### Step 5: Deploy Backend

```bash
git add .
git commit -m "Deploy backend to Cloud Run"
git push origin main
```

Cloud Build will automatically:
- Build Docker image
- Push to Container Registry
- Deploy to Cloud Run
- Run health check

**Verify deployment:**
```bash
curl https://cycling-coach-backend-25085100592.asia-northeast3.run.app/api/health
```

Expected response:
```json
{"status": "healthy", "timestamp": "2026-01-11T..."}
```

---

## Part 2: Frontend Deployment (Vercel)

### Step 1: Import Project

1. Go to [Vercel Dashboard](https://vercel.com/dashboard)
2. Click **"Add New..."** → **"Project"**
3. Import your GitHub repository

### Step 2: Configure Build Settings

**Important**: Set Root Directory to `frontend`

- **Framework Preset**: Vite (auto-detected)
- **Root Directory**: `frontend` ⚠️
- **Build Command**: `pnpm run build` (default)
- **Output Directory**: `dist` (default)
- **Install Command**: `pnpm install` (default)

### Step 3: Set Environment Variables

Go to **"Environment Variables"** section:

```bash
VITE_API_URL=https://cycling-coach-backend-25085100592.asia-northeast3.run.app
VITE_SUPABASE_URL=https://xxx.supabase.co
VITE_SUPABASE_ANON_KEY=eyJ...
```

⚠️ **Important**: All Vite env vars must start with `VITE_`

### Step 4: Deploy

Click **"Deploy"**

Vercel will:
1. Clone repository
2. Install dependencies
3. Build project
4. Deploy to global CDN

**Deployment time**: ~2-3 minutes

**Production URL**: Will be shown after deployment

---

## Part 3: CORS Configuration

Update backend CORS to allow Vercel domain.

Edit `api/main.py`:

```python
origins = [
    "http://localhost:5173",  # Local dev
    "http://localhost:3101",
    "https://ai-cycling-workout-planner.vercel.app",  # Production
    "https://*.vercel.app",  # Preview deployments
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

Commit and push to trigger backend redeployment:

```bash
git add api/main.py
git commit -m "Update CORS for Vercel domain"
git push origin main
```

---

## Verification

### Backend Health Check

```bash
curl https://cycling-coach-backend-25085100592.asia-northeast3.run.app/api/health
```

### Frontend Access

Open https://ai-cycling-workout-planner.vercel.app

### API Documentation

Visit https://cycling-coach-backend-25085100592.asia-northeast3.run.app/docs

---

## CI/CD Pipeline

### Automatic Deployment Flow

```
Developer commits to main
        ↓
GitHub detects push
        ↓
    ┌───────┴──────┐
    ↓              ↓
Backend (GCP)   Frontend (Vercel)
Cloud Build     Vercel Build
    ↓              ↓
Docker Build    pnpm build
    ↓              ↓
Cloud Run       CDN Deploy
Deploy          
    ↓              ↓
Live in ~5min   Live in ~2min
```

### Zero-Downtime Deployment

- **Backend**: Cloud Run with `min-instances=1` ensures no cold starts
- **Frontend**: Vercel atomic deployments (instant switch)

---

## Monitoring

### Backend Logs (GCP)

**Real-time logs:**
```bash
gcloud logging tail "resource.type=cloud_run_revision" --project=gen-lang-client-0043735738
```

**Console**: [Cloud Run Logs](https://console.cloud.google.com/run/detail/asia-northeast3/cycling-coach-backend/logs)

### Frontend Analytics

- **Vercel Analytics**: https://vercel.com/dashboard/analytics
- Web Vitals (LCP, FID, CLS)
- Page views and load times

### Metrics Dashboard

- **GCP Console**: [Metrics](https://console.cloud.google.com/run/detail/asia-northeast3/cycling-coach-backend/metrics)
- Request count
- Response time (p50, p95, p99)
- Error rate
- Container instances

---

## Rollback Procedures

### Backend Rollback

**Option 1: Via Console**
1. Go to Cloud Run console
2. **Revisions** tab
3. Select previous revision
4. **Manage Traffic** → Route 100% to previous

**Option 2: Via CLI**
```bash
gcloud run services update-traffic cycling-coach-backend \
  --region=asia-northeast3 \
  --to-revisions=PREVIOUS_REVISION=100
```

### Frontend Rollback

1. Go to Vercel Deployments
2. Find previous successful deployment
3. Click **"..."** → **"Promote to Production"**

Takes ~30 seconds.

---

## Cost Estimation

### Google Cloud Run

**Pricing (asia-northeast3):**
- vCPU: $0.00002400/second
- Memory: $0.0000025/GiB-second
- Requests: $0.40/million

**Estimated (50 users, 100 workouts/day):**
- Always-on (min-instances=1): ~$20/month
- Requests: ~$1/month
- **Total**: ~$21/month

### Vercel (Free Tier)

- Unlimited deployments
- Unlimited bandwidth
- 100 GB-hours/month

**Cost**: $0

### Total Monthly Cost

**~$21** (backend only)

---

## Troubleshooting

### Backend Not Responding

```bash
# Check service status
gcloud run services describe cycling-coach-backend --region=asia-northeast3

# Check recent logs
gcloud logging read "resource.type=cloud_run_revision" --limit=50
```

### Build Failures

1. Check Cloud Build history
2. Review build logs
3. Verify Dockerfile.backend
4. Check environment variables

### CORS Errors

1. Verify `origins` list in `api/main.py`
2. Check `VITE_API_URL` in Vercel
3. Inspect browser console

### Frontend Build Fails

1. Check Vercel build logs
2. Verify `package.json` scripts
3. Ensure all dependencies listed
4. Check Node version compatibility

---

## Security Checklist

- [ ] API keys in environment variables only
- [ ] CORS origins whitelisted (no `*`)
- [ ] HTTPS enforced
- [ ] JWT expiration set (1 hour)
- [ ] Admin secret strong and unique
- [ ] Secrets never logged
- [ ] Rate limiting implemented
- [ ] Regular dependency updates

---

## Maintenance

### Weekly
- Review error logs
- Check response times
- Monitor costs

### Monthly
- Update dependencies
- Review security advisories
- Analyze usage metrics

### Quarterly
- Rotate API keys
- Cost optimization review
- Performance audit

---

## Additional Resources

- [Infrastructure Setup](infrastructure-setup.md)
- [System Architecture](../reference/system-architecture.md)
- [GCP Console](https://console.cloud.google.com/?project=gen-lang-client-0043735738)
- [Vercel Dashboard](https://vercel.com/dashboard)
- [Cloud Run Documentation](https://cloud.google.com/run/docs)

---

**Last Updated**: 2026-01-11  
**Maintained By**: AI Cycling Coach Team
