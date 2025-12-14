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

---

## 📋 남은 작업

### Phase 9: 사용자별 API 연동
- [ ] 설정 페이지에서 입력한 API 키로 Intervals.icu 연동
- [ ] 설정 페이지에서 입력한 LLM API 키로 워크아웃 생성
- [ ] Backend에서 사용자별 API 키 조회 로직 구현
- [ ] API 키 암호화 저장 (Supabase Vault 또는 AES)

### Phase 10: UX 개선
- [ ] 온보딩 플로우 (첫 로그인 시 API 키 설정 안내)
- [ ] API 키 유효성 검증
- [ ] 에러 핸들링 개선

### Phase 11: 추가 기능 (선택)
- [ ] 워크아웃 히스토리 저장
- [ ] 주간 플래너
- [ ] 푸시 알림

---

## 배포 정보

| 서비스 | URL |
|--------|-----|
| Frontend | https://ai-cycling-workout-planner.vercel.app |
| Backend | https://ai-cycling-workout-planner.onrender.com |
