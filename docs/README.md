# AI Cycling Coach - Documentation

> **Last Updated**: 2026-01-11  
> **Project**: AI-powered cycling workout generation and planning system

## 📚 Documentation Structure

이 문서 폴더는 프로젝트의 모든 기술 문서와 가이드를 체계적으로 관리합니다.

---

## 📖 Quick Navigation

### 🚀 Getting Started
- [Project README](../README.md) - 프로젝트 소개 및 빠른 시작 가이드
- [System Architecture](reference/system-architecture.md) - 전체 시스템 구조 및 설계
- [Requirements Specification](reference/requirements-specification.md) - 기능 요구사항 명세

### 🛠️ Guides
운영 및 개발 가이드 문서들:
- [Deployment Guide](guides/deployment-guide.md) - Vercel + Google Cloud Run 배포 가이드
- [Infrastructure Setup](guides/infrastructure-setup.md) - GCP 인프라 구조 및 관리 링크
- [Caching Strategy](guides/caching-strategy.md) - TTL 기반 캐싱 구현 및 무효화 전략
- [Frontend Performance](guides/frontend-performance.md) - React Query 및 성능 최적화
- [Version Update System](guides/version-update-system.md) - 앱 버전 관리 및 업데이트 알림 시스템

### 💻 Development
개발자를 위한 참고 문서:
- [Prompt Architecture](development/prompt-architecture.md) - AI 프롬프트 구조 및 설계 원칙
- [Prompt Library](development/prompt-library.md) - 훈련 스타일별 프롬프트 템플릿
- [Claude Skills](development/claude-skills.md) - Claude Code와 함께 사용하는 커스텀 스킬

### 📚 Reference
기술 명세 및 API 문서:
- [System Architecture](reference/system-architecture.md) - 시스템 아키텍처 상세 문서
- [Roadmap and TODOs](reference/roadmap-and-todos.md) - 기능 로드맵 및 작업 목록
- [API Specification](reference/api-specification.json) - OpenAPI 3.0 명세

### 🗄️ Archive
과거 버그 수정 및 작업 기록:
- [Bug Fixes (2026-01-10)](archive/bug-fixes-2026-01-10.md) - Weekly Plan 버그 수정 기록
- [Weekly Plan Bug Report](archive/weekly-plan-bug-report.md) - 주간 계획 버그 리포트
- [Refactoring Proposal](archive/refactoring-proposal.md) - 코드 리팩토링 제안
- [Worklog (2025-12)](archive/worklog-2025-12.md) - 2025년 12월 작업 로그

---

## 🏗️ System Overview

```
┌─────────────────┐     HTTPS    ┌─────────────────┐     API      ┌─────────────────┐
│   React.js      │ ──────────▶  │    FastAPI      │ ──────────▶  │  Intervals.icu  │
│   (Vercel)      │              │  (Cloud Run)    │              │      API        │
└─────────────────┘              └────────┬────────┘              └─────────────────┘
                                          │
                              ┌───────────┴───────────┐
                              ▼                       ▼
                       ┌─────────────┐         ┌─────────────┐
                       │  Vercel AI  │         │  Supabase   │
                       │  Gateway    │         │    Auth     │
                       └─────────────┘         └─────────────┘
```

---

## 🎯 Key Features

### 1. AI Workout Generation
- **Modular System**: WARMUP → MAIN → COOLDOWN 구조
- **Training Styles**: Polarized, Norwegian, Sweet Spot, Base, Threshold
- **Smart Planning**: CTL/ATL/TSB 기반 부하 관리

### 2. Weekly Planning
- **7-Day Generation**: 주간 훈련 계획 자동 생성
- **Auto Registration**: Intervals.icu 캘린더 자동 등록
- **Adaptive Load**: 일일 부하 및 회복 상태 고려

### 3. Multi-LLM Fallback
- **Primary**: Groq (Llama 3.3 70B)
- **Secondary**: Google Gemini 2.0 Flash
- **Tertiary**: Google Gemini 1.5 Flash
- **Auto Fallback**: 쿼터 초과 시 자동 전환

### 4. Performance Optimization
- **React Query**: 클라이언트 사이드 캐싱
- **Backend Cache**: Redis 기반 TTL 캐싱
- **Parallel Loading**: 병렬 데이터 페칭

---

## 📝 Contributing

문서 업데이트 시 다음 규칙을 따라주세요:

### 파일 명명 규칙
- **소문자 + 하이픈**: `system-architecture.md` ✅ (NOT `SystemArchitecture.md` ❌)
- **명확한 목적**: 파일명만 보고 내용을 파악할 수 있어야 함
- **카테고리 분류**: guides, development, reference, archive 중 적절한 폴더에 배치

### 문서 작성 스타일
- **Last Updated**: 문서 상단에 마지막 수정일 표시
- **코드 예시**: 실제 동작하는 코드 블록 사용
- **명확한 구조**: 제목 계층 구조 명확히 (H1 → H2 → H3)
- **링크 활용**: 관련 문서 및 코드 파일 링크 추가

---

## 🔗 External Resources

- **Production URL**: https://ai-cycling-workout-planner.vercel.app
- **Backend API**: https://cycling-coach-backend-25085100592.asia-northeast3.run.app
- **API Docs**: https://cycling-coach-backend-25085100592.asia-northeast3.run.app/docs
- **GCP Console**: https://console.cloud.google.com/?project=gen-lang-client-0043735738
- **Supabase**: https://supabase.com/dashboard

---

## 📞 Support

문서 관련 문의사항이나 개선 제안은 이슈를 생성해 주세요.

**Document Maintainer**: AI Cycling Coach Team  
**Last Review**: 2026-01-11
