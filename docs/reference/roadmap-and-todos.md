# Roadmap and TODOs

> **Last Updated**: 2026-01-11  
> **Project Status**: Production (v1.2)

---

## ✅ Completed Features

### Phase 1-7: Core Platform (2025-Q4)
- [x] FastAPI 백엔드 구현
- [x] React 프론트엔드 구현
- [x] AI 워크아웃 생성 (Multi-LLM)
- [x] Intervals.icu 연동
- [x] Vercel + Google Cloud Run 배포

### Phase 8: Multi-User System (2025-12)
- [x] Supabase Auth 통합
- [x] Google OAuth + Email/Password 로그인
- [x] 사용자별 설정 관리
- [x] Landing Page 구현

### Phase 9: API Key Management (2025-12)
- [x] 사용자별 Intervals.icu API 키 저장
- [x] Settings 페이지 UI
- [x] API 키 검증 로직
- [x] 서버 측 LLM API 키 관리

### Phase 10: Multi-LLM & Fallback (2025-12)
- [x] Vercel AI Gateway 통합
- [x] Groq (Llama 3.3 70B) 프라이머리
- [x] Google Gemini 2.0/1.5 Flash 폴백
- [x] 자동 쿼터 초과 감지 및 전환
- [x] Admin API (LLM 모델 관리)

### Phase 11: System Management (2025-12)
- [x] Audit 로깅 시스템
- [x] Request logging middleware
- [x] Admin API 엔드포인트
- [x] Google Forms 피드백 연동

### Phase 12: Weekly Planning (2026-01)
- [x] 주간 훈련 계획 자동 생성
- [x] 7일 워크아웃 일괄 생성
- [x] TSS 기반 일일 부하 분배
- [x] Intervals.icu 캘린더 일괄 등록
- [x] Weekly Plan UI 컴포넌트

### Phase 13: Performance Optimization (2026-01)
- [x] React Query 통합
- [x] 병렬 데이터 페칭 (3.5s → 1.8s)
- [x] TTL 기반 백엔드 캐싱
- [x] Cache invalidation 전략
- [x] Frontend lazy loading

### Phase 14: Version Management (2026-01)
- [x] 버전 업데이트 알림 모달
- [x] Semantic versioning
- [x] localStorage 기반 버전 추적
- [x] Release notes UI

---

## 📋 In Progress

### Phase 15: Security Hardening
- [ ] API 키 암호화 (Supabase Vault)
- [ ] Rate limiting per user (5 workouts/day)
- [ ] CSRF protection
- [ ] IP-based access control for admin

---

## 🎯 Planned Features

### Phase 16: UX Improvements (2026-Q1)
- [ ] Onboarding flow 개선
- [ ] Interactive tutorial
- [ ] API 키 유효성 실시간 검증
- [ ] Error boundary 및 에러 핸들링 강화
- [ ] Loading skeleton UI

**Priority**: High  
**Estimated Effort**: 2 weeks

---

### Phase 17: Workout History (2026-Q1)
- [ ] 과거 생성된 워크아웃 히스토리 저장
- [ ] 워크아웃 재사용 기능
- [ ] 즐겨찾기 워크아웃
- [ ] 워크아웃 검색 및 필터링
- [ ] 통계 대시보드 (생성 횟수, 평균 TSS 등)

**Database Schema:**
```sql
CREATE TABLE workout_history (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id),
  workout_data JSONB,
  training_style TEXT,
  target_duration INTEGER,
  actual_tss INTEGER,
  generated_at TIMESTAMPTZ,
  registered_at TIMESTAMPTZ,
  intervals_event_id TEXT,
  is_favorite BOOLEAN DEFAULT false
);
```

**Priority**: High  
**Estimated Effort**: 1 week

---

### Phase 18: Advanced Analytics (2026-Q2)

**Features:**
- [ ] 훈련 부하 트렌드 차트 (CTL/ATL/TSB 히스토리)
- [ ] 주간/월간 TSS 요약
- [ ] Power Curve 분석 (Intervals.icu API 연동)
- [ ] Fitness level progression
- [ ] Training load heatmap

**UI Components:**
- Line charts (CTL/ATL/TSB over time)
- Bar charts (Weekly TSS distribution)
- Heatmap calendar (Training intensity)
- Power duration curve

**Priority**: Medium  
**Estimated Effort**: 2 weeks

---

### Phase 19: Metabolic Testing Integration (2026-Q2)

**Goal**: 대사 테스트 리포트를 업로드하여 더 정확한 훈련 존 설정

