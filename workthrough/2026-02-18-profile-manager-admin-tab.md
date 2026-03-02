# Profile Manager — Admin Profiles 탭 전체 구현

## Overview

기존 Admin 대시보드에 **Profiles 탭**을 추가하여 2,578개 워크아웃 프로필을 브라우징, 검색, 필터링, 상세 조회, 삭제할 수 있도록 구현했다. 백엔드 REST API(FastAPI + SQLite)와 프론트엔드 UI(React + SWR + Recharts)를 풀스택으로 개발하고, Gemini-Claude 리뷰 루프를 거쳐 코드 품질을 검증했으며, 29개 E2E 테스트를 모두 통과했다.

## Context

- 2,578개 워크아웃 프로필이 SQLite DB(24개 컬럼)에 저장되어 있었으나 관리 UI가 없었음
- 기존 `/api/profile-stats` 엔드포인트는 `api/main.py`에 인라인으로 작성되어 있어 구조적으로 부적절
- Admin 페이지는 3개 탭(`overview`, `api-logs`, `audit-logs`)으로 운영 중이었음

## Changes Made

### 1. Backend Service — `api/services/workout_profile_service.py`

`WorkoutProfileService` 클래스에 3개 메서드 추가 (+147 lines):

- **`list_profiles()`**: 페이지네이션 + 동적 필터링 (category, difficulty, source, search, is_active). `steps_json`/`zwo_xml` 제외하여 성능 최적화. 별도 COUNT 쿼리로 total 반환.
- **`delete_profile()`**: Hard delete with commit. rowcount 기반 존재 여부 확인.
- **`get_profile_stats()`**: GROUP BY 쿼리로 카테고리/소스/난이도별 분포 통계.

```python
# api/services/workout_profile_service.py
def list_profiles(self, offset=0, limit=50, category=None, difficulty=None,
                  source=None, search=None, is_active=None) -> Dict[str, Any]:
    columns = "id, name, slug, category, ..."  # steps_json, zwo_xml 제외
    query = f"SELECT {columns} FROM workout_profiles WHERE 1=1"
    # 동적 WHERE 절 + 파라미터 바인딩
    if category:
        query += " AND category = ?"
        params.append(category)
    # ... 나머지 필터
    query += " ORDER BY id ASC LIMIT ? OFFSET ?"
    return {"items": [...], "total": count}
```

### 2. Backend Router — `api/routers/profiles.py` (신규, 120 lines)

| Endpoint | Method | Description |
|---|---|---|
| `/api/profiles/stats` | GET | DB 통계 (category/source/difficulty 분포) |
| `/api/profiles` | GET | 페이지네이션 목록 (필터/검색 지원) |
| `/api/profiles/{id}` | GET | 전체 24개 컬럼 상세 (JSON 필드 파싱) |
| `/api/profiles/{id}` | DELETE | Hard delete |

- 인증: `get_admin_user()` 의존성 (admin.py에서 import) — JWT + Supabase admin 검증
- `/profiles/stats`를 `/profiles/{id}` 위에 등록하여 FastAPI 라우팅 충돌 방지
- 상세 조회 시 `is_active=0`인 비활성 프로필도 admin에게 표시

### 3. Backend Main — `api/main.py`

- profiles 라우터 등록: `app.include_router(profiles.router, prefix="/api", tags=["profiles"])`
- 기존 인라인 `@app.get("/api/profile-stats")` 엔드포인트 제거 (-33 lines)

### 4. Frontend — `AdminPage.tsx`

```typescript
// 탭 타입 확장
const [activeTab, setActiveTab] = useState<
    'overview' | 'api-logs' | 'audit-logs' | 'profiles'
>('overview');

// 탭 버튼 + 렌더링 추가
{activeTab === 'profiles' && <ProfilesTab />}
```

### 5. Frontend — `ProfilesTab.tsx` (신규, 336 lines)

주요 기능:
- **Stats Bar**: 4개 카드 (총 프로필수, 카테고리수, 소스수, 난이도 레벨수)
- **필터바**: category/difficulty/source 드롭다운 (stats 데이터로 옵션 동적 생성) + 텍스트 검색
- **테이블**: 10개 컬럼 (ID, Name, Category, Zone, Duration, TSS, IF, Difficulty, Source, Active)
- **페이지네이션**: offset/limit 기반, 이전/다음 버튼
- **행 클릭**: ProfileDetailModal 열기

