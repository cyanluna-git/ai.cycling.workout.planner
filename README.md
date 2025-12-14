# AI Cycling Coach 🚴‍♂️

AI 기반 사이클링 워크아웃 추천 및 Intervals.icu 자동 동기화 서비스

## 기능

- **자동 워크아웃 생성**: CTL/ATL/TSB와 Wellness 데이터 기반 AI 맞춤 워크아웃
- **Intervals.icu 연동**: API를 통한 캘린더 자동 등록
- **Wahoo 동기화**: Intervals.icu에서 Wahoo 장치로 자동 전송
- **스케줄러**: 매일 지정 시간에 자동 실행

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

### 3. 실행

```bash
# 오늘의 워크아웃 생성
python -m src.main

# 테스트 (실제 등록 없이)
python -m src.main --dry-run

# 특정 날짜
python -m src.main --date 2024-12-20

# 기존 워크아웃 덮어쓰기
python -m src.main --force
```

### 4. 스케줄러 (선택사항)

```bash
# 매일 오전 6시 실행
python -m src.scheduler

# 지정 시간에 실행
python -m src.scheduler --time 05:30

# 즉시 실행 후 스케줄러 시작
python -m src.scheduler --run-now
```

## 프로젝트 구조

```
src/
├── main.py              # 메인 진입점
├── config.py            # 환경 변수 관리
├── scheduler.py         # 일일 스케줄러
├── clients/
│   ├── intervals.py     # Intervals.icu API 클라이언트
│   └── llm.py           # LLM 클라이언트 (OpenAI/Anthropic/Gemini)
└── services/
    ├── data_processor.py    # CTL/ATL/TSB 계산
    ├── workout_generator.py # AI 워크아웃 생성
    └── validator.py         # 워크아웃 텍스트 검증
```

## API 연결 테스트

```bash
python -c "
from src.config import load_config
from src.clients.intervals import IntervalsClient

config = load_config()
client = IntervalsClient(config.intervals)
profile = client.get_athlete_profile()
print(f'Connected! FTP: {profile.get(\"icu_ftp\")}W')
"
```

## 테스트

```bash
pytest tests/ -v
```

## 라이선스

MIT License
