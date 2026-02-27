# Project-Local Tools Setup

이 프로젝트는 **gcloud**, **supabase** CLI를 프로젝트 폴더 내에 격리하여 설치합니다.
다른 프로젝트와 버전 충돌 없이 독립적으로 운영됩니다.

## 📍 디렉토리 구조

```
ai.cycling.workout.planner/
├── tools/
│   ├── activate.sh                    # 환경 변수 설정 스크립트
│   ├── bin/
│   │   └── supabase                   # Supabase CLI (2.75.0)
│   └── google-cloud-sdk/
│       └── bin/gcloud                 # Google Cloud SDK (556.0.0)
```

## 🚀 사용 방법

### 1️⃣ 단일 명령어 (권장)

```bash
cd /home/cyanluna-jarvis/ai.cycling.workout.planner
source tools/activate.sh
gcloud auth list
supabase status
```

### 2️⃣ 직접 경로 지정

```bash
/home/cyanluna-jarvis/ai.cycling.workout.planner/tools/google-cloud-sdk/bin/gcloud --version
/home/cyanluna-jarvis/ai.cycling.workout.planner/tools/bin/supabase --version
```

### 3️⃣ Docker 내부에서 (compose.yml에서)

```yaml
services:
  backend:
    environment:
      - PATH=/app/tools/bin:/app/tools/google-cloud-sdk/bin:$PATH
```

## 📋 설치된 버전

| Tool | Version | Path |
|------|---------|------|
| gcloud | 556.0.0 | `tools/google-cloud-sdk/bin/gcloud` |
| supabase | 2.75.0 | `tools/bin/supabase` |

## ⚙️ 버전 업데이트

향후 새 버전 필요 시:

```bash
# 기존 도구 제거
rm -rf tools/bin/supabase tools/google-cloud-sdk

# 새 버전 설치 (시스템에서)
# 설치 후 본 프로젝트에 복사
cp /path/to/new/supabase tools/bin/
cp -r /path/to/new/google-cloud-sdk tools/
```

## 🔒 격리 이유

- **버전 독립성**: 다른 프로젝트와 버전 충돌 없음
- **재현성**: 팀원이 같은 버전 사용 보장
- **관리 용이**: 프로젝트별 도구 관리

## 📝 주의사항

- `tools/` 폴더는 `.gitignore`에 포함되어 있습니다 (큰 용량)
- 새로운 팀원이 추가될 때, `tools/activate.sh` 스크립트를 실행하도록 안내하세요
- `activate.sh`는 git에 커밋됩니다 (다른 팀원도 같은 방식으로 사용 가능)

