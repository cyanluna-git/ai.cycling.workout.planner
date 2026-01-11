# Software Requirements Specification (SRS)

> **Last Updated**: 2026-01-11  
> **Version**: 2.0  
> **Status**: Production

---

## 1. Project Overview

| 항목 | 내용 |
|------|------|
| **Project Name** | AI Cycling Coach |
| **목표** | AI 기반 맞춤형 사이클링 훈련 계획 자동 생성 및 Intervals.icu 동기화 시스템 |
| **핵심 가치** | 1) 개인화된 AI 워크아웃 생성<br>2) 주간 훈련 계획 자동화<br>3) 훈련 부하(TSS) 기반 스마트 관리<br>4) Wahoo/Garmin 장치 자동 동기화 |
| **사용자** | 사이클링 훈련을 체계적으로 관리하려는 라이더 (입문~고급) |

---

## 2. System Architecture

```
┌─────────────────┐     HTTPS    ┌─────────────────┐     API      ┌─────────────────┐
│   React.js      │ ──────────▶  │    FastAPI      │ ──────────▶  │  Intervals.icu  │
│   (Vercel)      │              │  (Cloud Run)    │              │      API        │
└─────────────────┘              └────────┬────────┘              └─────────────────┘
                                          │
                                          ▼
                                   ┌─────────────────┐
                                   │  Vercel AI      │
                                   │  Gateway        │
                                   └─────────────────┘
```

| Component | Technology |
|----------|-----------|
| **Frontend** | React 18 + TypeScript + Vite + Tailwind CSS + shadcn/ui |
| **Backend** | Python 3.11 + FastAPI |
| **Database** | Supabase (PostgreSQL) |
| **Authentication** | Supabase Auth (Google OAuth + Email) |
| **AI Gateway** | Vercel AI Gateway (Groq, Gemini) |
| **External API** | Intervals.icu API |
| **Hosting** | Vercel (Frontend) + Google Cloud Run (Backend) |

---

## 3. Functional Requirements

### 3.1. User Authentication & Authorization

| Requirement | Description |
|----------|------|
| **FR-1.1** | 사용자는 Google OAuth로 로그인할 수 있어야 한다 |
| **FR-1.2** | 사용자는 이메일/비밀번호로 회원가입 및 로그인할 수 있어야 한다 |
| **FR-1.3** | 로그인 후 JWT 토큰을 발급받아 API 요청에 사용해야 한다 |
| **FR-1.4** | 토큰 만료 시 자동 로그아웃 처리되어야 한다 |

**구현:**
- Supabase Auth
- JWT 기반 인증
- React Context API로 전역 상태 관리

---

### 3.2. User Settings Management

| Requirement | Description |
|----------|------|
| **FR-2.1** | 사용자는 Intervals.icu API 키와 Athlete ID를 등록할 수 있어야 한다 |
| **FR-2.2** | 사용자는 FTP, Max HR, LTHR을 설정할 수 있어야 한다 |
| **FR-2.3** | 사용자는 훈련 목표(Training Goal)를 텍스트로 입력할 수 있어야 한다 |
| **FR-2.4** | 사용자는 선호하는 훈련 스타일을 선택할 수 있어야 한다 (Polarized, Norwegian, Sweet Spot, Base, Threshold) |
| **FR-2.5** | 사용자는 주간 목표 TSS를 설정할 수 있어야 한다 (예: 500 TSS/week) |

**구현:**
- Settings Page UI
- `PUT /api/settings` API
- Supabase `user_settings` 테이블

---

### 3.3. Fitness Data Integration

| Requirement | Description |
|----------|------|
| **FR-3.1** | 시스템은 Intervals.icu에서 최근 42일 훈련 데이터를 조회해야 한다 |
| **FR-3.2** | 시스템은 현재 CTL, ATL, TSB 값을 계산하여 표시해야 한다 |
| **FR-3.3** | 시스템은 최근 7일 Wellness 데이터(HRV, RHR, 수면)를 조회해야 한다 |
| **FR-3.4** | 피트니스 데이터는 2시간 캐싱되어야 한다 (TTL: 2h) |

