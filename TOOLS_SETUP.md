# Project-Local Tools Setup

이 프로젝트는 **gcloud**, **supabase**, **vercel** CLI를 프로젝트 폴더 내에 격리하여 설치합니다.
다른 프로젝트와 버전 충돌 없이 독립적으로 운영됩니다.

## 📍 디렉토리 구조

```
ai.cycling.workout.planner/
├── node_modules/
│   └── .bin/
│       └── vercel                    # Vercel CLI (50.18.0)
├── tools/
│   ├── activate.sh                   # 환경 변수 설정 스크립트
│   ├── bin/
│   │   └── supabase                  # Supabase CLI (2.75.0)
│   └── google-cloud-sdk/
│       └── bin/gcloud                # Google Cloud SDK (556.0.0)
└── package.json
    └── devDependencies.vercel: ^50.18.0
```

## 🚀 사용 방법

### 1️⃣ 단일 명령어 (권장)

```bash
cd /home/cyanluna-jarvis/ai.cycling.workout.planner
source tools/activate.sh

# 이제 모든 CLI 사용 가능
gcloud auth list
supabase status
vercel projects list
```

### 2️⃣ npx로 Vercel 직접 실행 (activate.sh 불필요)

```bash
cd /home/cyanluna-jarvis/ai.cycling.workout.planner
npx vercel --version
npx vercel projects list
npx vercel deployments
```

### 3️⃣ npm scripts로 관리 (package.json)

```json
{
  "scripts": {
    "vercel:login": "vercel login",
    "vercel:list": "vercel projects list",
    "vercel:deploy": "vercel deploy --prod",
    "vercel:env": "vercel env ls",
    "vercel:logs": "vercel logs --follow"
  }
}
```

사용:
```bash
npm run vercel:list
npm run vercel:deploy
```

### 4️⃣ 직접 경로 지정

```bash
/home/cyanluna-jarvis/ai.cycling.workout.planner/tools/google-cloud-sdk/bin/gcloud --version
/home/cyanluna-jarvis/ai.cycling.workout.planner/tools/bin/supabase --version
/home/cyanluna-jarvis/ai.cycling.workout.planner/node_modules/.bin/vercel --version
```

### 5️⃣ Docker 내부에서 (compose.yml에서)

```yaml
services:
  backend:
    environment:
      - PATH=/app/tools/bin:/app/tools/google-cloud-sdk/bin:/app/node_modules/.bin:$PATH
```

## 📋 설치된 버전

| Tool | Version | Path | 설치 방식 |
|------|---------|------|---------|
| gcloud | 556.0.0 | `tools/google-cloud-sdk/bin/gcloud` | 바이너리 (격리) |
| supabase | 2.75.0 | `tools/bin/supabase` | 바이너리 (격리) |
| vercel | 50.18.0 | `node_modules/.bin/vercel` | npm (package.json) |

## ⚙️ 버전 업데이트

### gcloud / supabase (바이너리)

```bash
# 기존 도구 제거
rm -rf tools/bin/supabase tools/google-cloud-sdk

# 새 버전 설치 (시스템에서)
# 설치 후 본 프로젝트에 복사
cp /path/to/new/supabase tools/bin/
cp -r /path/to/new/google-cloud-sdk tools/
```

### vercel (npm 패키지)

```bash
cd /home/cyanluna-jarvis/ai.cycling.workout.planner
npm install -D vercel@latest   # 최신 버전으로 업데이트
npm update vercel              # 마이너 업데이트
```

## 🔒 격리 이유

- **버전 독립성**: 다른 프로젝트와 버전 충돌 없음
- **재현성**: 팀원이 같은 버전 사용 보장
- **관리 용이**: 프로젝트별 도구 관리

## 🎮 Vercel CLI 주요 명령어

```bash
# 계정 인증
npx vercel login

# 프로젝트 관리
npx vercel projects list              # 모든 Vercel 프로젝트 조회
npx vercel projects add               # 새 프로젝트 추가

# 배포 현황
npx vercel deployments                # 배포 히스토리 조회
npx vercel deployments list --limit 10 # 최근 10개 배포

# 환경 변수
npx vercel env ls                     # 환경 변수 조회
npx vercel env pull                   # 환경 변수 로컬 저장 (.env.local)
npx vercel env set KEY VALUE          # 환경 변수 설정
npx vercel env add                    # 대화형 환경 변수 추가

# 배포
npx vercel deploy                     # Preview 배포
npx vercel deploy --prod              # Production 배포

# 로그 및 모니터링
npx vercel logs --follow              # 실시간 로그 보기
npx vercel logs --tail                # 최근 로그 조회

# 도메인 관리
npx vercel domains ls                 # 도메인 목록
npx vercel domains add                # 도메인 추가
```

## 📝 주의사항

- `tools/` 폴더는 `.gitignore`에 포함되어 있습니다 (큰 용량)
- `node_modules/`는 `.gitignore`에 자동 포함됨 (npm 패키지)
- 새로운 팀원이 추가될 때:
  1. `npm install` → vercel 자동 설치 (package.json 기반)
  2. `source tools/activate.sh` → 다른 CLI 활성화
  3. `npx vercel login` → Vercel 계정 연동
- `activate.sh`는 git에 커밋됩니다 (다른 팀원도 같은 방식으로 사용 가능)

