# Cache Implementation Guide

## Overview

AI Cycling Workout Planner는 Intervals.icu API 호출을 최소화하고 사용자 경험을 개선하기 위해 최적화된 TTL 기반 캐싱 시스템을 구현하고 있습니다.

## Architecture

### Cache Service Structure

```
api/services/cache_service.py
├── TTL_SETTINGS          # 데이터 타입별 TTL 설정
├── CACHE_KEYS            # 캐시 키 프리픽스
├── get_user_cache()      # 사용자별 캐시 인스턴스 관리
├── get_cached()          # 캐시 조회
├── set_cached()          # 캐시 저장
├── clear_user_cache()    # 캐시 무효화
└── get_cache_stats()     # 캐시 통계
```

## TTL Settings

데이터 업데이트 빈도에 따라 차별화된 TTL을 적용합니다:

| Data Type | TTL | Reason |
|-----------|-----|--------|
| `wellness` | 1 hour | 웰니스 데이터는 하루 단위로 변경됨 |
| `fitness` | 2 hours | 트레이닝 메트릭은 새 활동 발생 시 업데이트 |
| `calendar` | 2 hours | 주간 캘린더/계획된 워크아웃 |
| `activities` | 3 hours | 최근 활동 데이터 |
| `profile` | 6 hours | 사용자 프로필/설정 (거의 변경되지 않음) |
| `sport_settings` | 6 hours | FTP, 파워존 등 (거의 변경되지 않음) |

### Implementation

```python
# api/services/cache_service.py
TTL_SETTINGS = {
    "wellness": 1 * 60 * 60,      # 1 hour
    "fitness": 2 * 60 * 60,        # 2 hours
    "activities": 3 * 60 * 60,     # 3 hours
    "calendar": 2 * 60 * 60,       # 2 hours
    "profile": 6 * 60 * 60,        # 6 hours
    "sport_settings": 6 * 60 * 60, # 6 hours
}
```

## Granular Cache Keys

Fitness 데이터를 세분화하여 선택적 무효화가 가능합니다:

### Before (단일 키)
```
fitness → { training, wellness, profile }
```

### After (세분화된 키)
```
fitness:complete  → 전체 데이터
fitness:training  → CTL/ATL/TSB만
fitness:wellness  → 웰니스 데이터만
fitness:profile   → FTP, 심박 등
```

### Benefits

1. **선택적 무효화**: 특정 데이터만 갱신 가능
2. **효율성**: 불필요한 API 호출 감소
3. **유연성**: 각 데이터 타입별 독립적 관리

## Cache Invalidation Strategy

### Automatic Invalidation Points

캐시는 다음 시점에 자동으로 무효화됩니다:

#### 1. Weekly Plan Generation
```python
# api/routers/plans.py - generate_weekly_plan()
clear_user_cache(user["id"], keys=[
    "calendar",
    "fitness:complete",
    "fitness:training",
    "fitness:wellness"
])
```

**Trigger**: 새로운 주간 플랜 생성 시
**Reason**: 계획된 워크아웃이 변경되므로 캘린더와 피트니스 데이터 갱신 필요

#### 2. Workout Registration to Intervals.icu
```python
# api/routers/plans.py - register_weekly_plan_to_intervals()
if registered_count > 0:
    clear_user_cache(user["id"], keys=[
        "calendar",
        "fitness:complete",
        "fitness:training",
        "fitness:wellness"
    ])
```

**Trigger**: Intervals.icu에 워크아웃 등록 성공 시
**Reason**: 외부 시스템에 데이터가 추가되어 동기화 필요

#### 3. Today's Workout Regeneration
```python
# api/routers/plans.py - regenerate_today_workout()
clear_user_cache(user["id"], keys=[
    "calendar",
    "fitness:complete",
    "fitness:training",
    "fitness:wellness"
])
```