**구현:**
- `GET /api/fitness` API
- Intervals.icu API 연동
- TTL 기반 캐싱

---

### 3.4. AI Workout Generation

| Requirement | Description |
|----------|------|
| **FR-4.1** | 사용자는 훈련 스타일, 시간, 난이도를 입력하여 워크아웃을 생성할 수 있어야 한다 |
| **FR-4.2** | 시스템은 사용자의 현재 TSB 상태를 고려하여 적절한 강도를 추천해야 한다 |
| **FR-4.3** | 생성된 워크아웃은 WARMUP → MAIN → COOLDOWN 구조여야 한다 |
| **FR-4.4** | 워크아웃 생성 시간은 10초 이내여야 한다 |
| **FR-4.5** | LLM 쿼터 초과 시 자동으로 다른 프로바이더로 전환되어야 한다 |

**구현:**
- `POST /api/workout/generate` API
- Modular workout system
- Vercel AI Gateway (Groq → Gemini fallback)

**Workout Structure:**
```json
{
  "warmup": ["10m @ 50%", "5m @ 60%"],
  "main": ["8m @ 95%", "2m @ 50%", "8m @ 95%"],
  "cooldown": ["10m @ 50%"]
}
```

**TSB-based Intensity Guidelines:**
| TSB Range | Recommended Intensity |
|-----------|----------------------|
| TSB < -20 | Recovery only (50-65%) |
| -20 ≤ TSB ≤ -10 | Endurance/Tempo (65-85%) |
| -10 < TSB ≤ 0 | Sweet Spot (85-93%) |
| TSB > 0 | Threshold/VO2max (95-110%) |

---

### 3.5. Weekly Plan Generation

| Requirement | Description |
|----------|------|
| **FR-5.1** | 사용자는 다음 주 월~일 7일 훈련 계획을 자동 생성할 수 있어야 한다 |
| **FR-5.2** | 주간 총 TSS는 사용자가 설정한 weekly_tss_target을 기준으로 해야 한다 |
| **FR-5.3** | 일일 TSS 분배는 High-Medium-High-Recovery-High-Medium-Recovery 패턴을 따라야 한다 |
| **FR-5.4** | 생성된 계획은 Intervals.icu 캘린더에 일괄 등록할 수 있어야 한다 |
| **FR-5.5** | 주간 계획 생성 시간은 60초 이내여야 한다 (7개 워크아웃 생성) |

**구현:**
- `POST /api/plans/generate` API
- `weekly_plan_service.py`
- Daily TSS distribution: [18%, 12%, 16%, 10%, 18%, 14%, 12%]

**Weekly Plan Schema:**
```json
{
  "week_start": "2026-01-13",
  "week_end": "2026-01-19",
  "total_tss": 500,
  "daily_workouts": [
    {
      "date": "2026-01-13",
      "day": "Monday",
      "target_tss": 90,
      "workout": {...}
    },
    ...
  ]
}
```

---

### 3.6. Intervals.icu Integration

| Requirement | Description |
|----------|------|
| **FR-6.1** | 생성된 워크아웃은 ZWO 형식으로 Intervals.icu에 업로드되어야 한다 |
| **FR-6.2** | 업로드된 워크아웃은 Wahoo/Garmin 장치와 자동 동기화되어야 한다 |
| **FR-6.3** | 업로드 실패 시 사용자에게 명확한 에러 메시지를 표시해야 한다 |
| **FR-6.4** | 주간 계획 등록 시 이미 등록된 워크아웃은 건너뛰어야 한다 |

**구현:**
- `POST /api/workout/register` API
- `POST /api/v1/athlete/{id}/events` (Intervals.icu)
- ZWO 형식 변환

---

### 3.7. Caching & Performance

| Requirement | Description |
|----------|------|
| **FR-7.1** | 백엔드는 데이터 유형별 TTL 캐싱을 구현해야 한다 |
| **FR-7.2** | 프론트엔드는 React Query로 API 응답을 캐싱해야 한다 |
| **FR-7.3** | 초기 로딩 시간은 2초 이내여야 한다 (캐시 히트 시) |
| **FR-7.4** | 워크아웃 생성 후 관련 캐시는 무효화되어야 한다 |

