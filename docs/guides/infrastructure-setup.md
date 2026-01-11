# AI Cycling Coach - 인프라 및 운영 가이드

본 문서는 Render에서 Google Cloud Platform(GCP)으로 마이그레이션된 현재의 백엔드 인프라 구조와 관련 링크를 정리합니다.

---

## 🏗 인프라 구조 (Infrastructure)

### 1. 백엔드 (Backend)
- **서비스**: Google Cloud Run
- **리전**: `asia-northeast3` (서울)
- **상태**: `min-instances=1` 설정으로 콜드 스타트 방지 (항상 빠른 응답)
- **URL**: `https://cycling-coach-backend-25085100592.asia-northeast3.run.app`

### 2. CI/CD 자동화
- **도구**: Google Cloud Build
- **워크플로우**: 
  1. GitHub `main` 브랜치에 `push` 발생
  2. Cloud Build 자동 트리거 실행
  3. `Dockerfile.backend`를 사용하여 이미지 빌드
  4. Cloud Run에 자동 재배포

### 3. AI 게이트웨이 (LLM Proxy)
- **서비스**: Vercel AI Gateway
- **역할**: 여러 AI 모델(Groq, Gemini 등) 통합 관리, 자동 재시도, Fallback 처리.
- **구성 전략**:
  - **1순위**: Groq Llama 3.3 70B (속도 및 성능 최적화)
  - **2순위**: Google Gemini 2.0 Flash (안정성)
  - **3순위**: Google Gemini 1.5 Flash (무료 쿼터 최후 보루)

---

## 🔗 주요 관리 링크 (Admin Links)

### Google Cloud (GCP)
- **[전체 콘솔 대시보드](https://console.cloud.google.com/?project=gen-lang-client-0043735738)**
- **[Cloud Run 서비스 관리](https://console.cloud.google.com/run/detail/asia-northeast3/cycling-coach-backend/metrics?project=gen-lang-client-0043735738)**
- **[실시간 로그 확인](https://console.cloud.google.com/run/detail/asia-northeast3/cycling-coach-backend/logs?project=gen-lang-client-0043735738)**
- **[Cloud Build 빌드 기록](https://console.cloud.google.com/cloud-build/builds?project=gen-lang-client-0043735738)**

### Vercel
- **[Vercel 대시보드 (프론트엔드 관리)](https://vercel.com/dashboard)**
- **[Vercel AI Gateway 모니터링](https://vercel.com/dashboard/settings/ai)** (프로젝트 설정 내 AI 섹션)

### API 및 데이터베이스
- **[백엔드 API 문서 (Swagger UI)](https://cycling-coach-backend-25085100592.asia-northeast3.run.app/docs)**
- **[Supabase 대시보드](https://supabase.com/dashboard)**

---

## ⚙️ 주요 환경 변수 (Environment Variables)

Cloud Run에 설정된 핵심 변수들입니다:
- `VERCEL_AI_GATEWAY_API_KEY`: Vercel 게이트웨이 인증용
- `SUPABASE_URL` / `SUPABASE_ANON_KEY`: DB 연동용
- `ADMIN_SECRET`: 관리자용 API 보안 패스워드

---

## 🛠 유지보수 가이드
- **코드 수정 후**: `git push origin main`만으로 자동 배포됩니다.
- **응답이 느려질 때**: Cloud Run 로그에서 LLM 호출 시간을 확인하거나 Vercel AI Gateway 대시보드에서 Rate Limit 발생 여부를 확인하세요.
