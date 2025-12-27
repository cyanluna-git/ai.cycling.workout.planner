# AI Cycling Coach 🚴‍♂️

AI 기반 사이클링 워크아웃 추천 및 Intervals.icu 자동 동기화 서비스

## 🌐 배포 URL

| 서비스 | URL |
|--------|-----|
| **Frontend** | https://ai-cycling-workout-planner.vercel.app |
| **Backend API** | https://ai-cycling-workout-planner.onrender.com |

## ✨ 주요 기능

- **AI 워크아웃 생성**: CTL/ATL/TSB와 Wellness 데이터 기반 맞춤 워크아웃
- **Intervals.icu 연동**: ZWO 형식으로 정확한 워크아웃 구조 전송
- **Wahoo 동기화**: Intervals.icu에서 Wahoo 장치로 자동 전송
- **훈련 스타일 선택**: 양극화, 노르웨이, 스윗스팟 등 다양한 스타일 지원
- **React 웹 UI**: 브라우저에서 직접 워크아웃 생성 및 등록
- **멀티유저 인증**: Supabase 기반 Google OAuth 및 이메일 로그인

## 🏗️ 아키텍처

```
┌─────────────────┐     HTTP     ┌─────────────────┐     API      ┌─────────────────┐
│   React.js      │ ──────────▶  │    FastAPI      │ ──────────▶  │  Intervals.icu  │
│   (Vercel)      │              │   (Render)      │              │      API        │
└─────────────────┘              └────────┬────────┘              └─────────────────┘
                                          │
                              ┌───────────┴───────────┐
                              ▼                       ▼
                       ┌─────────────┐         ┌─────────────┐
                       │  Groq/LLM   │         │  Supabase   │
                       └─────────────┘         └─────────────┘
```

## 🚀 빠른 시작

### 방법 1: 로컬 실행 (권장)

```bash
# 1. 저장소 클론
git clone https://github.com/your-repo/ai-cycling-workout-planner.git
cd ai-cycling-workout-planner

# 2. Python 가상환경 설정
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 3. 의존성 설치
pip install -r requirements.txt
cd frontend && pnpm install && cd ..

# 4. 환경 변수 설정
cp .env.example .env
# .env 파일을 편집하여 API 키 입력

# 5. 실행
python run.py
```

### 방법 2: Docker 실행

```bash
# 환경 변수 설정
cp .env.example .env
# .env 파일 편집

# Docker Compose로 실행
docker-compose up --build
```

### 실행 스크립트 (run.py)

```bash
# 백엔드 + 프론트엔드 동시 실행
python run.py

# 백엔드만 실행
python run.py backend

# 프론트엔드만 실행
python run.py frontend

# Docker로 실행
python run.py --docker
```

**기본 포트:**
- Backend: `http://localhost:8005`
- Frontend: `http://localhost:3005`
- API Docs: `http://localhost:8005/docs`

## ⚙️ 환경 변수 설정

`.env.example`을 `.env`로 복사 후 편집:

```bash
# 서버 포트
BACKEND_PORT=8005
FRONTEND_PORT=3005
DEBUG=true

# Supabase (필수)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key

# Intervals.icu (사용자별 설정 페이지에서 입력)
INTERVALS_API_KEY=your-api-key
ATHLETE_ID=i123456

# LLM (하나 이상 필수)
LLM_PROVIDER=groq
GROQ_API_KEY=your-groq-key
```

## 🧠 AI "오마카세" 로직

이 서비스는 AI가 워크아웃을 처음부터 창작하지 않고, **검증된 워크아웃 모듈 메뉴판**에서 최적의 코스를 선택합니다.

1. **메뉴판 (Library)**: 검증된 워밍업, 메인 본운동, 쿨다운 모듈이 미리 정의됨
2. **지능적 선택 (AI Selector)**: TSB와 목표 시간을 분석하여 최적 모듈 조합 선택
3. **정확한 조립 (Assembler)**: ZWO 형식으로 변환하여 Intervals.icu에 등록

## 📁 프로젝트 구조

```
aiworkout.planner/
├── api/                    # FastAPI 백엔드
│   ├── main.py             # API 진입점
│   ├── routers/            # API 라우터
│   └── services/           # 비즈니스 로직
├── frontend/               # React 프론트엔드
│   ├── src/
│   │   ├── components/     # UI 컴포넌트
│   │   ├── hooks/          # 커스텀 훅
│   │   ├── lib/            # 유틸리티
│   │   └── pages/          # 페이지 컴포넌트
├── src/                    # 핵심 서비스
│   ├── clients/            # 외부 API 클라이언트
│   ├── services/           # 워크아웃 생성 로직
│   ├── data/               # 워크아웃 모듈 데이터
│   └── utils/              # 유틸리티
├── docs/                   # 문서
├── tests/                  # 테스트
├── run.py                  # 통합 실행 스크립트
├── docker-compose.yml      # Docker 설정
└── requirements.txt        # Python 의존성
```

## 🎯 훈련 스타일

| 스타일 | 설명 |
|--------|------|
| `auto` | TSB 상태에 맞게 자동 결정 |
| `polarized` | 양극화 - 80% 쉬움 + 20% 매우 힘듦 |
| `norwegian` | 노르웨이식 - 4x8분 역치 인터벌 |
| `threshold` | 역치 중심 - FTP 95-105% |
| `sweetspot` | 스윗스팟 - FTP 88-94% |
| `endurance` | 지구력 - Z2 장거리 |

## 🧪 테스트

```bash
pytest tests/ -v
```

## 📝 문서

- [아키텍처](docs/ARCHITECTURE.md)
- [배포 가이드](docs/DEPLOYMENT.md)
- [프롬프트 구조](docs/PROMPT_ARCHITECTURE.md)
- [요구사항 명세](docs/SRS.md)

## 📄 라이선스

MIT License
