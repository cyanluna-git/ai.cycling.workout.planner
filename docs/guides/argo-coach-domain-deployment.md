# Coach custom-domain deployment — 2026-10-29

Frontend: https://argo-coach.cyanluna.com/ ; original Vercel alias retained. Coach backend: cycling-coach-backend, GCP gen-lang-client-0043735738, asia-northeast3. This is separate from ARGO Intervals MCP project agro-project-511007.

## Current nonsecret configuration
INTERVALS_OAUTH_REDIRECT_URI=https://argo-coach.cyanluna.com/auth/callback

Applied only this environment key via Cloud Run --update-env-vars, without source rebuild. Current revision cycling-coach-backend-oauth-argo-20261029, 100% traffic. CORS-patched image remains sha256:cfb8b5ca9c8b300239564fdd966a5cb45e5f2a1a194519b4fcec41cd9143d02d. Previous revision cycling-coach-backend-cors-argo-20261029; old callback https://ai-cycling-workout-planner.vercel.app/auth/callback.

User reported registering new callback in Intervals client234. Logged-out provider request returned 403; independent admin allowlist acceptance and real login/consent are not verified. This client is documented as shared with ARGO Intervals MCP: preserve all old/MCP callbacks and scopes; do not alter the separate MCP deployment/app.

Supabase wlwvxqicvceelqtyydbc verified return list retains https://ai-cycling-workout-planner.vercel.app/** and adds exact https://argo-coach.cyanluna.com plus https://argo-coach.cyanluna.com/reset-password. Site URL remains https://ai-cycling-workout-planner.vercel.app.

## Preserve on future deployment
Existing cloudbuild.yaml image deployment does not set callback env and should retain it. Avoid replacing all environment variables; preserve new callback and unrelated env. CORS one-line source fix is durably remote in draft PR https://github.com/cyanluna-git/ai.cycling.workout.planner/pull/11, not merged. Retain it before future main source deployment so an image-only patch is not lost. Do not deploy unrelated local WIP.

## Verified and untested
Readback matches callback; image/service account/concurrency/timeout/resources unchanged. Exact source authorize-URL builder tested with fake state persistence and live nonsecret callback value; no live authenticated endpoint or user DB write. Coach /api/health and new frontend callback route 200. Old/new CORS origins 200; unrelated origin 400. Separate ARGO MCP /health200 and unauth /mcp401. No consent/token exchange, health records, password-reset email or account data used.

Remaining user E2E: sign in to Coach, confirm new-host return, connect Intervals with personal consent and confirm callback routing. Public HTTP200 is not proof of successful login.

## Rollback
If approved, route traffic to cycling-coach-backend-cors-argo-20261029 (retains CORS with previous callback), or update only INTERVALS_OAUTH_REDIRECT_URI to the old Vercel callback. Do not restore a pre-CORS image accidentally. Preserve provider added URLs unless separately asked to remove them. No rollback performed.
