# AI Cycling Coach - Architecture & Design Notes

## 개요

AI Cycling Coach는 Intervals.icu 훈련 데이터를 기반으로 개인화된 사이클링 워크아웃을 자동 생성하고, 사이클링 컴퓨터(Wahoo, Garmin)로 직접 전송하는 서비스입니다.

---

## 시스템 아키텍처

```
┌─────────────────────────────────────────────────────────────────────┐
│                           Frontend (Vercel)                          │
│                                                                      │
│   React + TypeScript + Vite + Tailwind CSS + shadcn/ui              │
│   ├── LandingPage     (마케팅)                                       │
│   ├── AuthPage        (로그인/회원가입)                               │
│   ├── OnboardingPage  (초기 설정)                                    │
│   └── Dashboard       (메인 앱)                                      │
│       ├── FitnessCard          (체력 상태)                           │
│       ├── WorkoutForm          (워크아웃 생성)                        │
│       ├── WorkoutPreview       (결과 미리보기)                        │
│       └── WeeklyCalendarCard   (주간 일정)                           │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ REST API
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                           Backend (Render)                           │
│                                                                      │
│   FastAPI + Python                                                  │
│   ├── /api/auth/*        (인증)                                      │
│   ├── /api/settings/*    (사용자 설정)                               │
│   ├── /api/fitness       (체력 데이터)                               │
│   ├── /api/workout/*     (워크아웃 생성)                              │
│   └── /api/admin/*       (관리자 API)                                │
└─────────────────────────────────────────────────────────────────────┘
                        │                    │
                        ▼                    ▼
            ┌──────────────────┐  ┌───────────────────────┐
            │    Supabase      │  │   LLM Providers       │
            │                  │  │                       │
            │  - auth.users    │  │  - Groq (Llama 3.3)   │
            │  - user_api_keys │  │  - Gemini             │
            │  - user_settings │  │  - HuggingFace        │
            │  - audit_logs    │  │  - OpenAI             │
            │  - llm_models    │  │                       │
            └──────────────────┘  └───────────────────────┘
                                             │
                                             ▼
                                  ┌───────────────────────┐
                                  │    Intervals.icu     │
                                  │                       │
                                  │  - 훈련 데이터 조회    │
                                  │  - 워크아웃 동기화     │
                                  └───────────────────────┘
```

---

## 핵심 기능

### 1. AI 워크아웃 생성

**흐름:**
1. 사용자가 워크아웃 유형/시간/목표 입력
2. Intervals.icu에서 최근 훈련 데이터 조회
3. 사용자 프로필(FTP, HR) + 훈련 상태 기반으로 프롬프트 생성
4. LLM이 MRC 형식 워크아웃 생성
5. 워크아웃 유효성 검증
6. Intervals.icu로 자동 동기화

**구현 파일:**
- `src/services/workout_generator.py` - 워크아웃 생성 로직
- `src/prompts/workout_prompt.py` - LLM 프롬프트
- `api/routers/workout.py` - API 엔드포인트

---

### 2. 멀티 LLM 폴백 시스템

**설계 원칙:**
- 단일 프로바이더 의존성 제거
- 무료 티어 한도 초과 시 자동 전환
- 런타임에 모델 변경 가능 (재배포 불필요)

**폴백 순서:**
```
1. Groq (llama-3.3-70b-versatile) - 가장 빠름
       ↓ 쿼타 초과 시
2. Gemini (gemini-1.5-flash-latest) - 안정적
       ↓ 쿼타 초과 시
3. HuggingFace (Mistral-7B) - 무료
       ↓ 쿼타 초과 시
4. OpenAI (gpt-4o-mini) - 최후 보루
```

**구현 파일:**
- `src/clients/llm.py` - LLM 클라이언트들
  - `OpenAIClient`
  - `AnthropicClient`
  - `GeminiClient`
  - `GroqClient`
  - `HuggingFaceClient`
  - `FallbackLLMClient` - 폴백 로직
- `api/services/model_service.py` - DB에서 모델 설정 로드
- `api/services/user_api_service.py` - 클라이언트 팩토리

**쿼타 에러 감지:**
```python
QUOTA_ERROR_PATTERNS = [
    "quota", "rate limit", "exceeded", "429",
    "too many requests", "resource exhausted"
]
```

---

### 3. DB 기반 모델 관리

**llm_models 테이블:**
```sql
CREATE TABLE llm_models (
    id UUID PRIMARY KEY,
    provider TEXT,      -- groq, gemini, huggingface, openai
    model_id TEXT,      -- llama-3.3-70b-versatile
    display_name TEXT,
    is_active BOOLEAN,
    priority INT,       -- 높을수록 먼저 시도
    created_at TIMESTAMPTZ
);
```

**장점:**
- 재배포 없이 모델 추가/제거
- A/B 테스트 가능
- 문제 모델 즉시 비활성화

---

### 4. 인증 시스템

**방식:** Supabase Auth + JWT

**지원 방법:**
- Google OAuth
- 이메일/비밀번호

**흐름:**
```
Frontend                 Backend                 Supabase
   │                        │                        │
   │── Login Request ──────>│                        │
   │                        │── Verify Token ───────>│
   │                        │<── User Info ─────────│
   │<── JWT Token ─────────│                        │
```

---

### 5. Audit 로깅

**audit_logs 테이블:**
```sql
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY,
    event_type TEXT,    -- user.login, workout.generated, llm.error
    user_id UUID,
    details JSONB,
    ip_address TEXT,
    created_at TIMESTAMPTZ
);
```

**이벤트 유형:**
- `user.login/logout/signup`
- `workout.generated/sync_success/sync_failed`
- `llm.request/fallback/error`
- `api_keys.updated`
- `settings.updated`

---

### 6. 관리자 API

**인증:** `X-Admin-Secret` 헤더

**엔드포인트:**
| Method | Path | 설명 |
|--------|------|------|
| GET | `/api/admin/audit-logs` | 로그 조회 |
| GET | `/api/admin/audit-logs/stats` | 통계 |
| DELETE | `/api/admin/audit-logs/cleanup` | 오래된 로그 삭제 |
| GET | `/api/admin/llm-models` | 모델 목록 |
| POST | `/api/admin/llm-models` | 모델 추가 |
| PUT | `/api/admin/llm-models/{id}` | 모델 수정 |
| DELETE | `/api/admin/llm-models/{id}` | 모델 삭제 |
| PATCH | `/api/admin/llm-models/{id}/toggle` | 활성화 토글 |

---

## 환경변수

### Backend
```
# Supabase
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
