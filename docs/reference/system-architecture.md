# System Architecture

> **Last Updated**: 2026-01-11  
> **Status**: Production-ready

## Overview

AI Cycling Coach는 Intervals.icu 훈련 데이터를 기반으로 개인화된 사이클링 워크아웃을 자동 생성하고 주간 훈련 계획을 제공하며, 사이클링 컴퓨터(Wahoo, Garmin)로 직접 전송하는 종합 훈련 관리 서비스입니다.

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                           Frontend (Vercel)                          │
│                                                                      │
│   React + TypeScript + Vite + Tailwind CSS + shadcn/ui              │
│   ├── LandingPage     (마케팅)                                       │
│   ├── AuthPage        (Google OAuth / Email 로그인)                  │
│   ├── SettingsPage    (API 키 및 훈련 설정)                          │
│   └── Dashboard       (메인 앱)                                      │
│       ├── FitnessCard          (CTL/ATL/TSB 상태)                    │
│       ├── WorkoutForm          (단일 워크아웃 생성)                   │
│       ├── WorkoutPreview       (결과 미리보기)                        │
│       └── WeeklyPlanCard       (주간 훈련 계획)                       │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ HTTPS REST API
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      Backend (Google Cloud Run)                      │
│                          Region: asia-northeast3                     │
│                                                                      │
│   FastAPI + Python 3.11                                             │
│   ├── /api/auth/*        (Supabase Auth 연동)                        │
│   ├── /api/settings/*    (사용자 설정 CRUD)                          │
│   ├── /api/fitness       (Intervals.icu 피트니스 데이터)             │
│   ├── /api/workout/*     (단일 워크아웃 생성)                         │
│   ├── /api/plans/*       (주간 계획 생성 및 관리)                     │
│   └── /api/admin/*       (관리자 API - LLM 모델 관리)                 │
└─────────────────────────────────────────────────────────────────────┘
                │                      │                      │
                ▼                      ▼                      ▼
    ┌──────────────────┐  ┌───────────────────┐  ┌───────────────────┐
    │    Supabase      │  │  Vercel AI        │  │  Intervals.icu    │
    │                  │  │  Gateway          │  │  API              │
    │  - auth.users    │  │                   │  │                   │
    │  - user_api_keys │  │  - Groq Llama 3.3 │  │  - 훈련 데이터     │
    │  - user_settings │  │  - Gemini 2.0     │  │  - 워크아웃 등록   │
    │  - weekly_plans  │  │  - Auto Fallback  │  │  - 캘린더 동기화   │
    │  - audit_logs    │  │                   │  │                   │
    └──────────────────┘  └───────────────────┘  └───────────────────┘
```

---

## Core Features

### 1. AI Workout Generation

**Modular Workout System:**
- **Warmup**: 5-15분, 점진적 강도 증가
- **Main Segments**: 훈련 스타일별 맞춤 메인 세그먼트
- **Cooldown**: 5-15분, 점진적 강도 감소

**Training Styles:**
- **Polarized**: 저강도 80% + 고강도 20%
- **Norwegian**: 4x8min 임계치 + 저강도 기반
- **Sweet Spot**: 88-93% FTP 지속
- **Base**: 순수 유산소 지구력 (65-75%)
- **Threshold**: FTP 임계치 훈련

**구현 파일:**
- `src/services/workout_generator.py` - 워크아웃 생성 로직
- `src/data/workout_modules/` - 훈련 모듈 라이브러리
- `api/routers/workout.py` - API 엔드포인트

**흐름:**
```
1. 사용자 입력 (스타일, 시간, 목표)
2. Intervals.icu 데이터 조회 (CTL/ATL/TSB)
3. AI 프롬프트 생성 (사용자 상태 + 훈련 목표)
4. LLM이 모듈 조합하여 워크아웃 생성
5. 유효성 검증 (구조, 시간, TSS)
6. Intervals.icu 업로드 (ZWO 형식)
```

---

### 2. Weekly Plan Generation

**기능:**
- 월요일~일요일 7일 훈련 계획 자동 생성
- 일일 부하 균형 조절 (TSS 목표 달성)
- 회복 일정 자동 배치
- Intervals.icu 캘린더 일괄 등록

**Smart Load Management:**
```python
# 목표 주간 TSS 분배
week_tss_target = user_settings.weekly_tss_target  # 예: 500
daily_distribution = [
    0.18,  # Monday - High
    0.12,  # Tuesday - Medium
    0.16,  # Wednesday - High
    0.10,  # Thursday - Recovery
    0.18,  # Friday - High
    0.14,  # Saturday - Medium
    0.12,  # Sunday - Recovery
]
```

**구현 파일:**
- `api/services/weekly_plan_service.py` - 주간 계획 생성
- `api/routers/plans.py` - 주간 계획 API
- `frontend/src/components/WeeklyPlanCard.tsx` - UI 컴포넌트

**Database Schema:**
```sql
weekly_plans (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES auth.users,
  week_start DATE,
  week_end DATE,
  total_tss INTEGER,
  status TEXT,  -- 'draft', 'registered', 'completed'
  daily_workouts JSONB[]  -- 7-day workout array
)
```

---

### 3. Multi-LLM Fallback System

**설계 원칙:**
- 단일 프로바이더 의존성 제거
- 무료 티어 한도 초과 시 자동 전환
- Vercel AI Gateway를 통한 통합 관리

**Fallback Chain:**
```
1. Groq (llama-3.3-70b-versatile)
   - 가장 빠름 (~3초)
   - 무료: 30 requests/minute
       ↓ 쿼터 초과 시
2. Google Gemini 2.0 Flash
   - 빠르고 안정적 (~5초)
   - 무료: 15 RPM
       ↓ 쿼터 초과 시
3. Google Gemini 1.5 Flash
   - 최후 보루
   - 무료: 15 RPM
```

**구현:**
- **Vercel AI Gateway**: 통합 LLM 프록시
- **Auto Retry**: 쿼터 에러 시 자동 재시도
- **DB 기반 설정**: 런타임 모델 변경 가능

**환경 변수:**
```bash
VERCEL_AI_GATEWAY_API_KEY=xxx
LLM_PROVIDER=vercel-gateway  # Vercel Gateway 사용
```

---

### 4. Authentication System

**방식:** Supabase Auth + JWT

**지원 방법:**
- Google OAuth 2.0
- Email/Password

**흐름:**
```
1. 사용자 로그인 (Google/Email)
2. Supabase에서 JWT 토큰 발급
3. Frontend에서 토큰 저장 (localStorage)
4. 모든 API 요청에 Authorization 헤더 포함
5. Backend에서 JWT 검증
```

**구현 파일:**
- `frontend/src/contexts/AuthContext.tsx` - Auth 상태 관리
- `api/routers/auth.py` - Auth API 엔드포인트
- `api/middleware.py` - JWT 검증 미들웨어
---

### 5. Performance Optimization

**Client-Side Caching (React Query):**
```typescript
// 2시간 캐시 유지
queryClient: new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 2 * 60 * 60 * 1000,  // 2 hours
      gcTime: 5 * 60 * 1000,           // 5 minutes
      refetchOnWindowFocus: true,
    },
  },
});
```

**Backend Caching (TTL-based):**
| Data Type | TTL | Reason |
|-----------|-----|--------|
| wellness | 1h | 일일 데이터 |
| fitness | 2h | 훈련 후 업데이트 |
| calendar | 2h | 계획 변경 빈도 |
| activities | 3h | 과거 데이터 |
| profile | 6h | 거의 변경 안 됨 |

**Parallel Loading:**
- 3개 API 병렬 호출: 3.5초 → 1.8초 (**48% 개선**)
- Network waterfall 제거

**구현 파일:**
- `frontend/src/lib/queryClient.ts` - React Query 설정
- `api/services/cache_service.py` - Redis 캐싱
- [Frontend Performance Guide](../guides/frontend-performance.md)
- [Caching Strategy Guide](../guides/caching-strategy.md)

---

### 6. Audit Logging & Admin System

**Audit Logs:**
```sql
audit_logs (
  id UUID PRIMARY KEY,
  event_type TEXT,    -- user.login, workout.generated, llm.error
  user_id UUID,
  details JSONB,
  ip_address TEXT,
  created_at TIMESTAMPTZ
)
```

**Event Types:**
- `user.login/logout/signup`
- `workout.generated/sync_success/sync_failed`
- `llm.request/fallback/error`
- `api_keys.updated`
- `settings.updated`

**Admin API:**
- `GET /api/admin/audit-logs` - 로그 조회
- `GET /api/admin/audit-logs/stats` - 통계
- `DELETE /api/admin/audit-logs/cleanup` - 정리

**구현 파일:**
- `api/services/audit_service.py` - 로깅 서비스
- `api/routers/admin.py` - Admin API
- `api/middleware.py` - Request logging middleware

---

## Technology Stack

### Frontend
- **Framework**: React 18 + TypeScript
- **Build**: Vite
- **Styling**: Tailwind CSS + shadcn/ui
- **State**: React Query + Context API
- **Charts**: Recharts
- **HTTP**: Axios
- **Hosting**: Vercel (Serverless)

### Backend
- **Framework**: FastAPI (Python 3.11)
- **ORM**: Direct Supabase client
- **Validation**: Pydantic v2
- **CORS**: FastAPI middleware
- **Hosting**: Google Cloud Run (asia-northeast3)

### Infrastructure
- **Database**: Supabase (PostgreSQL)
- **Authentication**: Supabase Auth
- **AI Gateway**: Vercel AI Gateway
- **Cache**: In-memory TTL cache
- **CI/CD**: Google Cloud Build
- **Monitoring**: Google Cloud Logging

---

## Environment Variables

### Backend
```bash
# Supabase
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_ANON_KEY=xxx
SUPABASE_SERVICE_ROLE_KEY=xxx

# AI Gateway
VERCEL_AI_GATEWAY_API_KEY=xxx
LLM_PROVIDER=vercel-gateway

# Admin
ADMIN_SECRET=xxx

# Server
PORT=8005
```

### Frontend
```bash
VITE_API_URL=https://cycling-coach-backend-xxx.run.app
VITE_SUPABASE_URL=https://xxx.supabase.co
VITE_SUPABASE_ANON_KEY=xxx
```

---

## Deployment

### Production URLs
- **Frontend**: https://ai-cycling-workout-planner.vercel.app
- **Backend**: https://cycling-coach-backend-25085100592.asia-northeast3.run.app
- **API Docs**: https://cycling-coach-backend-25085100592.asia-northeast3.run.app/docs

### CI/CD Pipeline
```
GitHub Push (main)
    ↓
Google Cloud Build Trigger
    ↓
Docker Build (Dockerfile.backend)
    ↓
Deploy to Cloud Run (min-instances=1)
    ↓
Health Check (/api/health)
```

**Zero Downtime**: min-instances=1 설정으로 콜드 스타트 없음

---

## Database Schema

### Core Tables

**auth.users** (Supabase)
- User authentication and profile

**user_api_keys**
```sql
CREATE TABLE user_api_keys (
  user_id UUID PRIMARY KEY REFERENCES auth.users(id),
  intervals_api_key TEXT,
  athlete_id TEXT,
  created_at TIMESTAMPTZ,
  updated_at TIMESTAMPTZ
);
```

**user_settings**
```sql
CREATE TABLE user_settings (
  user_id UUID PRIMARY KEY REFERENCES auth.users(id),
  ftp INTEGER,
  max_hr INTEGER,
  lthr INTEGER,
  training_goal TEXT,
  training_style TEXT,  -- polarized, norwegian, sweetspot, base, threshold
  weekly_tss_target INTEGER,
  created_at TIMESTAMPTZ,
  updated_at TIMESTAMPTZ
);
```

**weekly_plans**
```sql
CREATE TABLE weekly_plans (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id),
  week_start DATE,
  week_end DATE,
  total_tss INTEGER,
  status TEXT,  -- draft, registered, completed
  daily_workouts JSONB[],  -- Array of 7 daily workouts
  intervals_event_ids TEXT[],  -- Synced event IDs
  created_at TIMESTAMPTZ
);
```

**audit_logs**
```sql
CREATE TABLE audit_logs (
  id UUID PRIMARY KEY,
  event_type TEXT,
  user_id UUID,
  details JSONB,
  ip_address TEXT,
  created_at TIMESTAMPTZ
);
```

---

## API Endpoints

### Authentication
- `POST /api/auth/register` - 회원가입
- `POST /api/auth/login` - 로그인
- `POST /api/auth/logout` - 로그아웃
- `GET /api/auth/me` - 현재 사용자 정보

### Settings
- `GET /api/settings/api-keys` - API 키 조회
- `PUT /api/settings/api-keys` - API 키 업데이트
- `GET /api/settings/check-configured` - 설정 완료 여부
- `GET /api/settings` - 사용자 설정 조회
- `PUT /api/settings` - 사용자 설정 업데이트

### Fitness
- `GET /api/fitness` - 피트니스 데이터 (CTL/ATL/TSB)

### Workout
- `POST /api/workout/generate` - 단일 워크아웃 생성
- `POST /api/workout/register` - Intervals.icu 등록

### Weekly Plans
- `GET /api/plans/current` - 현재 주 계획 조회
- `POST /api/plans/generate` - 주간 계획 생성
- `POST /api/plans/register` - 주간 계획 Intervals.icu 등록
- `GET /api/plans/history` - 과거 계획 목록

### Admin (Requires X-Admin-Secret)
- `GET /api/admin/audit-logs` - 감사 로그 조회
- `GET /api/admin/audit-logs/stats` - 로그 통계
- `POST /api/admin/llm-models` - LLM 모델 관리

---

## Security

### Authentication
- JWT tokens (Supabase)
- HTTP-only cookies (optional)
- Token expiration: 1 hour

### API Keys
- Stored in Supabase (user_api_keys table)
- Not encrypted (consider Supabase Vault for production)
- User-specific Intervals.icu API keys

### Admin Access
- Secret header: `X-Admin-Secret`
- IP whitelist (optional)
- Audit logging for all admin actions

### CORS
- Allowed origins: Vercel domains only
- Credentials: true
- Preflight caching: 3600s

---

## Monitoring & Observability

### Logging
- **Google Cloud Logging**: 모든 백엔드 로그
- **Audit Logs**: 사용자 액션 추적
- **Request Logging**: API 호출 모니터링

### Health Checks
- `GET /api/health` - Backend health
- `GET /` - Root endpoint

### Metrics
- Response times
- Error rates
- LLM fallback frequency
- Cache hit/miss rates

---

## Best Practices

### Code Organization
```
api/          # Backend API routes
src/          # Core business logic
  clients/    # External API clients
  services/   # Business services
  data/       # Data files (workout modules)
frontend/     # React frontend
  components/ # UI components
  contexts/   # Global state
  hooks/      # Custom hooks
  pages/      # Page components
```

### Error Handling
- Try/except all external API calls
- Log errors to audit_logs
- Return user-friendly error messages
- Fallback to alternative LLM providers

### Performance
- Use React Query for all API calls
- Implement TTL-based caching
- Parallel data fetching
- Lazy load components

---

## Future Enhancements

See [Roadmap and TODOs](roadmap-and-todos.md) for detailed plans.

**High Priority:**
- API key encryption (Supabase Vault)
- Rate limiting per user
- Workout history tracking
- Push notifications

**Medium Priority:**
- Metabolic test report integration
- Custom workout builder
- Social features (share workouts)
- Mobile app (React Native)

**Low Priority:**
- AI coach chat interface
- Training plan marketplace
- Integration with other platforms (TrainingPeaks, Strava)

---

## Resources

- [Deployment Guide](../guides/deployment-guide.md)
- [Infrastructure Setup](../guides/infrastructure-setup.md)
- [Caching Strategy](../guides/caching-strategy.md)
- [API Documentation](https://cycling-coach-backend-25085100592.asia-northeast3.run.app/docs)
- [Frontend Performance](../guides/frontend-performance.md)

---

**Last Updated**: 2026-01-11  
**Maintained By**: AI Cycling Coach Team
SUPABASE_URL=
SUPABASE_SERVICE_ROLE_KEY=

# LLM API Keys
GROQ_API_KEY=
GEMINI_API_KEY=
HF_API_KEY=
OPENAI_API_KEY=

# Admin
ADMIN_SECRET=
```

### Frontend
```
VITE_SUPABASE_URL=
VITE_SUPABASE_ANON_KEY=
VITE_API_URL=
```

---

## 배포

| 서비스 | 플랫폼 | URL |
|--------|--------|-----|
| Frontend | Vercel | ai-cycling-workout-planner.vercel.app |
| Backend | Render | ai-cycling-workout-planner.onrender.com |
| Database | Supabase | - |

---

## 향후 계획

1. **Rate Limiting** - 유저당 일일 5회 제한
2. **대사 테스트 리포트** - PDF 업로드 및 분석
3. **Inscyd 연동** - 테스트 데이터 활용
4. **수익화** - Stripe 결제, 프리미엄 플랜