**Cache TTL:**
- Wellness: 1h
- Fitness: 2h
- Calendar: 2h
- Activities: 3h
- Profile: 6h

---

## 4. REST API 명세 ✨ (신규)

FastAPI 백엔드 엔드포인트:

| Method | Endpoint | 설명 |
|--------|----------|------|
| `GET` | `/api/health` | 헬스 체크 |
| `GET` | `/api/fitness` | CTL/ATL/TSB + Wellness 조회 |
| `GET` | `/api/activities` | 최근 활동 목록 |
| `POST` | `/api/workout/generate` | AI 워크아웃 생성 |
| `POST` | `/api/workout/create` | Intervals.icu에 등록 |

---

## 5. AI 프롬프트 설계

### 5.1. System Prompt 전략

```
Role: 당신은 엘리트 사이클링 코치입니다.
Context: 선수의 FTP는 {ftp}W입니다. TSB는 {tsb}로 {form_status} 상태입니다.
Constraint:
- Intervals.icu workout text syntax를 엄격히 준수할 것
- 총 시간은 {max_duration}분을 넘지 말 것
- JSON 형식으로 출력할 것
Task: 오늘의 워크아웃을 생성하세요.
```

### 5.2. 프롬프트 아키텍처 ✨ (신규)

| 프롬프트 | 특성 | 설명 |
|----------|------|------|
| System Prompt | 고정 | AI 역할, 출력 규칙, JSON 스키마 |
| User Prompt | 동적 | 실시간 데이터 (CTL/ATL/TSB, CLI 인자) |

> **핵심 원칙**: 프롬프트 생성에 AI를 사용하지 않음. Python 코드로 조합.

### 5.3. 유효성 검사

| 검사 항목 | 방법 |
|-----------|------|
| 문법 검증 | 정규식으로 시간+파워 형식 확인 |
| 강도 제한 | Zone 5는 최대 5분, FTP 200% 초과 금지 |
| 파싱 확인 | Intervals.icu 섹션 헤더 필수 (Warmup, Main Set, Cooldown) |

---

## 6. 비기능 요구사항

### 6.1. 에러 처리

| 상황 | 처리 방법 |
|------|-----------|
| API Rate Limit (429) | Exponential Backoff 재시도 |
| 중복 등록 방지 | 해당 날짜 이벤트 조회 후 없을 때만 생성 |
| LLM 오류 | Fallback 텍스트 파싱 로직 |

### 6.2. 보안

- API 키는 환경 변수로만 관리
- CORS 설정으로 허용 도메인 제한
- 프론트엔드에 API 키 노출 금지

---

## 7. 배포 환경 ✨ (신규)

| 서비스 | 호스팅 | URL |
|--------|--------|-----|
| Frontend | Vercel | https://ai-cycling-workout-planner.vercel.app |
| Backend | Render | https://ai-cycling-workout-planner.onrender.com |

---

## 8. 개발 로드맵

| Phase | 내용 | 상태 |
|-------|------|------|
| Phase 1 | API 래퍼 (IntervalsClient) 구현 | ✅ 완료 |
| Phase 2 | 데이터 전처리 (CTL/ATL/TSB 계산) | ✅ 완료 |
| Phase 3 | AI 프롬프트 엔지니어링 | ✅ 완료 |
| Phase 4 | 메인 로직 및 스케줄러 | ✅ 완료 |
| Phase 5 | 사용자 입력 파라미터 | ✅ 완료 |
| Phase 6 | React 프론트엔드 | ✅ 완료 |
| Phase 7 | 분리 배포 (Vercel + Render) | ✅ 완료 |

---

## 9. 참고 자료

- [Intervals.icu API 문서](https://intervals.icu/api-docs.html)
- [프롬프트 아키텍처 문서](docs/prompt_architecture.md)
- [배포 가이드](docs/deployment_guide.md)