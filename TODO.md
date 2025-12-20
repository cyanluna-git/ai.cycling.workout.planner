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

