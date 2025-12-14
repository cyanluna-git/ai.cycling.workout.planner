# AI Cycling Coach 🚴‍♂️

AI 기반 사이클링 워크아웃 추천 및 Intervals.icu 자동 동기화 서비스

## 🌐 배포 URL

| 서비스 | URL |
|--------|-----|
| **Frontend** | https://ai-cycling-workout-planner.vercel.app |
| **Backend API** | https://ai-cycling-workout-planner.onrender.com |

## 기능

- **자동 워크아웃 생성**: CTL/ATL/TSB와 Wellness 데이터 기반 AI 맞춤 워크아웃
- **Intervals.icu 연동**: API를 통한 캘린더 자동 등록
- **Wahoo 동기화**: Intervals.icu에서 Wahoo 장치로 자동 전송
- **훈련 스타일 선택**: 양극화, 노르웨이, 스윗스팟 등 다양한 스타일 지원
- **React 웹 UI**: 브라우저에서 직접 워크아웃 생성 및 등록
- **스케줄러**: 매일 지정 시간에 자동 실행

## 아키텍처

```
┌─────────────────┐     HTTP     ┌─────────────────┐     API      ┌─────────────────┐
│   React.js      │ ──────────▶  │    FastAPI      │ ──────────▶  │  Intervals.icu  │
│   (Vercel)      │              │   (Render)      │              │      API        │
└─────────────────┘              └────────┬────────┘              └─────────────────┘
                                          │
                                          ▼
                                   ┌─────────────────┐
                                   │   Gemini API    │
                                   └─────────────────┘
```

## 빠른 시작

### 1. 설치

```bash
cd /Users/cyanluna-pro16/Documents/0.Dev/aiworkout.planner
pip install -e ".[dev]"
```

### 2. 설정

```bash
cp .env.example .env
# .env 파일을 편집하여 API 키 입력
```

필수 설정:
- `INTERVALS_API_KEY`: [Intervals.icu 설정](https://intervals.icu/settings)에서 발급
- `ATHLETE_ID`: 본인의 Athlete ID (예: i12345)
- `LLM_API_KEY`: OpenAI/Anthropic/Gemini API 키
- `LLM_PROVIDER`: `openai`, `anthropic`, `gemini` 중 선택

---

## CLI 사용법

### 기본 명령어

```bash
python -m src.main [옵션]
```

### 전체 옵션

| 옵션 | 설명 | 기본값 |
|------|------|--------|
| `--date DATE` | 워크아웃 생성 날짜 (YYYY-MM-DD) | 오늘 |
| `--dry-run` | 실제 등록 없이 미리보기만 | - |
| `--force` | 기존 워크아웃 삭제 후 새로 생성 | - |
| `--duration N` | 목표 운동 시간 (분) | 60 |
| `--style STYLE` | 훈련 스타일 | auto |
| `--intensity LEVEL` | 강도 선호 | auto |
| `--notes "..."` | AI에게 추가 요청 | - |
| `--indoor` | 실내 트레이너 모드 | - |

### 훈련 스타일 (--style)

| 스타일 | 설명 |
|--|------|------|
| `auto` | TSB 상태에 맞게 자동 결정 |
| `polarized` | 양극화 - 80% 쉬움 + 20% 매우 힘듦 |
| `norwegian` | 노르웨이식 - 4x8분 역치 인터벌 |
| `pyramidal` | 피라미드 - Z1-Z2 기반, Z3-Z4 추가 |
| `threshold` | 역치 중심 - FTP 95-105% |
| `sweetspot` | 스윗스팟 - FTP 88-94% |
| `endurance` | 지구력 - Z2 장거리 

### 강도 선호 (--intensity)

| 강도 | 설명 |
|------|------|
| `auto` | TSB 상태에 맞게 자동 결정 |
| `easy` | 회복 훈련 (Z1-Z2만) |
| `moderate` | 적당한 강도 (템포/스윗스팟) |
| `hard` | 높은 강도 (역치/VO2max) |

---

## 테스트 예제 🧪

### 1. 기본 실행 (미리보기)
```bash
python -m src.main --dry-run
```

### 2. 내일 워크아웃 생성
```bash
python -m src.main --date 2025-12-15
```

### 3. 45분 짧은 워크아웃
```bash
python -m src.main --duration 45 --dry-run
```

### 4. 노르웨이식 역치 훈련
```bash
python -m src.main --style norwegian --intensity hard --dry-run
```

### 5. 양극화 훈련 (긴 지구력)
```bash
python -m src.main --duration 90 --style polarized --dry-run
```

### 6. 스윗스팟 인터벌
```bash
python -m src.main --style sweetspot --dry-run
```

### 7. 실내 트레이너 워크아웃
```bash
python -m src.main --indoor --duration 60 --dry-run
```

### 8. 사용자 요청 추가
```bash
python -m src.main --notes "오늘 다리가 무거워서 쉽게" --intensity easy --dry-run
```

### 9. 기존 워크아웃 대체
```bash
python -m src.main --date 2025-12-15 --force
```

### 10. 종합 예제
```bash
python -m src.main --date 2025-12-16 --duration 60 --style norwegian --intensity hard --indoor --notes "클라이밍 준비"
```

---

## 데이터 확인 (CLI 뷰어)

```bash
# 선수 프로필
python -m src.cli profile

# 최근 활동
python -m src.cli activities

# 훈련 상태 (CTL/ATL/TSB)
python -m src.cli fitness

# 웰니스 데이터
python -m src.cli wellness

# 캘린더 이벤트
python -m src.cli calendar
```

---

## 스케줄러 (매일 자동 실행)

```bash
# 매일 오전 6시 실행
python -m src.scheduler

# 지정 시간에 실행
python -m src.scheduler --time 05:30

# 즉시 실행 후 스케줄러 시작
python -m src.scheduler --run-now
```

---

## 프로젝트 구조

```
src/
├── main.py              # 메인 진입점
├── config.py            # 환경 변수 관리
├── cli.py               # 데이터 뷰어
├── scheduler.py         # 일일 스케줄러
├── clients/
│   ├── intervals.py     # Intervals.icu API 클라이언트
│   └── llm.py           # LLM 클라이언트 (OpenAI/Anthropic/Gemini)
└── services/
    ├── data_processor.py    # CTL/ATL/TSB 계산
    ├── workout_generator.py # AI 워크아웃 생성
    └── validator.py         # 워크아웃 텍스트 검증
```

## 테스트

```bash
pytest tests/ -v
```

## 라이선스

MIT License
