# 분리 배포 가이드: Vercel + Render

## 아키텍처

```
┌─────────────────┐     HTTP     ┌─────────────────┐
│   React.js      │ ──────────▶  │    FastAPI      │
│   (Vercel)      │              │   (Render)      │
│   무료 ∞        │              │   무료 (슬립)    │
└─────────────────┘              └─────────────────┘
```

---

## Step 1: GitHub 저장소 생성 (필수)

```bash
cd /Users/cyanluna-pro16/Documents/0.Dev/aiworkout.planner

# .gitignore 확인
git init
git add .
git commit -m "Initial commit: AI Cycling Coach"

# GitHub에서 새 저장소 생성 후:
git remote add origin https://github.com/YOUR_USERNAME/aiworkout.planner.git
git push -u origin main
```

---

## Step 2: Render 백엔드 배포

### 2.1 가입
1. https://render.com 접속
2. **"Get Started for Free"** 클릭
3. **"GitHub"** 로 가입

### 2.2 Web Service 생성
1. Dashboard → **"New +"** → **"Web Service"**
2. **"Connect a repository"** → `aiworkout.planner` 선택
3. 설정:
   - **Name**: `ai-cycling-coach-api`
   - **Region**: Singapore (Southeast Asia) ← 한국에서 가장 빠름!
   - **Branch**: main
   - **Root Directory**: (비워둠)
   - **Runtime**: Python 3
   - **Build Command**: `pip install -e .`
   - **Start Command**: `uvicorn api.main:app --host 0.0.0.0 --port $PORT`

### 2.3 환경 변수 설정
Dashboard → Environment 탭에서 추가:
```
INTERVALS_API_KEY=your_intervals_api_key
ATHLETE_ID=i12345
LLM_API_KEY=your_gemini_api_key
LLM_PROVIDER=gemini
LLM_MODEL=gemini-2.0-flash-exp
FTP=250
MAX_HR=190
LTHR=170
TRAINING_GOAL=지구력 강화
```

### 2.4 배포 완료
- **URL 확인**: `https://ai-cycling-coach-api.onrender.com`
- 테스트: `curl https://YOUR-URL.onrender.com/api/health`

---

## Step 3: Vercel 프론트엔드 배포

### 3.1 가입
1. https://vercel.com 접속
2. **"Sign Up"** → **"Continue with GitHub"**

### 3.2 프로젝트 가져오기
1. **"Add New..."** → **"Project"**
2. `aiworkout.planner` 선택
3. **Configure Project**:
   - **Root Directory**: `frontend` ← 중요!
   - **Framework Preset**: Vite (자동 감지)
4. **"Deploy"** 클릭

### 3.3 환경 변수 설정
Settings → Environment Variables:
```
VITE_API_URL=https://ai-cycling-coach-api.onrender.com
```
(Step 2에서 받은 Render URL 입력)

### 3.4 재배포
환경변수 설정 후 **Deployments** → **Redeploy** 필요

---

## Step 4: CORS 설정 업데이트

배포 완료 후 `api/main.py` 수정:

```python
origins = [
    "http://localhost:5173",
    "https://your-app.vercel.app",  # 실제 Vercel URL로 변경
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # "*" 대신 origins 사용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 완료 체크리스트

- [ ] GitHub 저장소 생성 & 푸시
- [ ] Render 백엔드 배포
- [ ] Vercel 프론트엔드 배포
- [ ] 환경변수 설정
- [ ] CORS 도메인 업데이트
- [ ] 전체 테스트
