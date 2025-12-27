#!/bin/bash

# 1. 루트 .env 파일이 있는지 확인 및 로드
if [ -f .env ]; then
    echo "📝 Syncing environment variables from root .env to frontend..."
    
    # 루트 .env에서 값을 추출하여 VITE_ 접두사와 함께 export
    export VITE_SUPABASE_URL=$(grep "^SUPABASE_URL=" .env | cut -d'=' -f2-)
    export VITE_SUPABASE_ANON_KEY=$(grep "^SUPABASE_ANON_KEY=" .env | cut -d'=' -f2-)
    
    # 백엔드 API 주소 설정 (로컬 백엔드 기본값)
    export VITE_API_URL="http://localhost:8000"
    
    echo "✅ Environment variables exported"
else
    echo "⚠️ Root .env file not found"
fi

# 2. 프론트엔드 디렉토리로 이동하여 실행
echo "🚀 Starting Frontend..."
cd frontend && pnpm run dev
