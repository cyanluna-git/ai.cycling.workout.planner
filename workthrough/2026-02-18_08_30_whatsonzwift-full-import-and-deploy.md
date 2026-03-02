# whatsonzwift.com 2,420개 운동 임포트 및 프로덕션 배포

## 개요
whatsonzwift.com 스크래퍼를 실제 실행하여 127개 사이클링 컬렉션에서 2,420개 운동을 임포트했다. 임포트된 프로필에 difficulty/coach_notes/category enrichment를 적용하고, Dockerfile을 수정하여 프로덕션(Cloud Run)에 배포 완료했다. `/api/profile-stats` 엔드포인트를 추가하여 프로덕션에서 2,578개 프로필 확인.

## 주요 변경사항

### 스크래퍼 수정 및 대규모 임포트
- `extract_step_texts()` 수정 — `div.textbar` 기반 1차 추출 + 텍스트 노드 fallback 구조로 변경 (사이트 HTML이 span+data-value 포함)
- `SKIP_SLUGS` 보강 — 러닝/트라이 관련 31개 슬러그 추가 (151 → 127개 사이클링 컬렉션)
- 이름 충돌 수정 — 페이지 타이틀 대신 URL slug 사용 (같은 컬렉션 내 "Day 1" 충돌 해결)
- **전체 실행 결과**: 2,420개 임포트, 165개 스킵(no steps), 0개 실패, 약 2.5시간 소요

### enrichment 스크립트 (`scripts/enrich_profiles.py`)
- **Difficulty 재분류**: IF < 0.70 → beginner, 0.70-0.85 → intermediate, ≥ 0.85 → advanced (1,228개 변경)
- **coach_notes 추가**: 모든 프로필에 기본 커스터마이즈 범위 부여 (2,478개 추가)
- **"mixed" 카테고리 해소**: 659개 → 0개 (step power 분석으로 구체적 카테고리 재분류)

### 배포 파이프라인 변경
- `.gitignore`에서 `data/workout_profiles.db` 추적 활성화 (7.4MB)
- `Dockerfile.backend` — `seed_profiles.py + migrate_db_format.py` 실행 제거 → `COPY data/workout_profiles.db` 직접 복사
- `STYLE_CATEGORIES`에 "mixed" fallback 추가

### 프로덕션 검증 엔드포인트
- `GET /api/profile-stats` 추가 — 인증 없이 프로필 DB 통계 반환 (total, by_source, by_category, by_difficulty)

## 결과
- ✅ 39/39 유닛 테스트 통과
- ✅ Docker 로컬 빌드 성공 (이미지 내 2,578개 확인)
- ✅ Cloud Build 2회 성공 (fd51242, ef58720)
- ✅ 프로덕션 `/api/profile-stats` → total: 2,578

## 프로덕션 DB 현황

| 소스 | 수량 |
|---|---|
| whatsonzwift | 2,420 |
| custom (시드) | 100 |
| zwift (GitHub) | 58 |
| **합계** | **2,578** |

| 카테고리 | 수량 | Difficulty | 수량 |
|---|---|---|---|
| vo2max | 633 | advanced | 716 |
| endurance | 607 | intermediate | 1,335 |
| threshold | 475 | beginner | 527 |
| sprint | 340 | | |
| tempo | 244 | | |
| sweetspot | 185 | | |
| recovery+ | 94 | | |

## 다음 단계
- 실제 운동 생성 테스트 — LLM이 2,578개 후보에서 적절히 선택하는지 확인
- 카테고리 자동 분류 정확도 검증 — sweetspot vs threshold 경계 등
- 대규모 DB에서의 쿼리 성능 모니터링 (ORDER BY RANDOM() LIMIT 50)
- `enrich_profiles.py`를 CI/CD에 통합하여 향후 재임포트 시 자동 실행
- 프로필 중복 정리 — 같은 운동이 다른 컬렉션에 중복 존재할 수 있음
