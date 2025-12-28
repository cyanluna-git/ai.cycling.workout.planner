# AI Cycling Coach - TODO

## ✅ 완료된 작업

### Phase 1-7: 코어 기능
- [x] FastAPI 백엔드 구현
- [x] React 프론트엔드 구현
- [x] AI 워크아웃 생성 (Gemini/OpenAI/Anthropic)
- [x] Intervals.icu 연동
- [x] Vercel + Render 분리 배포

### Phase 8: 멀티유저 인증
- [x] Supabase 설정
- [x] Google OAuth 연동
- [x] 이메일/비밀번호 로그인
- [x] 로그인/회원가입 UI
- [x] 설정 페이지 UI

### Phase 9: 사용자별 API 연동
- [x] 설정 페이지에서 입력한 API 키로 Intervals.icu 연동
- [x] Backend에서 사용자별 API 키 조회 로직 구현
- [x] LLM API 키 서버 관리 (사용자 입력 불필요)

### Phase 10: 멀티 LLM 프로바이더
- [x] Groq 프로바이더 추가 (Llama 3.3)
- [x] HuggingFace 프로바이더 추가
- [x] 쿼타 초과 시 자동 폴백 라우팅
- [x] DB 기반 모델 관리 (llm_models 테이블)
- [x] 관리자 API (모델 CRUD)

### Phase 11: 시스템 관리
- [x] Audit 로깅 시스템
- [x] 관리자 API 엔드포인트
- [x] 랜딩 페이지
- [x] 피드백 폼 (Google Forms)

---

## 📋 남은 작업

### Phase 12: 보안 & 제한
- [ ] API 키 암호화 저장 (Supabase Vault 또는 AES)
- [ ] **유저당 일일 워크아웃 생성 Rate Limit (5회/일)**
- [ ] 유료 플랜 시 제한 해제

### Phase 13: UX 개선
- [ ] 온보딩 플로우 개선
- [ ] API 키 유효성 검증
- [ ] 에러 핸들링 개선

### Phase 14: 추가 기능
- [ ] 워크아웃 히스토리 저장
- [ ] 주간 훈련 플래너
- [ ] 푸시 알림
- [ ] **대사 테스트 리포트 업로드 및 히스토리화**
- [ ] **Inscyd 테스트 리포트 업로드 및 분석 연동**

### Phase 15: 수익화 (선택)
- [ ] Stripe 결제 연동
- [ ] 프리미엄 플랜 기능

---

## 🔧 기존 기능 개선 (Intervals.icu API 활용)

### Workout 업로드 고도화
- [ ] `/api/v1/athlete/{id}/workouts/bulk` 활용한 대량 업로드
- [ ] `.fit`, `.mrc`, `.erg` 포맷 다운로드 지원

### Sport Settings 동기화
- [ ] `/api/v1/athlete/{athleteId}/sport-settings/{id}` - FTP, 파워존, HR존 자동 동기화
- [ ] 운동 생성 시 사용자의 실제 존 설정 반영

### 실시간 피트니스 동기화
- [ ] webhook/polling으로 자동 동기화 구현

---

## 🚀 신규 기능 계획 (Intervals.icu API 활용)

### Phase 16: Wellness 데이터 통합

**목적**
사용자의 일일 건강 상태를 추적하고 컨디션에 맞는 맞춤형 운동을 제안

**베네핏**
- 과훈련 방지 및 부상 리스크 감소
- HRV, 수면 품질 기반 회복 상태 파악
- 개인화된 운동 강도 자동 조절로 최적의 훈련 효과

**구현 방향**
- [ ] `/api/v1/athlete/{id}/wellness` API 연동
- [ ] 대시보드에 웰니스 지표 표시 (수면, HRV, 체중, 스트레스, 피로도)
- [ ] 웰니스 점수 기반 운동 강도 자동 조절 로직
- [ ] 컨디션 불량 시 회복 운동 또는 휴식 권장 알림

---

### Phase 17: Power Curve / Fitness 분석 대시보드

**목적**
선수의 피트니스 수준과 훈련 부하를 시각적으로 분석하여 훈련 상태 파악

**베네핏**
- MMP 커브로 현재 체력 수준과 약점 파악
- CTL/ATL/TSB 추적으로 피크 컨디션 타이밍 예측
- 과훈련 징후 조기 발견

**구현 방향**
- [ ] `/api/v1/athlete/{id}/power-curves` - MMP(Maximum Mean Power) 커브 시각화
- [ ] `/api/v1/athlete/{id}/hr-curves` - 심박수 커브 표시
- [ ] CTL(Chronic Training Load) / ATL(Acute Training Load) / TSB(Training Stress Balance) 차트
- [ ] 피트니스 트렌드 분석 및 예측 그래프
- [ ] 목표 이벤트까지의 피크 컨디션 시뮬레이션

---

### Phase 18: 훈련 계획 관리 (Training Plans)

**목적**
AI가 생성한 개별 운동을 체계적인 훈련 블록으로 구성하여 장기 훈련 관리

**베네핏**
- 주기화 훈련(Periodization) 지원
- 목표 레이스/이벤트 기반 역산 계획
- 훈련 일관성 및 연속성 향상

**구현 방향**
- [ ] `/api/v1/athlete/{id}/folders` - 훈련 계획 폴더 생성/관리 연동
- [ ] `/api/v1/athlete/{id}/training-plan` - 훈련 블록 적용 기능
- [ ] AI 생성 운동을 주간/월간 계획으로 묶어서 일괄 적용
- [ ] 훈련 계획 템플릿 (베이스, 빌드, 피크, 테이퍼)
- [ ] 계획 진행률 및 준수율 트래킹

---

### Phase 19: Activity 분석 강화

**목적**
완료된 운동을 상세 분석하여 목표 대비 수행도를 평가하고 개선점 도출

**베네핏**
- 계획한 운동 vs 실제 수행 비교로 정확한 피드백
- 인터벌 품질 분석으로 훈련 효과 극대화
- 장기적인 성과 추적 및 성장 지표 확인

**구현 방향**
- [ ] `/api/v1/activity/{id}/intervals` - 인터벌별 상세 분석 표시
- [ ] `/api/v1/activity/{id}/power-curve` - 활동별 파워 커브 시각화
- [ ] 운동 목표(계획) vs 실제 수행 비교 분석 리포트
- [ ] 인터벌 준수율, 파워 타겟 적중률 등 KPI 계산
- [ ] 과거 동일 운동과의 성과 비교

---

## 배포 정보

| 서비스 | URL |
|--------|-----|
| Frontend | https://ai-cycling-workout-planner.vercel.app |
| Backend | https://ai-cycling-workout-planner.onrender.com |

## 환경변수 (Backend)

| 변수 | 설명 |
|------|------|
| `SUPABASE_URL` | Supabase 프로젝트 URL |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase 서비스 키 |
| `GROQ_API_KEY` | Groq API 키 |
| `GEMINI_API_KEY` | Google Gemini API 키 |
| `HF_API_KEY` | HuggingFace API 키 |
| `OPENAI_API_KEY` | OpenAI API 키 (선택) |
| `ADMIN_SECRET` | 관리자 API 인증 키 |