**Trigger**: 오늘의 워크아웃 재생성 시
**Reason**: 새로운 워크아웃으로 교체되므로 관련 데이터 갱신 필요

#### 4. Workout Upload
```python
# api/routers/workout.py - create_workout()
clear_user_cache(user["id"], keys=[
    "calendar",
    "fitness:complete",
    "fitness:training",
    "fitness:wellness"
])
```

**Trigger**: 새로운 워크아웃 업로드 시
**Reason**: 캘린더에 새 워크아웃이 추가됨

#### 5. Settings Update
```python
# api/routers/settings.py
clear_user_cache(user["id"])  # 전체 캐시 클리어
```

**Trigger**: 사용자 설정 변경 시
**Reason**: FTP, 심박 등 기본 설정 변경은 모든 계산에 영향

### Manual Refresh

모든 GET 엔드포인트는 `refresh=true` 파라미터를 지원합니다:

```bash
# Force fresh data
GET /api/fitness?refresh=true
GET /api/activities?refresh=true
GET /api/weekly-calendar?refresh=true
```

## Usage Examples

### 1. Cached Request (Normal Flow)
```python
# First request - Cache MISS
response = await get_fitness(user_id="user123")
# → API call to Intervals.icu
# → Store in cache: "fitness:complete"

# Second request within TTL - Cache HIT
response = await get_fitness(user_id="user123")
# → Return from cache
# → No API call
```

### 2. After Plan Generation
```python
# Generate plan
await generate_weekly_plan(user_id="user123", week_start="2026-01-13")
# → Cache cleared: calendar, fitness:*

# Next request - Cache MISS (forced refresh)
response = await get_fitness(user_id="user123")
# → Fresh API call
# → Updated data returned
```

### 3. Manual Refresh
```python
# Force bypass cache
response = await get_fitness(user_id="user123", refresh=True)
# → Skip cache check
# → Fresh API call
# → Update cache
```

## Monitoring & Debugging

### Cache Statistics

```python
from api.services.cache_service import get_cache_stats

stats = get_cache_stats(user_id="user123")
# Returns:
# {
#   "exists": True,
#   "size": 5,
#   "maxsize": 100,
#   "ttl": 7200,
#   "keys": ["fitness:complete", "fitness:training", "calendar", ...],
#   "ttl_settings": { ... }
# }
```

### Logging

캐시 동작은 DEBUG 레벨에서 로깅됩니다:

```
DEBUG: Cache HIT for user 12345678... key=fitness:complete
DEBUG: Cache MISS for user 12345678... key=wellness
INFO: Cleared cache for user 12345678... after plan generation
```

### Cache Performance Metrics

```python
# Check cache hit rate
hits = log_count("Cache HIT")
misses = log_count("Cache MISS")
hit_rate = hits / (hits + misses) * 100
```

## Best Practices

### 1. Always Clear Relevant Caches

When modifying data that affects multiple entities:

```python
# ✅ Good - Clear all related caches
clear_user_cache(user["id"], keys=[
    "calendar",
    "fitness:complete",
    "fitness:training",
    "fitness:wellness"
])

# ❌ Bad - Partial cache clear
clear_user_cache(user["id"], keys=["calendar"])
```

### 2. Use Granular Keys When Possible

```python
# ✅ Good - Only invalidate what changed
clear_user_cache(user["id"], keys=["fitness:wellness"])

# ❌ Bad - Invalidate everything
clear_user_cache(user["id"])
```

### 3. Log Cache Operations

```python
# ✅ Good - Log for debugging
clear_user_cache(user["id"], keys=["calendar"])
logger.info(f"Cleared calendar cache for user {user['id'][:8]}...")

# ❌ Bad - Silent operation
clear_user_cache(user["id"], keys=["calendar"])
```

### 4. Provide Refresh Option

```python
# ✅ Good - Allow manual override
@router.get("/endpoint")
async def get_data(refresh: bool = False):
    if not refresh:
        cached = get_cached(user_id, cache_key)
        if cached:
            return cached
    # ... fetch fresh data
```

