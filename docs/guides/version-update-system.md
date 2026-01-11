# 업데이트 알림 시스템 가이드

## 개요

사용자에게 새로운 기능 업데이트를 알리는 모달 팝업 시스템입니다. localStorage를 사용하여 사용자가 마지막으로 확인한 버전을 추적하고, 새 버전이 배포되면 자동으로 알림을 표시합니다.

## 주요 기능

- **자동 버전 감지**: 앱 로드 시 자동으로 새 버전 확인
- **Semantic Versioning**: `v1.1.0` 형식의 버전 관리
- **LocalStorage 기반**: 디바이스별로 확인 상태 저장
- **아름다운 UI**: Radix UI Dialog를 활용한 세련된 모달 디자인
- **기능 강조**: 각 업데이트 항목에 아이콘과 설명 포함

## 파일 구조

```
frontend/src/
├── lib/version.ts                          # 버전 관리 유틸리티
├── components/UpdateAnnouncementModal.tsx  # 업데이트 알림 모달
├── hooks/useVersionCheck.ts                # 버전 체크 훅 (선택적)
└── App.tsx                                 # 모달 통합
```

## 새 버전 추가 방법

### 1. 버전 번호 업데이트

[lib/version.ts](frontend/src/lib/version.ts) 파일에서 `CURRENT_VERSION`을 변경합니다.

```typescript
// Semantic Versioning: MAJOR.MINOR.PATCH
export const CURRENT_VERSION = "1.2.0";
```

**버전 규칙:**
- **MAJOR**: 호환성이 깨지는 큰 변경 (예: 1.x.x → 2.0.0)
- **MINOR**: 새로운 기능 추가 (예: 1.1.x → 1.2.0)
- **PATCH**: 버그 수정 및 마이너 개선 (예: 1.1.0 → 1.1.1)

### 2. 업데이트 내용 추가

같은 파일의 `VERSION_HISTORY` 배열 **맨 앞에** 새 버전 정보를 추가합니다.

```typescript
export const VERSION_HISTORY: VersionUpdate[] = [
  {
    version: "1.2.0",  // CURRENT_VERSION과 동일해야 함
    date: "2026-01-15",  // YYYY-MM-DD 형식
    title: "성능 개선 및 새 기능 추가",
    features: [
      {
        title: "AI 추천 속도 향상",
        description: "워크아웃 생성 시간이 50% 단축되었습니다.",
        icon: "⚡",
      },
      {
        title: "다크 모드 지원",
        description: "눈의 피로를 줄이는 다크 테마를 추가했습니다.",
        icon: "🌙",
      },
    ],
  },
  // 이전 버전들...
];
```

### 3. 배포 및 확인

```bash
# 빌드 및 배포
npm run build
# 또는
npm run dev

# 앱을 열면 자동으로 업데이트 모달이 표시됩니다
```

## 동작 원리

### 초기 방문 (신규 사용자)
1. localStorage에 저장된 `lastSeenVersion`이 없음
2. 현재 버전을 localStorage에 저장
3. **모달을 표시하지 않음** (첫 방문이므로)

### 재방문 (기존 사용자)
1. localStorage의 `lastSeenVersion`을 읽음
2. `CURRENT_VERSION`과 비교
3. 현재 버전이 더 높으면 → **모달 표시**
4. 사용자가 "확인했습니다" 클릭 → 새 버전을 localStorage에 저장

### 버전 비교 로직

```typescript
// 예시:
compareVersions("1.2.0", "1.1.0") // → 1 (새 버전)
compareVersions("1.1.0", "1.1.0") // → 0 (같은 버전)
compareVersions("1.0.5", "1.1.0") // → -1 (이전 버전)
```

## 테스트 방법

### 1. 로컬 테스트 (개발 중)

```javascript
// 브라우저 콘솔에서 실행
localStorage.removeItem('lastSeenVersion');
// 페이지 새로고침 → 모달이 나타나야 함
```

### 2. 특정 버전으로 테스트

```javascript
// 이전 버전으로 설정
localStorage.setItem('lastSeenVersion', '1.0.0');
// 페이지 새로고침 → 현재 버전이 1.1.0이면 모달 표시
```

### 3. 모달 재표시하기

```javascript
// 현재 저장된 버전 확인
console.log(localStorage.getItem('lastSeenVersion'));

// 삭제 후 새로고침
localStorage.removeItem('lastSeenVersion');
location.reload();
```

