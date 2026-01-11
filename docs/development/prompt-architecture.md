# AI Cycling Coach - 프롬프트 아키텍처

이 문서는 AI 워크아웃 생성 시 사용되는 프롬프트 구조를 설명합니다.

## 핵심 원칙

> **프롬프트 생성에 AI를 사용하지 않습니다.**  
> 모든 프롬프트는 Python 코드로 조합되며, AI 호출은 **워크아웃 생성 시 1회**뿐입니다.

---

## 프롬프트 구조

```
┌─────────────────────────────────────────┐
│           LLM.generate()                │
│  ┌─────────────┐  ┌─────────────────┐  │
│  │ System      │  │ User            │  │
│  │ Prompt      │  │ Prompt          │  │
│  │ (고정 규칙)   │  │ (동적 데이터)     │  │
│  └─────────────┘  └─────────────────┘  │
└─────────────────────────────────────────┘
```

---

## 1. System Prompt (고정)

**목적**: AI의 역할, 행동 규칙, 출력 형식 정의

**구성 요소**:
- 코치 역할 부여
- 훈련 강도 가이드라인 (TSB 기반)
- 워크아웃 문법 가이드 (시간, 파워 형식)
- JSON 출력 스키마

**위치**: `src/services/workout_generator.py` > `SYSTEM_PROMPT`

```python
SYSTEM_PROMPT = """당신은 세계적인 수준의 사이클링 코치입니다...

워크아웃 강도 가이드라인:
- TSB < -20: 회복만 (50-65%)
- TSB -20 ~ -10: 지구력 (65-75%)
- TSB > 0: Threshold/VO2max 가능

{syntax_guide}

**출력 규칙:**
```json
{
  "name": "워크아웃 이름",
  "type": "Endurance|Threshold|VO2max|Recovery",
  "tss": 예상TSS,
  "warmup": ["스텝1"],
  "main": ["스텝1", "스텝2"],
  "cooldown": ["스텝1"]
}
```
"""
```

---

## 2. User Prompt (동적)

**목적**: 실시간 데이터 + 사용자 설정 전달

**위치**: `src/services/workout_generator.py` > `USER_PROMPT_TEMPLATE`

```python
USER_PROMPT_TEMPLATE = """
선수 프로필:
- FTP: {ftp}W
- 훈련 목표: {training_goal}

현재 훈련 상태:
- CTL: {ctl:.1f}
- ATL: {atl:.1f}
- TSB: {tsb:.1f} ({form_status})

웰니스 상태:
- 준비 상태: {readiness}
{wellness_details}

오늘 날짜: {today}
요일: {weekday}

**사용자 설정:**
- 목표 시간: {max_duration}분
- 훈련 스타일: {style}
- 강도 선호: {intensity}
- 환경: {environment}
{user_notes}

위 정보를 바탕으로 워크아웃을 생성해주세요.
"""
```

---

## 3. 데이터 소스

| 데이터 | 소스 | 예시 |
|--------|------|------|
| FTP, max_hr, lthr | `.env` 설정 | 250W, 190bpm |
| CTL, ATL, TSB | Intervals.icu API | 68.1, 66.1, 2.0 |
| HRV, RHR | Intervals.icu API (Wellness) | 30, 56 |
| duration | CLI `--duration` | 60 |
| style | CLI `--style` | norwegian |
| intensity | CLI `--intensity` | hard |
| notes | CLI `--notes` | "오늘 다리가 무거워" |
| indoor | CLI `--indoor` | True/False |

---

## 4. 데이터 흐름

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Intervals.icu  │    │   CLI 인자       │    │   .env 설정      │
│     API         │    │                 │    │                 │
└────────┬────────┘    └────────┬────────┘    └────────┬────────┘
         │                      │                      │
         ▼                      ▼                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                    _build_user_prompt()                         │
│                                                                 │
│  TrainingMetrics(ctl, atl, tsb) + WellnessMetrics(hrv, rhr)    │
│  + UserProfile(ftp, max_hr) + CLI args(style, duration, ...)   │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│             USER_PROMPT_TEMPLATE.format(...)                    │
│                                                                 │
│                      완성된 User Prompt                          │
└─────────────────────────────────────────────────────────────────┘
```

---

## 5. 스타일 & 강도 설명

**스타일 매핑** (`STYLE_DESCRIPTIONS`):

| 키 | AI에게 전달되는 설명 |
|----|---------------------|
| `auto` | TSB 상태에 맞게 자동 결정 |
| `polarized` | 양극화 훈련 - 80% 쉬움 + 20% 매우 힘듦 |
| `norwegian` | 노르웨이식 - 4x8분 역치 인터벌 |
| `sweetspot` | 스윗스팟 - FTP 88-94% 긴 인터벌 |

**강도 매핑** (`INTENSITY_DESCRIPTIONS`):

| 키 | AI에게 전달되는 설명 |
|----|---------------------|
| `auto` | TSB 상태에 맞게 자동 결정 |
| `easy` | 쉬운 회복 훈련 (Z1-Z2만 사용) |
| `hard` | 높은 강도 (역치/VO2max 허용) |

---

## 6. 프롬프트 조합 함수

**위치**: `src/services/workout_generator.py`

```python
def _build_user_prompt(
    self,
    metrics: TrainingMetrics,      # CTL, ATL, TSB
    wellness: WellnessMetrics,     # HRV, RHR
    target_date: date,
    style: str = "auto",
    notes: str = "",
    intensity: str = "auto",
    indoor: bool = False,
) -> str:
    # 1. 웰니스 상세 정보 포맷
    wellness_details = [...]
    
    # 2. 스타일/강도 설명 조회
    style_desc = STYLE_DESCRIPTIONS.get(style, style)
    intensity_desc = INTENSITY_DESCRIPTIONS.get(intensity, intensity)
    
    # 3. 템플릿에 값 삽입
    return USER_PROMPT_TEMPLATE.format(
        ftp=self.profile.ftp,
        ctl=metrics.ctl,
        style=style_desc,
        ...
    )
```

---

## 7. 왜 프롬프트 생성에 AI를 쓰지 않는가?

1. **비용 절감**: AI 호출 1회 vs 2회
2. **지연 시간 감소**: 프롬프트 생성은 즉시 (< 1ms)
3. **예측 가능성**: 동일 입력 → 동일 프롬프트
4. **디버깅 용이**: 프롬프트 로깅으로 문제 추적 가능
5. **충분한 구조화**: 템플릿 + 딕셔너리로 충분히 표현 가능

---

## 파일 참조

- `src/services/workout_generator.py` - 프롬프트 템플릿 및 조합 로직
- `src/config.py` - 사용자 프로필 설정
- `src/services/data_processor.py` - TrainingMetrics, WellnessMetrics