## Troubleshooting

### Problem: Stale Data After Updates

**Symptom**: 사용자가 플랜을 생성했지만 오래된 웰니스 데이터를 봄

**Diagnosis**:
1. Check if cache invalidation is triggered:
   ```bash
   grep "Cleared cache" logs/app.log
   ```

2. Verify cache keys match:
   ```python
   # Ensure invalidation uses same keys as getter
   clear_user_cache(user["id"], keys=["fitness:complete"])
   ```

**Solution**: Add cache invalidation to the operation endpoint

### Problem: Too Many API Calls

**Symptom**: Rate limiting errors from Intervals.icu

**Diagnosis**:
1. Check cache hit rate:
   ```bash
   grep "Cache HIT\|Cache MISS" logs/app.log | tail -100
   ```

2. Verify TTL settings are appropriate

**Solution**:
- Increase TTL for stable data
- Reduce cache invalidation frequency
- Use granular keys to avoid full cache clears

### Problem: Memory Usage Too High

**Symptom**: Server memory consumption increases

**Diagnosis**:
```python
stats = get_cache_stats(user_id)
print(f"Cache size: {stats['size']}/{stats['maxsize']}")
```

**Solution**:
- Reduce `maxsize` in `get_user_cache()`
- Implement cache cleanup for inactive users
- Consider external cache (Redis)

## Future Improvements

### 1. Redis Integration
Replace in-memory cache with Redis for:
- Distributed caching across multiple servers
- Persistence across restarts
- Better memory management

### 2. Smart TTL
Implement dynamic TTL based on:
- Data freshness requirements
- User activity patterns
- API rate limits

### 3. Cache Warming
Pre-populate cache for frequently accessed data:
- Morning wellness data
- Weekly calendar on Monday
- Recent activities after workout

### 4. Webhook Integration
Receive real-time updates from Intervals.icu:
- Instant cache invalidation on external changes
- No need for polling
- Always fresh data

## Migration Notes

### From Old System (Single Key)

If migrating from older code using single `fitness` key:

```python
# Old code
clear_user_cache(user["id"], keys=["fitness"])

# New code (backward compatible)
clear_user_cache(user["id"], keys=[
    "fitness:complete",
    "fitness:training",
    "fitness:wellness",
    "fitness:profile"
])
```

### Backward Compatibility

The cache service maintains backward compatibility:
- Old endpoints using `CACHE_KEYS["fitness"]` still work
- New granular keys work alongside legacy keys
- Gradual migration is possible

## API Reference

### get_cached(user_id, cache_key)
Retrieve cached value for a user.

**Parameters**:
- `user_id` (str): User identifier
- `cache_key` (str): Cache key to retrieve

**Returns**: Cached value or None

### set_cached(user_id, cache_key, value)
Store a value in cache.

**Parameters**:
- `user_id` (str): User identifier
- `cache_key` (str): Cache key
- `value` (Any): Value to cache

### clear_user_cache(user_id, keys=None)
Clear cache for a user.

**Parameters**:
- `user_id` (str): User identifier
- `keys` (list[str], optional): Specific keys to clear. If None, clears all.

### get_cache_stats(user_id)
Get cache statistics.

**Parameters**:
- `user_id` (str): User identifier

**Returns**: Dictionary with cache statistics

## Related Documentation

- [Architecture Overview](./architecture.md)
- [API Documentation](./API.md)
- [Deployment Guide](./DEPLOYMENT.md)

## Changelog

### 2026-01-10
- ✅ Implemented granular cache keys for fitness data
- ✅ Optimized TTL settings for different data types
- ✅ Added cache invalidation to plan generation endpoints
- ✅ Added cache invalidation to workout registration
- ✅ Enhanced logging for cache operations

### Previous
- Initial cache implementation with 6-hour TTL
- Basic cache invalidation on workout upload
