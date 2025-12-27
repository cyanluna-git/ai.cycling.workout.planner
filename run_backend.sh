#!/bin/bash

# 1. .env 파일의 환경 변수 로드
if [ -f .env ]; then
    echo "📝 Loading environment variables from .env..."
    # 주석 제외하고 export
    export $(grep -v '^#' .env | xargs)
else
    echo "⚠️ .env file not found"
fi

# 2. 가상환경 활성화 (있는 경우)
if [ -d ".venv" ]; then
    source ".venv/bin/activate"
fi

# 3. PYTHONPATH 설정 (api 패키지를 찾기 위함)
export PYTHONPATH=$PYTHONPATH:$(pwd)

# 4. 백엔드 실행
echo "🚀 Starting AI Cycling Coach Backend..."
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000