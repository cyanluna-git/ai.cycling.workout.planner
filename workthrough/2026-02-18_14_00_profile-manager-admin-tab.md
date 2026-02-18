# Profile Manager — Admin Profiles 탭 구현

## 개요
2,578개 워크아웃 프로필을 브라우징/검색/삭제할 수 있는 Admin 페이지 "Profiles" 탭을 구현했다. 백엔드 API(FastAPI + SQLite)와 프론트엔드 UI(React + SWR + Recharts)를 모두 새로 작성했으며, Gemini-Claude 리뷰 루프로 코드 품질을 검증했다.

## 주요 변경사항

### Backend (Python/FastAPI)
- **추가**: `api/routers/profiles.py` — 프로필 CRUD API (GET list, GET detail, DELETE, GET stats)
- **수정**: `api/services/workout_profile_service.py` — `list_profiles()`, `delete_profile()`, `get_profile_stats()` 메서드 추가
- **수정**: `api/main.py` — profiles 라우터 등록, 기존 inline `/api/profile-stats` 엔드포인트 제거

### Frontend (React/TypeScript)
- **추가**: `ProfilesTab.tsx` — 프로필 목록 + 필터(category/difficulty/source) + 검색 + 페이지네이션
- **추가**: `ProfileDetailModal.tsx` — 24개 컬럼 상세 모달 + Zwift 차트 + 2단계 삭제 확인
- **추가**: `ProfileChart.tsx` — Zwift 스타일 파워 프로필 차트 (dark bg, zone colors, Recharts)
- **수정**: `AdminPage.tsx` — 'profiles' 탭 추가

### Gemini 리뷰 반영
- `authFetcher` useMemo로 메모이제이션 (성능)
- Delete 에러 핸들링 추가 (빈 catch → 에러 메시지 표시)

## 핵심 API

```
GET  /api/profiles?offset=0&limit=50&category=&difficulty=&source=&search=
GET  /api/profiles/{id}        # 전체 24개 컬럼 (steps_json 파싱)
DELETE /api/profiles/{id}      # Hard delete
GET  /api/profiles/stats       # 카테고리/난이도/소스별 통계
```

## 결과
- ✅ 프론트엔드 빌드 성공 (`pnpm build`)
- ✅ 백엔드 DB 쿼리 정상 동작 (2,578 프로필)
- ✅ Gemini 코드 리뷰 통과

## 다음 단계
- 프로필 편집(PATCH) 기능 추가 — is_active 토글, 메타데이터 수정
- 프로필 일괄 삭제/내보내기 기능
- 목록에 미니 차트 프리뷰 추가 (성능 테스트 필요)
- 프로필 중복 검사 기능 (slug 기반)
- i18n 지원 (현재 영어 하드코딩)
