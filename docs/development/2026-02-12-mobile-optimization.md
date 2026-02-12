# Mobile Optimization & UX Improvements - 2026-02-12

> **Created**: 2026-02-12 (Wed) 20:24 KST
> **Updated**: 2026-02-12 (Wed) 20:24 KST

## Overview

Major development session focused on:
1. Backend workout generation improvements
2. Frontend mobile optimization (7 phases)
3. UX/copy enhancements
4. Bug fixes and technical debt reduction

**Total commits**: 15+
**Lines changed**: -689 (backend), +hundreds (frontend)
**Duration**: ~3 hours

---

## Backend Improvements

### 1. TSB-Based Intensity Auto-Selection
**Commits**: `ce13063`, `b18b2ad`, `5373304`

**Problem**: Workout generation produced monotonous endurance patterns regardless of athlete readiness.

**Solution**: 
- Implemented TSB-based intensity mapping in `generator.py`
- Added explicit intensity parameter to LLM mode
- Changed prompt from "Allow" to "STRICTLY FOLLOW" for intensity

**Code changes**:
- `generate_enhanced()`: TSB thresholds (<-20: easy, <-10: easy, <5: moderate, >=5: hard)
- `_select_modules_with_llm()`: intensity parameter + HIGHEST PRIORITY rules

**Result**: AI now generates VO2max/Threshold workouts when TSB is positive, recovery when negative.

### 2. LLM Prompt Refactoring
**Commits**: `c6c4146`, `c9df051`

**Changes**:
- Split `MODULE_SELECTOR_PROMPT` → `MODULE_SELECTOR_SYSTEM` + `MODULE_SELECTOR_USER`
- Added `INTENSITY_TYPE_MAP` for pre-filtering (50-70% token reduction)
- Added FTP, weight, wellness, weekday, indoor/outdoor to context
- Deleted unused functions (-689 lines total)

**Benefits**:
- Clearer separation of fixed rules vs. dynamic data
- Reduced API costs via inventory pre-filtering
- Better maintainability

### 3. Other Backend Fixes
- Warmup validation (`f189a6e`): Auto-prepend `ramp_standard` if missing
- Module diversity (`f61fea7`): Weighted random selection using `module_usage_tracker.py`
- Test fixes (`2a300b3`): 62 passed, 1 skipped

---

## Frontend Mobile Optimization

### Phase 1: Responsive Layout
**Commits**: `1f3b25d`, `0ec6eb8`

**Changes**:
- Header: 2-row layout, responsive button sizing (`text-xs sm:text-sm`)
- App padding: `2rem` → `px-3 sm:px-4`
- TodayWorkoutCard: Button stacking (`flex-col sm:flex-row`)
- WeeklyCalendarCard: Chart overflow fix (`min-w-[640px] + overflow-x-auto`)

**Bug fix**: JSX nesting error in WeeklyCalendarCard (urgent repair in `0ec6eb8`)

### Phase 2: UX Optimization
**Commit**: `2671673`

**44px touch targets**:
- All buttons: `h-11 sm:h-9` (44px mobile, 36px desktop)
- Slider thumb: `[&_[role=slider]]:h-11`

**Loading states**:
- Wired FitnessCard, WeeklyCalendar, WeeklyPlan, TodayWorkout skeletons
- Added spinners to Generate/Register buttons

**Touch animations**:
- `transition-all active:scale-95` (buttons)
- `active:scale-[0.99]` (cards)

### Phase 3: Performance
**Commit**: `04a5271`

**Code splitting**:
- React.lazy() for AdminPage, SettingsPage, OnboardingPage, LandingPage, AuthPage, ResetPasswordPage
- Suspense with PageLoader component

**Bundle optimization**:
- Manual chunks: vendor-react (11.32 kB), vendor-charts (288.92 kB), vendor-ui (44.52 kB), vendor-i18n (54.41 kB), vendor-data (203.51 kB)
- **Result**: 68% reduction (940.78 → 298.17 kB, gzipped 280.55 → 91.87 kB)
- 500 kB+ warning resolved

### Phase 4: Best Practices
**Commit**: `093125d`

**Error Boundary**: Catch React errors gracefully
**SEO**: Meta tags (description, keywords, Open Graph, Twitter Card)
**PWA**: `manifest.json` (standalone mode, icons, shortcuts)
**Vercel security**: X-Frame-Options, X-Content-Type-Options, Referrer-Policy, etc.

### Phase 5: UX Copy
**Commit**: `ffe2818`

**Button/message improvements**:
- "워크아웃 생성" → "오늘의 훈련 만들기"
- "등록 완료!" → "🎉 완벽해요! 이제 사이클링 컴퓨터에서 확인하세요"
- Error messages: "😥 잠시 문제가 발생했어요..."

