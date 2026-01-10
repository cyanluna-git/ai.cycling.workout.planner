# cache-check

캐시 구현 상태를 확인하고 누락된 캐시 무효화 로직을 찾습니다.

## Usage

```bash
/cache-check
```

## What it does

1. **Cache Invalidation 감사**
   - 모든 데이터 수정 엔드포인트 확인
   - `clear_user_cache()` 호출 여부 검증
   - 누락된 캐시 무효화 리포트

2. **Cache Key 일관성 확인**
   - Getter와 Setter에서 동일한 키 사용 확인
   - 세분화된 키 사용 권장사항 제시

3. **TTL 설정 분석**
   - 현재 TTL 설정 요약
   - 데이터 타입별 적절성 평가

4. **개선 제안**
   - 캐시 효율성 개선 방안
   - 잠재적 stale data 문제 식별

## Example Output

```
🔍 Cache Implementation Audit

✅ Endpoints with Cache Invalidation:
  - POST /plans/weekly/generate
  - POST /plans/weekly/{id}/register-all
  - POST /plans/today/regenerate
  - POST /workout/create

⚠️  Potential Issues:
  - PUT /plans/daily/{id}/skip - No cache invalidation
  - DELETE /plans/weekly/{id} - No cache invalidation

📊 Cache Key Usage:
  ✅ fitness:complete - Used in 3 places
  ✅ fitness:training - Used in 3 places
  ⚠️  Old 'fitness' key still used in 1 place

💡 Recommendations:
  1. Add cache invalidation to skip_workout endpoint
  2. Add cache invalidation to delete_weekly_plan endpoint
  3. Consider migrating remaining 'fitness' key usage
```

## Implementation

```python
import re
from pathlib import Path

def audit_cache_implementation():
    # Search for endpoints that modify data
    modification_patterns = [
        r'@router\.(post|put|delete|patch)',
        r'supabase\.table\(.*\)\.(insert|update|delete)',
        r'intervals\.create_workout',
        r'intervals\.delete_event',
    ]

    # Search for cache invalidation calls
    cache_clear_pattern = r'clear_user_cache'

    # Scan all router files
    router_files = Path('api/routers').glob('*.py')

    issues = []
    for file in router_files:
        content = file.read_text()

        # Find functions with modifications
        functions = re.findall(r'async def (\w+)\(', content)

        for func in functions:
            func_content = extract_function(content, func)

            has_modification = any(
                re.search(pattern, func_content)
                for pattern in modification_patterns
            )

            has_cache_clear = re.search(cache_clear_pattern, func_content)

            if has_modification and not has_cache_clear:
                issues.append({
                    'file': file.name,
                    'function': func,
                    'issue': 'Missing cache invalidation'
                })

    return issues
```