```typescript
// SWR: 탭 활성화 시에만 fetch (lazy loading)
const { data: listData } = useSWR<{ items: ProfileListItem[]; total: number }>(
    session?.access_token ? `/api/profiles?${queryParams}` : null,
    authFetcher, defaultSWRConfig
);
```

### 6. Frontend — `ProfileDetailModal.tsx` (신규, 234 lines)

- SWR로 개별 프로필 fetch (전체 24개 컬럼)
- **ProfileChart**: Zwift 스타일 파워 프로필 차트 (풀사이즈)
- 섹션별 그룹핑: Basic Info → Training Data → Tags → Description → Coach Notes → ZWO XML (접기/펼치기) → System
- **2단계 삭제 확인**: Delete → Confirm Delete (에러 메시지 표시)
- Backdrop 클릭으로 닫기

### 7. Frontend — `ProfileChart.tsx` (신규, 279 lines)

- Recharts `ComposedChart` + `Area` (type="stepAfter", stackId="power")
- **Zwift 스타일**: 검은 배경 (`#1a1a2e`), 네온 Zone 색상
- DB 포맷과 프론트엔드 포맷 모두 지원 (type/start_power/end_power 및 power.value/power.start/power.end)
- Repeat 블록 재귀 처리 (intervals, nested steps)

```typescript
// Zone 색상 (Zwift 팔레트)
function getZoneColor(power: number): string {
    if (power <= 55) return '#009e80';   // Z1
    if (power <= 75) return '#009e00';   // Z2
    if (power <= 90) return '#ffcb0e';   // Z3
    if (power <= 105) return '#ff7f0e';  // Z4
    if (power <= 120) return '#dd0447';  // Z5
    return '#6633cc';                     // Z6
}
```

### 8. Gemini Review 반영

- `ProfileDetailModal.tsx`: `authFetcher`를 `useMemo`로 메모이제이션 (매 렌더 재생성 방지)
- `ProfileDetailModal.tsx`: `handleDelete`의 빈 catch 블록 → 에러 상태 관리 + UI 에러 메시지 표시

## Verification Results

### Frontend Build
```
> pnpm build
✓ built in 2.52s
dist/assets/AdminPage-B3a2rG4B.js  39.96 kB │ gzip: 11.83 kB
```

### E2E Tests (29/29 PASSED)

```
--- Auth Guard (5/5) ---
GET /api/profiles      (no auth)   → 401  PASS
GET /api/profiles/stats (no auth)  → 401  PASS
GET /api/profiles/1     (no auth)  → 401  PASS
DELETE /api/profiles/1  (no auth)  → 401  PASS
GET /api/profiles       (bad token)→ 401  PASS

--- Stats (5/5) ---
returns 200, total=2578, 10 categories, 3 sources, 3 difficulty levels

--- List & Pagination (4/4) ---
limit=5 returns 5 items, excludes steps_json/zwo_xml,
all required fields present, offset pagination works

--- Filters (6/6) ---
category=vo2max, difficulty=beginner, source=zwift (58),
search=Burst (45), combined filters, empty search → 0

--- Detail (5/5) ---
GET /api/profiles/1 → 200, steps_json parsed as dict,
24 columns present (25 keys), tags parsed as list,
non-existent → 404

--- Delete (4/4) ---
DELETE → 200, deleted → 404, non-existent → 404,
total count 2578 → 2577
```

### Git
```
54e6c1d feat(admin): add Profiles tab with browse, search, and delete
8 files changed, 1181 insertions(+), 35 deletions(-)
Pushed to origin/main
```

## Architecture Summary

```
AdminPage.tsx
  └── ProfilesTab.tsx
        ├── SWR: GET /api/profiles?filters    → list_profiles()
        ├── SWR: GET /api/profiles/stats      → get_profile_stats()
        └── ProfileDetailModal.tsx
              ├── SWR: GET /api/profiles/{id}  → get_profile_by_id()
              ├── ProfileChart.tsx (Recharts)
              └── DELETE /api/profiles/{id}    → delete_profile()
```

## Next Steps

- 프로필 편집 (PATCH) — is_active 토글, 메타데이터 수정
- 프로필 일괄 삭제/내보내기
- 목록에 미니 차트 프리뷰 (성능 테스트 필요)
- 프로필 중복 검사 (slug 기반)
- i18n 지원 (현재 영어 하드코딩)