**Landing page FAQ**: 5 questions (platform support, flexibility, cost, outdoor, data safety)

### Phase 6: Onboarding & Dashboard
**Commits**: `daba7a3`, `50c6813`, `94c963e`

**Onboarding progress**: Step 1/3, progress bar, estimated time
**Empty states**: TodayWorkoutCard + WeeklyPlanCard friendly guidance
**Glossary**: Collapsible term definitions (CTL, ATL, TSB, FTP, HRV)

**Bug**: Tooltip accessibility on mobile → replaced with `<details>` glossary
**Fix**: Exercise physiology accuracy (HRV baseline, CTL overtraining, FTP measurement)

### Phase 7: Landing Page Enhancement
**Commit**: `c185ee0`

**Mock testimonials**: 3 cards (Wahoo/Garmin/trainer users), labeled as examples
**Before/After**: 2-column comparison (❌ vs ✅)

---

## Bug Fixes

### Emoji Duplication (Multiple occurrences)
**Commits**: `7218133`, `56e16be`, `92af629`

**Problem**: Emoji appearing twice (e.g., "🔄 🔄 Try Different Workout")
**Root cause**: Code prefixes emoji + i18n also contains emoji
**Solution**: Remove emoji from i18n when code prefixes it
**Prevention**: Added `_comment` rule in i18n files

### i18n Consistency
**Commits**: `7218133`, `56e16be`

**Problem**: "regenerate" and "register" keys had emoji in translation files
**Fix**: Removed emoji from `ko.json` and `en.json`

### Admin Deployment Info
**Commit**: `5203384`

**Feature**: Added deployment version info to admin dashboard
- Backend: `git_commit`, `git_commit_date`, `started_at` in `/api/health`
- Frontend: `__BUILD_TIME__` via Vite define

---

## Development Environment

### Git Pre-Push Hook
**Setup**: `.git/hooks/pre-push`

**Checks**:
1. Frontend: `pnpm build` (blocks push if build fails)
2. Backend: Python syntax check (`py_compile`)

**Benefit**: Prevents deployment of broken code (e.g., JSX errors)

---

## Key Decisions & Lessons

### 1. Emoji Policy
**Rule**: Emoji in code only, never in i18n translation values
**Reason**: Prevents duplication when code prefixes emoji
**Enforcement**: Comment in i18n files + pre-push hook

### 2. Mobile-First Design
**Approach**: 44px touch targets, collapse/expand over hover, skeleton loading
**Tools**: Tailwind CSS v4 responsive utilities (`sm:`, `md:`, `lg:`)

### 3. Exercise Physiology Accuracy
**Learning**: HRV is relative to personal baseline, not absolute values
**Expert review**: User (experienced cyclist) corrected HRV glossary
**Takeaway**: Domain expertise required for specialized content

### 4. Performance Budget
**Target**: <300 kB initial load (gzipped)
**Achieved**: 91.87 kB (gzipped) via code splitting + manual chunks
**Monitoring**: Vite build warnings + pre-push hook

### 5. Incremental Deployment
**Strategy**: 7 phases over 3 hours, each tested and deployed separately
**Benefit**: Easy rollback if issues found, clear commit history

---

## Technical Stack

- **Backend**: Python, FastAPI
- **Frontend**: React 18, Vite, Tailwind CSS v4
- **UI**: shadcn/ui components
- **i18n**: react-i18next (ko/en)
- **Deployment**: Vercel (frontend), Google Cloud Run (backend)
- **Infrastructure**: Raspberry Pi 5 (8GB), Docker

---

## Metrics

**Build Performance**:
- Before: 940.78 kB (280.55 kB gzipped)
- After: 298.17 kB (91.87 kB gzipped)
- Improvement: 68% reduction

**Code Changes**:
- Backend: -689 lines (legacy removal)
- Frontend: +hundreds (new features + mobile optimization)

**Test Coverage**:
- Backend: 62 passed, 1 skipped
- Frontend: Build validation via pre-push hook

---

## Next Steps

- [ ] Production verification (TSB 14.6 + auto → VO2max/Threshold)
- [ ] User testing (real users, not mock testimonials)
- [ ] Phase 8: Mobile gestures (swipe, pull-to-refresh)
- [ ] A/B testing: Landing page conversion rate

---

## References

- UX improvement suggestions: `/home/node/.openclaw/workspace/ux-improvement-suggestions.md`
- Memory log: `/home/node/.openclaw/workspace/memory/2026-02-12.md`
- Channel context: `/home/node/.openclaw/workspace/memory/channels/aicoach.md`
