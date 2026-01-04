# 리팩토링 제안

## 문제 1: 불필요한 데이터 변환 체인

### 현재 구조
```
Backend: 구조화된 steps → extract_workout_sections() → warmup/main/cooldown 텍스트 배열
Frontend: 텍스트 배열 → 정규식 파싱 → 와트 추가 → 표시
```

### 개선안
```
Backend: 구조화된 steps만 전송
Frontend: steps를 직접 포맷팅 (타입 안전하게)
```

**변경 사항:**
1. `extract_workout_sections()` 제거 → 프론트엔드로 이동
2. API 스키마에서 `warmup/main/cooldown` 필드 제거
3. 프론트엔드에서 구조화된 steps를 직접 포맷

**장점:**
- 불필요한 변환 제거
- 타입 안정성 향상
- 코드 간소화

---

## 문제 2: Dead Code 정리

### 제거할 코드
- `WorkoutChart.tsx:parseWorkoutSteps()` - 텍스트 파싱 fallback (50줄)
- `WorkoutChart.tsx:stepsToBarData()` - 더 이상 사용 안 함

**조건:** Intervals.icu가 항상 workout_doc를 반환한다면 제거 가능

**대안:** 방어적 프로그래밍을 위해 유지 (하지만 테스트 필요)

---

## 문제 3: 타입 강화

### 현재
```typescript
steps?: any[]  // 타입 체크 안 됨
```

### 개선안
```typescript
// 공통 타입 정의
interface WorkoutStep {
  duration: number;  // seconds
  power?: PowerSpec;
  ramp?: boolean;
  warmup?: boolean;
  cooldown?: boolean;
  repeat?: number;
  steps?: WorkoutStep[];
}

interface PowerSpec {
  value?: number;
  start?: number;
  end?: number;
  units: string;
}
```

**장점:**
- IDE 자동완성
- 컴파일 타임 에러 검출
- 리팩토링 안전성

---

## 구현 우선순위

### Priority 1 (High Impact, Low Risk)
✅ **타입 정의 추가** - 즉시 개선, 기존 코드 영향 없음

### Priority 2 (Medium Impact, Medium Risk)
⚠️ **Dead code 제거** - 테스트 후 안전하게 제거

### Priority 3 (High Impact, High Risk)
⚠️ **데이터 변환 로직 리팩토링** - API 스키마 변경 필요, 신중하게 진행

---

## 결론

**현재 코드는 동작하지만 비효율적입니다.**

- 급하지 않다면: Priority 1 → 2 → 3 순서로 점진적 개선
- 급하다면: Priority 1만 적용 (타입 추가)
- 안정성 우선: 현재 상태 유지

**추천:** Priority 1 (타입 추가)부터 시작
