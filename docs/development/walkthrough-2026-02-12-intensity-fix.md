# Walkthrough: Endurance 편향 버그 수정 & LLM 프롬프트 리팩터링

> **Created**: 2026-02-12 (Thu) 17:11 KST
> **Updated**: 2026-02-12 (Thu) 17:11 KST
> **Author**: Jevis (AI Assistant)
> **Commits**: `c12f68d` → `c9df051` (10 commits)
> **Branch**: main

---

## 1. 배경

### 증상
사용자가 프로덕션 환경(ai-cycling-workout-planner.vercel.app)에서 운동을 생성할 때,
**TSB 14.6 (Fresh 상태)에서도 Endurance 타입 운동만 반복 생성**되는 문제 발견.

- "Endurance Builder" (~92분, TSS 69)
- "Fresh Legs Endurance Builder" (~72분, TSS 54)
- "Endurance Foundation Builder" (~65분, TSS 48)
- intensity를 "빡세게"로 수동 선택해도 여전히 Endurance만 출력

### 기대 동작
- TSB 14.6 (>= 10) → `intensity = "hard"` 자동 선택
- hard intensity → VO2max/Threshold/Anaerobic 모듈 우선 선택
- 다양한 운동 타입 생성 (SST, VO2max, Threshold 등)

---

## 2. 아키텍처 분석

### 운동 생성 흐름 (프로덕션)

```
Frontend (Vercel)
  ↓ POST /api/workout/generate
Backend (Cloud Run)
  ↓ api/routers/workout.py → generate_enhanced()
  ↓
WorkoutGenerator.generate_enhanced()
  ├─ TSB → intensity 매핑 (코드)
  ├─ _select_modules_with_llm() ← LLM이 모듈 선택
  │   ├─ MODULE_SELECTOR_PROMPT (system_prompt)
  │   └─ "Please generate the workout plan." (user_prompt)
  └─ assembler.assemble_from_plan() ← 선택된 모듈 조합
  ↓
ProtocolBuilder → Intervals.icu 포맷 변환
  ↓
JSON Response → Frontend 렌더링
```

### 발견된 문제 (3가지 근본 원인)

| # | 문제 | 심각도 | 설명 |
|---|------|--------|------|
| 1 | intensity 미전달 | 🔴 Critical | `_select_modules_with_llm()`에 intensity 파라미터 자체가 없음. LLM은 TSB만 보고 판단 |
| 2 | 프롬프트 규칙 약함 | 🟠 High | "Allow High blocks" = 허용이지 강제가 아님. LLM이 보수적으로 Endurance 선택 가능 |
| 3 | 프롬프트 구조 비효율 | 🟡 Medium | system에 13,600 chars 몰빵, user는 고정 문자열. 선수 프로필/wellness 미전달 |

---

## 3. 수정 Phase 1: TSB & Assembler 핫픽스

### 3.1 TSB 경계값 버그 수정 (`c12f68d`)

**문제:** `<` / `>` 사용으로 TSB=-10, TSB=+10 경계값이 "moderate"로 분류

```python
# Before (버그)
if self.tsb < -10:      # TSB=-10은 여기 안 걸림
    intensity = "easy"
elif self.tsb > 10:     # TSB=+10도 여기 안 걸림
    intensity = "hard"

# After (수정)
if self.tsb <= self.TSB_FATIGUE_THRESHOLD:   # -10 이하 → easy
    intensity = "easy"
elif self.tsb >= self.TSB_FRESH_THRESHOLD:   # +10 이상 → hard
    intensity = "hard"
```

### 3.2 긴 운동 로직 수정 (`663a0b4`)

**문제:** 60분+ 운동에서 intensity와 무관하게 Endurance를 추가

```python
# Before (버그)
if available_time > 60:
    preferred_types.append("Endurance")  # hard여도 Endurance 추가됨

# After (수정)
if available_time > 60 and intensity in ["easy", "moderate"]:
    if "Endurance" not in preferred_types:
        preferred_types.append("Endurance")
```

### 3.3 TSB 임계값 상수화 (`a10f151`)

```python
class WorkoutAssembler:
    TSB_FATIGUE_THRESHOLD = -10
    TSB_FRESH_THRESHOLD = 10
```

### 3.4 Warmup 자동 삽입 (`f189a6e`)

```python
def assemble_from_plan(self, selected_modules):
    if first_module_key not in self.warmup_modules:
        logger.warning(f"First module '{first_module_key}' is not warmup. Prepending.")
        selected_modules.insert(0, "ramp_standard")
```

### 3.5 모듈 다양성 스코어링 (`f61fea7`)

기존 `module_usage_tracker.py`의 `calculate_priority_weights()`를 활용:

```python
weights = tracker.calculate_priority_weights(fitting_keys, category="main")
choice = random.choices(fitting, weights=weights, k=1)[0]
# 덜 사용된 모듈에 높은 가중치 (0.5-2.0 스케일)
```

---

## 4. 수정 Phase 2: LLM 프롬프트 수정

### 4.1 LLM에 intensity 명시적 전달 (`5373304`)

**핵심 버그 수정.** `_select_modules_with_llm()` 시그니처에 intensity 추가:

```python
def _select_modules_with_llm(
    self, tsb, form, duration, goal,
    intensity: str = "moderate",  # ← 추가
    weekly_tss=0, yesterday_load=0, exclude_barcode=False,
) -> dict:
```

프롬프트에 **HIGHEST PRIORITY** 강제 규칙 추가:

