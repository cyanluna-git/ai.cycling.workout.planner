[개발 사양서] AI 기반 사이클링 워크아웃 추천 및 자동 동기화 서비스
1. 프로젝트 개요
프로젝트명: AI Cycling Coach (가칭)

목표: 사용자 데이터를 기반으로 AI가 매일 최적의 워크아웃을 생성하여 Intervals.icu 캘린더에 등록, Wahoo Bolt2에서 즉시 실행 가능하게 함.

핵심 가치: 훈련 부하(Training Load)와 회복 상태(Wellness)를 고려한 동적 플랜 제공 및 플랫폼 간 자동화.

2. 시스템 아키텍처
Backend: Python 3.10+ (단일 서비스 또는 마이크로서비스 구조)

External APIs:

Intervals.icu API: 데이터 조회 및 워크아웃 등록

LLM API (OpenAI/Anthropic/Gemini): 데이터 분석 및 워크아웃 텍스트 생성

Database (Optional): 초기에는 로컬 JSON/SQLite 파일로 상태 관리 (MVP 단계), 추후 DB 도입.

Scheduler: Python schedule 라이브러리 또는 Cron (매일 새벽 실행).

3. 상세 기능 명세 (Functional Requirements)
3.1. 인증 및 사용자 관리 (Authentication)
API Key 방식: Intervals.icu 설정 페이지에서 발급받은 API Key를 .env 파일로 관리.

API_KEY: Intervals.icu API Key

ATHLETE_ID: 사용자 ID (API 호출 시 필요)

보안: API Key는 소스코드에 하드코딩하지 않고 환경 변수로 관리.

3.2. 데이터 수집 (Data Ingestion)
최근 활동 조회 (Activities):

지난 42일(6주)간의 라이딩 데이터 조회 (TSS, IF, 시간, 파워 커브 등).

목적: 현재의 Fitness(CTL), Fatigue(ATL), Form(TSB) 추세 파악.

건강 데이터 조회 (Wellness):

최근 7일간의 HRV, 안정시 심박수(RHR), 수면 시간, 기분(Soreness/Fatigue) 조회.

목적: 당일 훈련 가능 강도 판단.

기존 캘린더 일정 확인:

오늘 및 향후 7일간 이미 등록된 이벤트나 레이스 일정이 있는지 확인 (중복 생성 방지).

3.3. AI 분석 및 워크아웃 생성 (Core Logic)
Input (Prompt Context):

사용자 프로필 (FTP, Max HR, LTHR).

최근 부하 데이터 (CTL, TSB).

어제 Wellness 데이터.

사용자의 장기 목표 (예: "3개월 뒤 그란폰도 대비, 지구력 강화").

Processing (AI Agent):

TSB가 매우 낮음(-20 이하) → Recovery Ride 추천.

TSB가 적절하고 주중 → Interval (VO2max or Threshold) 추천.

주말 → Endurance (LSD) 추천.

Output (Format):

Intervals.icu 워크아웃 빌더 텍스트 포맷 (DSL) 생성.

예: 10m 50% (10분간 FTP 50%로 웜업).

3.4. Intervals.icu 캘린더 등록 (Automation)
워크아웃 변환: AI가 생성한 텍스트를 Intervals.icu API의 Event 객체 구조로 변환.

등록 실행: 해당 날짜에 WORKOUT 카테고리로 이벤트 생성.

Wahoo 동기화: Intervals.icu에 등록되면 Wahoo 클라우드가 자동으로 데이터를 가져가므로, "Plan workout on calendar" 단계까지만 성공하면 Wahoo 연동은 완료된 것으로 간주.

4. Intervals.icu API 연동 가이드
Intervals.icu API 문서를 기반으로 Python requests를 사용한 주요 구현 포인트입니다.

4.1. Base URL & Headers
Python

BASE_URL = "https://intervals.icu/api/v1"
HEADERS = {
    "Authorization": "Basic <BASE64_ENCODED_API_KEY_AND_USER>",
    "Content-Type": "application/json"
}
# 주의: API Key는 'API_KEY:user' 형태가 아니라 Basic Auth 헤더 처리 필요
# requests 사용 시 auth=('API_KEY', 'g') 형태로 전달 (username='API_KEY', password='g')
4.2. 주요 엔드포인트
운동 데이터 조회 (Activities):

GET /athlete/{id}/activities?oldest=YYYY-MM-DD&newest=YYYY-MM-DD

필요 데이터: icu_training_load, icu_intensity

Wellness 데이터 조회:

GET /athlete/{id}/wellness?oldest=YYYY-MM-DD&newest=YYYY-MM-DD

