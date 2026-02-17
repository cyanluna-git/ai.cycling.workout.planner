#!/bin/bash
# Activate project-local tools (gcloud, supabase, vercel)

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TOOLS_BIN="$PROJECT_ROOT/tools/bin"
GOOGLE_CLOUD_SDK="$PROJECT_ROOT/tools/google-cloud-sdk"
NODE_MODULES="$PROJECT_ROOT/node_modules/.bin"

# Add tools to PATH (prioritize project-local)
export PATH="$NODE_MODULES:$TOOLS_BIN:$GOOGLE_CLOUD_SDK/bin:$PATH"

# Set Google Cloud SDK home
export CLOUDSDK_ROOT_DIR="$GOOGLE_CLOUD_SDK"

echo "✅ ai.cycling.workout.planner tools activated"
echo "   - gcloud: $GOOGLE_CLOUD_SDK/bin/gcloud"
echo "   - supabase: $TOOLS_BIN/supabase"
echo "   - vercel: $NODE_MODULES/vercel"
