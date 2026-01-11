# AI Cycling Coach - Work Log

## 2025-12-21 (토요일)

### 🎯 오늘 완료한 작업

#### 1. 멀티 LLM 프로바이더 시스템 구현
- **Groq 프로바이더 추가**
  - OpenAI 호환 API 사용
  - 기본 모델: `llama-3.3-70b-versatile`
- **HuggingFace 프로바이더 추가**
  - Serverless Inference API 사용
  - 기본 모델: `mistralai/Mistral-7B-Instruct-v0.3`
- **자동 폴백 라우팅**
  - 쿼타 초과(429) 감지 시 다음 프로바이더로 자동 전환
  - 우선순위: Groq → Gemini → HuggingFace → OpenAI

#### 2. DB 기반 LLM 모델 관리
- `llm_models` 테이블 설계
- 환경변수 대신 DB에서 모델 설정 로드
- 관리자 API로 런타임 모델 변경 가능

#### 3. Audit 로깅 시스템
- `audit_logs` 테이블 생성
- `audit_service.py` - 이벤트 로깅 함수
- 관리자 API로 로그 조회/통계/정리

#### 4. 관리자 API 구현
- `/api/admin/audit-logs` - 로그 조회
- `/api/admin/llm-models` - 모델 CRUD
- `X-Admin-Secret` 헤더 인증

#### 5. 랜딩 페이지 구현
- 마케팅 콘텐츠 작성
- 3단계 동작 설명, 핵심 장점, 타겟 사용자

#### 6. 피드백 시스템
- Google Forms 연동
- 헤더에 피드백 링크 추가

---

### 📁 수정된 파일

| 파일 | 변경 내용 |
|------|----------|
| `src/clients/llm.py` | GroqClient, HuggingFaceClient, FallbackLLMClient 추가 |
| `api/services/model_service.py` | DB에서 모델 로드 |
| `api/services/audit_service.py` | Audit 로깅 |
| `api/services/user_api_service.py` | FallbackLLMClient 사용 |
| `api/routers/admin.py` | 관리자 API 엔드포인트 |
| `api/main.py` | admin 라우터 등록 |
| `frontend/src/pages/LandingPage.tsx` | 랜딩 페이지 |
| `frontend/src/App.tsx` | 랜딩 페이지 연동, 피드백 링크 |
| `TODO.md` | 완료 항목 업데이트 |

---

### 🗄️ 새 Supabase 테이블

1. **audit_logs** - 이벤트 로그
2. **llm_models** - LLM 모델 설정

---

### 📌 다음 작업

- [ ] 유저당 일일 워크아웃 생성 Rate Limit (5회/일)
- [ ] 대사 테스트/Inscyd 리포트 업로드

---

## 이전 기록

*(이전 작업 로그 추가 예정)*
