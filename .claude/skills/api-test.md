# api-test

API 엔드포인트를 테스트하고 캐시 동작을 검증합니다.

## Usage

```bash
/api-test [endpoint] [--method METHOD] [--with-cache]
```

## Arguments

- `endpoint` - 테스트할 API 엔드포인트 (예: `/api/fitness`)
- `--method` - HTTP 메소드 (default: GET)
- `--with-cache` - 캐시 동작 테스트 포함

## What it does

1. **엔드포인트 테스트**
   - API 호출 실행
   - 응답 시간 측정
   - 상태 코드 확인

2. **캐시 동작 검증** (--with-cache 옵션 시)
   - 첫 번째 요청 (Cache MISS)
   - 두 번째 요청 (Cache HIT)
   - 응답 시간 비교
   - refresh=true로 강제 갱신 테스트

3. **로그 분석**
   - 캐시 HIT/MISS 로그 확인
   - 캐시 무효화 로그 확인

## Examples

### Basic Test
```bash
/api-test /api/fitness
```

Output:
```
🧪 Testing: GET /api/fitness

✅ Status: 200 OK
⏱️  Response Time: 1.2s
📦 Response Size: 2.4 KB

{
  "training": { "ctl": 65.2, "atl": 58.1, "tsb": 7.1 },
  "wellness": { "readiness": "Good", ... }
}
```

### Cache Behavior Test
```bash
/api-test /api/fitness --with-cache
```

Output:
```
🧪 Testing Cache Behavior: GET /api/fitness

1️⃣ First Request (Cache MISS)
   ⏱️  Response Time: 1.8s
   📋 Cache: MISS (fetched from Intervals.icu)

2️⃣ Second Request (Cache HIT)
   ⏱️  Response Time: 0.05s
   📋 Cache: HIT (36x faster!)
   ✅ Data matches first request

3️⃣ Force Refresh (refresh=true)
   ⏱️  Response Time: 1.7s
   📋 Cache: Bypassed
   ✅ Fresh data fetched

📊 Summary:
   - Cache working correctly ✅
   - TTL: 2 hours
   - Cache Key: fitness:complete
```

### Test After Modification
```bash
# Generate a plan
/api-test /api/plans/weekly/generate --method POST

# Check if cache was cleared
/api-test /api/fitness --with-cache
```

Output:
```
🧪 Testing: POST /api/plans/weekly/generate

✅ Status: 200 OK
📋 Cache Cleared: calendar, fitness:complete, fitness:training, fitness:wellness

---

🧪 Testing Cache Behavior: GET /api/fitness

1️⃣ First Request (Cache MISS)
   ⏱️  Response Time: 1.9s
   ✅ Cache was properly invalidated!
```

## Implementation

```python
import httpx
import time
from rich.console import Console
from rich.table import Table

async def test_endpoint(
    endpoint: str,
    method: str = "GET",
    with_cache: bool = False
):
    console = Console()

    # Get auth token
    token = get_test_token()

    # First request
    start = time.time()
    response1 = await make_request(endpoint, method, token)
    time1 = time.time() - start

    console.print(f"✅ Status: {response1.status_code}")
    console.print(f"⏱️  Response Time: {time1:.2f}s")

    if with_cache and method == "GET":
        # Second request (should hit cache)
        start = time.time()
        response2 = await make_request(endpoint, method, token)
        time2 = time.time() - start

        speedup = time1 / time2
        console.print(f"\n2️⃣ Second Request: {time2:.2f}s")
        console.print(f"⚡ Speedup: {speedup:.1f}x faster")

        # Force refresh
        start = time.time()
        response3 = await make_request(
            f"{endpoint}?refresh=true", method, token
        )
        time3 = time.time() - start

        console.print(f"\n3️⃣ Force Refresh: {time3:.2f}s")

    # Check logs for cache operations
    check_cache_logs(endpoint)
```

## Related

- [cache-check](#cache-check) - Cache implementation audit
- [workout-gen](#workout-gen) - Generate and test workouts