## 커스터마이징

### 모달 디자인 변경

[UpdateAnnouncementModal.tsx](frontend/src/components/UpdateAnnouncementModal.tsx)에서 Tailwind CSS 클래스를 수정합니다.

```tsx
// 배경 그라디언트 변경
className="bg-gradient-to-br from-green-50 to-blue-50"

// 버전 뱃지 색상 변경
className="bg-gradient-to-br from-green-500 to-blue-600"
```

### 아이콘 추가

```typescript
features: [
  {
    title: "새 기능",
    description: "설명",
    icon: "🎉",  // 원하는 이모지 사용
  },
]
```

**추천 이모지:**
- 새 기능: 🎉 ✨ 🚀 ⭐
- 개선: ⚡ 📈 💪 🔧
- 버그 수정: 🐛 🔨 🩹
- UI/UX: 🎨 💅 📱
- 설정: ⚙️ 🔧 🛠️
- 달력/일정: 📅 📆 🗓️
- 워크아웃: 🚴 💪 🏋️
- 데이터: 📊 📈 💾

## 백엔드 연동 (선택 사항)

현재는 프론트엔드에서만 동작하지만, 디바이스 간 동기화가 필요한 경우 백엔드 저장소로 확장할 수 있습니다.

### 백엔드 API 추가 예시

```typescript
// lib/api.ts
export async function saveSeenVersion(
  accessToken: string,
  version: string
): Promise<void> {
  await fetch(`${API_BASE}/api/user/seen-version`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${accessToken}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ version }),
  });
}

export async function getSeenVersion(
  accessToken: string
): Promise<string | null> {
  const response = await fetch(`${API_BASE}/api/user/seen-version`, {
    headers: {
      'Authorization': `Bearer ${accessToken}`,
    },
  });
  const data = await response.json();
  return data.version || null;
}
```

### 데이터베이스 스키마 예시

```sql
CREATE TABLE user_settings (
  user_id UUID PRIMARY KEY,
  last_seen_version VARCHAR(20),
  updated_at TIMESTAMP DEFAULT NOW()
);
```

## 모범 사례

### 버전 릴리스 주기
- **MAJOR**: 분기별 (3개월)
- **MINOR**: 월별 (중요 기능 추가 시)
- **PATCH**: 주별 또는 필요 시 (버그 수정)

### 업데이트 내용 작성 팁
1. **사용자 관점**: 기술적 상세보다는 사용자 혜택 강조
2. **간결함**: 각 항목은 1-2문장으로 제한
3. **시각적 요소**: 아이콘을 활용하여 빠른 스캔 가능하게
4. **긍정적 언어**: "이제 ~할 수 있습니다" 형식 사용

### 좋은 예시
```typescript
{
  title: "주간 워크아웃 플랜 기능 추가",
  description: "이제 7일 치 워크아웃을 한 번에 생성하고 관리할 수 있습니다.",
  icon: "📅",
}
```

### 나쁜 예시
```typescript
{
  title: "WeeklyPlanCard 컴포넌트 구현",
  description: "React Query를 사용하여 주간 플랜 API를 호출하고 캐싱 처리",
  icon: "💻",
}
```

## 트러블슈팅

### 모달이 표시되지 않음
1. `CURRENT_VERSION`과 `VERSION_HISTORY[0].version`이 일치하는지 확인
2. localStorage의 `lastSeenVersion`이 현재 버전보다 낮은지 확인
3. 브라우저 콘솔에서 에러 메시지 확인

### 모달이 계속 표시됨
1. localStorage에 버전이 제대로 저장되는지 확인
2. `markVersionAsSeen()` 함수가 호출되는지 확인
3. localStorage가 차단되어 있지 않은지 확인 (프라이빗 모드)

### 타입 에러
```bash
# TypeScript 체크
npm run build

# 특정 파일만 체크
npx tsc --noEmit src/lib/version.ts
```

## 향후 개선 방향

- [ ] 관리자 페이지에서 업데이트 관리
- [ ] A/B 테스트를 위한 타겟팅 옵션
- [ ] 업데이트 내용 미리보기 기능
- [ ] 다국어 지원
- [ ] 애니메이션 개선
- [ ] 모달 대신 인앱 알림 옵션

## 라이선스

이 시스템은 프로젝트의 라이선스를 따릅니다.
