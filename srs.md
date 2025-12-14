# AI 기반 사이클링 워크아웃 추천 및 자동 동기화 서비스

## 소프트웨어 요구사항 명세서 (SRS)

---

## 1. 프로젝트 개요

| 항목 | 내용 |
|------|------|
| **프로젝트명** | AI Cycling Coach |
| **목표** | 사용자 데이터를 기반으로 AI가 매일 최적의 워크아웃을 생성하여 Intervals.icu 캘린더에 등록, Wahoo Bolt2에서 즉시 실행 가능하게 함 |
| **핵심 가치** | 훈련 부하(Training Load)와 회복 상태(Wellness)를 고려한 동적 플랜 제공 및 플랫폼 간 자동화 |

---

## 2. 시스템 아키텍처

```
┌─────────────────┐     HTTP     ┌─────────────────┐     API      ┌─────────────────┐
│   React.js      │ ──────────▶  │    FastAPI      │ ──────────▶  │  Intervals.icu  │
│   (Vercel)      │              │   (Render)      │              │      API        │
└─────────────────┘              └────────┬────────┘              └─────────────────┘
                                          │
                                          ▼
                                   ┌─────────────────┐
                                   │   LLM API       │
                                   │ (Gemini/OpenAI) │
                                   └─────────────────┘
```

| 컴포넌트 | 기술 스택 |
|----------|-----------|
| **Frontend** | React.js + Vite + Tailwind CSS + shadcn/ui |
| **Backend** | Python 3.10+ / FastAPI |
| **LLM** | Gemini / OpenAI / Anthropic (선택 가능) |
| **External API** | Intervals.icu API |
| **Scheduler** | Python `schedule` 라이브러리 또는 Cron |
| **Hosting** | Vercel (Frontend) + Render (Backend) |

---

## 3. 기능 명세 (Functional Requirements)

### 3.1. 인증 및 사용자 관리

| 요구사항 | 설명 |
|----------|------|
| API Key 방식 | Intervals.icu 설정 페이지에서 발급받은 API Key를 `.env` 파일로 관리 |
| 환경변수 | `INTERVALS_API_KEY`, `ATHLETE_ID` |
| 보안 | API Key는 소스코드에 하드코딩하지 않고 환경 변수로 관리 |

### 3.2. 데이터 수집 (Data Ingestion)

| 기능 | 설명 | API 엔드포인트 |
|------|------|----------------|
| 최근 활동 조회 | 42일간 라이딩 데이터 (TSS, IF 등) | `GET /athlete/{id}/activities` |
| Wellness 조회 | 7일간 HRV, RHR, 수면 시간 | `GET /athlete/{id}/wellness` |
| 캘린더 확인 | 기존 이벤트/레이스 일정 확인 | `GET /athlete/{id}/events` |

### 3.3. AI 워크아웃 생성 (Core Logic)

**입력 데이터 (Prompt Context):**
- 사용자 프로필 (FTP, Max HR, LTHR)
- 최근 부하 데이터 (CTL, ATL, TSB)
- Wellness 데이터 (HRV, RHR, 수면)
- 장기 목표 (예: "그란폰도 대비 지구력 강화")

**처리 로직:**

| TSB 상태 | 추천 워크아웃 |
|----------|---------------|
| TSB < -20 | Recovery Ride (회복 라이딩) |
| -20 ≤ TSB ≤ 0 | Endurance / Tempo |
| TSB > 0 | Interval (VO2max / Threshold) |

**출력 형식:**
- Intervals.icu 워크아웃 빌더 텍스트 포맷 (DSL)
- 예: `10m 50%` (10분간 FTP 50%로 웜업)

### 3.4. 사용자 입력 파라미터 ✨ (신규)

| 파라미터 | CLI 옵션 | 설명 |
|----------|----------|------|
| Duration | `--duration` | 목표 운동 시간 (분) |
| Style | `--style` | 훈련 스타일 (polarized, norwegian, sweetspot 등) |
| Intensity | `--intensity` | 강도 선호 (easy, moderate, hard) |
| Notes | `--notes` | 추가 요청 (자유 텍스트) |
| Indoor | `--indoor` | 실내 트레이너 모드 |

### 3.5. Intervals.icu 캘린더 등록

| 단계 | 설명 |
|------|------|
| 워크아웃 변환 | AI 생성 텍스트 → Event 객체로 변환 |
| 등록 실행 | `POST /athlete/{id}/events` 호출 |
| Wahoo 동기화 | Intervals.icu 등록 완료 시 Wahoo Cloud가 자동 동기화 |

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