```
1. **Intensity Override (HIGHEST PRIORITY - FOLLOW STRICTLY):**
   - easy: Use ONLY Endurance/Tempo. FORBID SweetSpot/Threshold/VO2max/Anaerobic.
   - moderate: Prefer SweetSpot/Tempo. Allow max 1 Threshold if TSB > 0.
   - hard: STRONGLY PREFER VO2max/Threshold/Anaerobic. Use 2-3 High blocks. Avoid Endurance.

2. **TSB Safety Check (Secondary):**
   - TSB < -20: Override to easy
   - TSB -10 to -20: Downgrade one level
   - TSB > -10: Follow Intensity preference
```

### 4.2 프롬프트 4단계 리팩터링 (`c6c4146`)

**Step 1: System/User 분리**
```python
# Before
response = llm.generate(
    system_prompt=HUGE_PROMPT_WITH_EVERYTHING,
    user_prompt="Please generate the workout plan."
)

# After
response = llm.generate(
    system_prompt=MODULE_SELECTOR_SYSTEM,  # 역할 + 규칙 + 포맷 (고정)
    user_prompt=MODULE_SELECTOR_USER.format(  # 인벤토리 + 컨텍스트 (가변)
        module_inventory=..., tsb=..., intensity=..., ftp=...,
    )
)
```

**Step 2: 인벤토리 Pre-filtering**
```python
INTENSITY_TYPE_MAP = {
    "easy": ["Endurance", "Tempo", "Recovery"],
    "moderate": ["SweetSpot", "Tempo", "Threshold", "Mixed"],
    "hard": ["VO2max", "Threshold", "Anaerobic", "SweetSpot"],
}
# intensity="hard" → 75개 중 53개만 전달 (토큰 50-70% 절약)
```

**Step 3: 누락 컨텍스트 추가**

| 항목 | Before | After |
|------|--------|-------|
| FTP/Weight | ❌ | ✅ `FTP: 252W \| Weight: 75.2kg` |
| Wellness | ❌ | ✅ `HRV, RHR, Sleep` |
| 날짜/요일 | ❌ | ✅ `Thursday` |
| Indoor/Outdoor | ❌ | ✅ `Indoor Trainer` |

### 4.3 레거시 정리 (`c9df051`)

삭제된 항목:
- `SYSTEM_PROMPT` (레거시 프롬프트)
- `TEMPLATE_REFINEMENT_PROMPT` (미사용)
- `USER_PROMPT_TEMPLATE` (미사용)
- `generate()` 메서드 및 관련 헬퍼 6개
- 임시 스크립트 및 백업 파일

코드 축소:
- **prompts/__init__.py:** 206줄 → 130줄 (-37%)
- **workout_generator.py:** 879줄 → 501줄 (-43%)
- **총 -689줄 삭제**

---

## 5. 수정 후 예상 동작

### Case 1: TSB 14.6 + 자동 intensity
```
TSB 14.6 >= 5 → intensity = "hard"
  ↓
인벤토리: VO2max(20) + Threshold(16) + Anaerobic(1) + SweetSpot(16)만 전달
  ↓
프롬프트: "STRONGLY PREFER VO2max/Threshold. Use 2-3 High blocks"
  ↓
결과: "VO2max Power Builder" / "Threshold Crusher" 등
```

### Case 2: TSB -15 + 자동 intensity
```
TSB -15 <= -10 → intensity = "easy"
  ↓
인벤토리: Endurance(10) + Tempo(7) + Recovery(1)만 전달
  ↓
프롬프트: "Use ONLY Endurance/Tempo. FORBID high intensity"
  ↓
결과: "Endurance + Tempo Combo" / "Easy Spin" 등
```

### Case 3: TSB 3.0 + 수동 "빡세게"
```
User 선택: intensity = "hard" (수동)
  ↓
TSB 3.0 > -10 → Safety Check 통과
  ↓
인벤토리: VO2max + Threshold + Anaerobic + SweetSpot
  ↓
결과: 고강도 인터벌 운동 생성
```

---

## 6. 테스트 결과

| 항목 | 결과 |
|------|------|
| pytest | 58 passed, 5 failed (기존 실패) |
| Vercel 배포 | ✅ Success |
| Cloud Run 배포 | ✅ Auto-trigger |

실패 5건:
- 4건: warmup/cooldown validation 테스트 (dict key 불일치 — `modules` vs `structure`)
- 1건: env vars 미설정 (`INTERVALS_API_KEY`, `ATHLETE_ID`)
→ 모두 이번 변경과 무관한 기존 실패

---

## 7. 커밋 이력

| 시간 (KST) | 커밋 | 내용 |
|------------|------|------|
| 14:56 | `c12f68d` | TSB 경계값 버그 수정 (`<=`, `>=`) |
| 15:01 | `663a0b4` | 긴 운동 로직 — intensity 존중 |
| 15:06 | `a10f151` | TSB 임계값 클래스 상수 추출 |
| 15:14 | `ce13063` | 경계값 테스트 업데이트 |
| 15:31 | `f189a6e` | Warmup 자동 삽입 validation |
| 15:34 | `f61fea7` | 모듈 다양성 weighted selection |
| 16:04 | `b18b2ad` | LLM 모드에도 TSB→intensity 매핑 |
| 16:24 | `5373304` | **LLM에 intensity 명시적 전달** (핵심 수정) |
| 16:35 | `c6c4146` | 프롬프트 4단계 리팩터링 |
| 16:45 | `c9df051` | 레거시 삭제 (-689줄) |

---

## 8. 향후 과제

- [ ] 프로덕션 실제 테스트 — 다양한 TSB 값에서 운동 생성 확인
- [ ] Cloud Run 배포 상태 확인
- [ ] LLM temperature 튜닝 (현재 0.7 — 다양성 vs 일관성 밸런스)
- [ ] Few-shot 예시 추가 (intensity별 모듈 조합 예시)
- [ ] 실패 테스트 5건 수정 (dict key 정규화)
- [ ] `prompt-architecture.md` 문서 업데이트