필요 데이터: hrv, restingHR, sleepSecs

워크아웃(이벤트) 등록:

POST /athlete/{id}/events

Payload 예시:

JSON

{
  "category": "WORKOUT",
  "start_date_local": "2025-12-15T00:00:00",
  "name": "AI Generated - VO2 Max Intervals",
  "description": "AI가 분석한 오늘의 추천 워크아웃입니다.\n\n- Warmup 15m 50%\n- 5x 3m 115% 3m 50%\n- Cooldown 15m 50%",
  "type": "Ride",
  "moving_time": 3600  // 초 단위 예상 시간
}
중요: description 필드에 Intervals.icu 포맷의 워크아웃 텍스트를 넣으면 자동으로 파싱되어 그래프와 구간이 생성됩니다. 이것이 Wahoo 장치에서 인식하는 핵심입니다.

5. AI 로직 설계 및 주요 고려사항
5.1. AI 모델 프롬프트 설계 전략 (System Prompt)
AI에게 단순한 텍스트 생성이 아닌, 구조화된 코치 역할을 부여해야 합니다.

Role: 당신은 엘리트 사이클링 코치입니다. Context: 선수의 FTP는 250W입니다. 어제 TSB는 -5로 훈련하기 좋은 상태입니다. Constraint:

Intervals.icu workout text syntax를 엄격히 준수할 것. (예: Duration Power% 또는 Duration Zone).

복잡한 설명 대신 실행 가능한 step만 출력할 것.

총 시간은 60분을 넘지 말 것. Task: VO2max 인터벌 워크아웃 텍스트를 생성하세요.

5.2. 환각(Hallucination) 방지 및 유효성 검사
파싱 오류 방지: AI가 생성한 텍스트가 Intervals.icu 문법에 맞는지 1차 정규식(Regex) 검증 필요. (예: 숫자 뒤에 m, s 등의 단위가 있는지 확인).

강도 제한: "FTP 200%로 10분" 같은 불가능한 훈련을 제안하지 않도록, 프롬프트 내에 Max Power Limit 설정 (예: "Zone 5는 최대 5분까지만 설정").

5.3. Wahoo Bolt2 연동 시 주의사항
파일 형식: Intervals.icu는 캘린더 이벤트를 Wahoo에 전송할 때 자동으로 변환하지만, 워크아웃 내용이 "Structured Workout" 문법이어야만 Bolt2에서 LED 가이드와 파워 타겟이 뜹니다. 단순히 텍스트 설명만 적으면 장치에서는 메모만 보입니다.

동기화 타이밍: API로 등록 직후 Wahoo 앱이나 기기에서 동기화(Wifi Sync)를 수행해야 반영됩니다.

5.4. 에러 처리 및 로그
API Rate Limit: 429 에러 발생 시 Exponential Backoff 알고리즘으로 재시도 로직 구현.

중복 등록 방지: 스크립트가 여러 번 실행되더라도 같은 날짜에 워크아웃이 중복 생성되지 않도록, 해당 날짜의 이벤트를 먼저 조회(GET)한 후 없을 때만 생성(POST)하거나 수정(PUT)하도록 구현.

6. 개발 로드맵 제안 (AI Coding Agent 활용)
Gerald님이 AI 코딩 에이전트를 사용하신다면, 아래 순서대로 프롬프트를 주어 개발을 진행하는 것을 추천합니다.

Phase 1: API 래퍼(Wrapper) 구현

"Intervals.icu API 문서를 참조하여 get_activities, get_wellness, create_workout 함수가 포함된 IntervalsClient 클래스를 Python으로 작성해줘. requests 라이브러리를 사용하고 Basic Auth를 적용해."

Phase 2: 데이터 전처리 로직

"지난 42일간의 활동 데이터를 받아서 현재의 CTL, ATL, TSB 값을 계산하거나 추출하는 함수를 만들어줘."

Phase 3: AI 프롬프트 엔지니어링 및 연동

"수집된 데이터를 바탕으로 OpenAI API(혹은 사용하시는 LLM)에 보낼 프롬프트 템플릿을 작성해줘. 출력은 Intervals.icu 워크아웃 텍스트 포맷이어야 해."

Phase 4: 메인 로직 및 스케줄러

"매일 아침 6시에 실행되어 위 함수들을 순차적으로 호출하는 main.py를 작성해. 로그는 파일로 저장되도록 해."

이 사양서를 바탕으로 개발을 시작하신다면, 가장 먼저 Intervals.icu의 API Key를 발급받고 간단한 'Hello World' (내 프로필 정보 가져오기)부터 성공하시는 것이 좋습니다.

api doc : https://intervals.icu/api-docs.html