**Features:**
- [ ] Inscyd 리포트 파일 업로드 (.pdf, .csv)
- [ ] FTP, VO2max, VLamax 자동 파싱
- [ ] 개인화된 파워/심박존 자동 설정
- [ ] 테스트 히스토리 관리
- [ ] 존 변화 추이 분석

**Database Schema:**
```sql
CREATE TABLE metabolic_tests (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id),
  test_date DATE,
  test_type TEXT,  -- 'inscyd', 'ramp', 'lactate'
  ftp INTEGER,
  vo2max FLOAT,
  vlamax FLOAT,
  zones JSONB,  -- Power zones
  file_url TEXT,
  created_at TIMESTAMPTZ
);
```

**Priority**: Medium  
**Estimated Effort**: 3 weeks

---

### Phase 20: Social Features (2026-Q3)

**Features:**
- [ ] 워크아웃 공유 (링크 생성)
- [ ] 공개 워크아웃 갤러리
- [ ] 다른 사용자 워크아웃 복사
- [ ] 코칭 기능 (코치가 선수에게 워크아웃 할당)
- [ ] 팀 훈련 계획

**Priority**: Low  
**Estimated Effort**: 4 weeks

---

### Phase 21: Mobile App (2026-Q3)

**Technology:**
- React Native + Expo
- Shared API with web app
- Push notifications
- Offline support

**Features:**
- [ ] 모바일 로그인
- [ ] 워크아웃 생성
- [ ] 주간 계획 조회
- [ ] Intervals.icu 동기화
- [ ] Push 알림 (워크아웃 시작 전)

**Priority**: Low  
**Estimated Effort**: 6 weeks

---

### Phase 22: Monetization (2026-Q4)

**Pricing Tiers:**
| Tier | Price | Features |
|------|-------|----------|
| **Free** | $0/month | 5 workouts/day, Basic styles |
| **Pro** | $9/month | Unlimited workouts, All styles, Priority support |
| **Coach** | $29/month | Pro + Team management, Custom modules |

**Implementation:**
- [ ] Stripe 결제 연동
- [ ] Subscription 관리
- [ ] Usage tracking
- [ ] Billing dashboard

**Priority**: Low  
**Estimated Effort**: 3 weeks

---

## 🔧 Technical Improvements

### Backend
- [ ] 워크아웃 생성 성능 최적화 (현재 10s → 목표 5s)
- [ ] Redis 캐싱 도입 (현재 in-memory)
- [ ] Database query 최적화
- [ ] Background job queue (Celery)
- [ ] Webhook system (Intervals.icu → Backend)

### Frontend
- [ ] Code splitting 최적화
- [ ] Image optimization (WebP)
- [ ] PWA 지원
- [ ] Service worker (offline support)
- [ ] i18n (English support)

### DevOps
- [ ] Automated testing (Pytest + Jest)
- [ ] E2E testing (Playwright)
- [ ] Performance monitoring (Sentry)
- [ ] Uptime monitoring
- [ ] Cost optimization

---

## 🐛 Known Issues

### Critical
- None

### High Priority
- [ ] LLM 응답 파싱 에러 핸들링 개선
- [ ] 주간 계획 생성 시 가끔 타임아웃 발생 (60초 초과)

### Medium Priority
- [ ] Settings 페이지에서 API 키 변경 시 캐시 무효화 안 됨
- [ ] Weekly Plan UI에서 과거 주 데이터 조회 불가

### Low Priority
- [ ] 모바일 Safari에서 차트 렌더링 느림
- [ ] Dark mode 일부 컴포넌트 스타일 깨짐

---

## 📊 Metrics & Goals

### Current Status (2026-01-11)
- **Active Users**: ~50
- **Daily Workouts Generated**: ~100
- **Average Response Time**: 1.8s (cached), 10s (uncached)
- **Uptime**: 99.9%
- **Error Rate**: 0.5%

### 2026 Q1 Goals
- **Active Users**: 200
- **Daily Workouts**: 500
- **Response Time**: 1.5s (cached), 7s (uncached)
- **Uptime**: 99.95%
- **Error Rate**: 0.3%

### 2026 Q2 Goals
- **Active Users**: 1000
- **Daily Workouts**: 3000
- **Paid Conversions**: 5%
- **Monthly Revenue**: $450

---

## 🔗 References

- [System Architecture](system-architecture.md)
- [Requirements Specification](requirements-specification.md)
- [Deployment Guide](../guides/deployment-guide.md)
- [API Documentation](https://cycling-coach-backend-25085100592.asia-northeast3.run.app/docs)

---

**Maintained By**: AI Cycling Coach Team  
**Last Review**: 2026-01-11

