# db-analyze

데이터베이스 상태를 분석하고 최적화 제안을 제공합니다.

## Usage

```bash
/db-analyze [--table TABLE] [--slow-queries] [--optimize]
```

## Arguments

- `--table` - 특정 테이블 분석 (optional)
- `--slow-queries` - 느린 쿼리 분석
- `--optimize` - 최적화 제안 제공

## What it does

1. **테이블 통계**
   - 레코드 수
   - 디스크 사용량
   - 인덱스 상태

2. **쿼리 성능**
   - 느린 쿼리 식별
   - N+1 쿼리 패턴
   - 누락된 인덱스

3. **데이터 품질**
   - NULL 값 비율
   - 중복 데이터
   - 참조 무결성

4. **최적화 제안**
   - 인덱스 추가 제안
   - 파티셔닝 제안
   - 쿼리 개선 제안

## Examples

### Basic Analysis
```bash
/db-analyze
```

Output:
```
🗄️  Database Analysis Report

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 Overview
Database: ai_cycling_planner
Size: 145 MB
Tables: 8
Total Records: 12,543

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 Table Statistics

┏━━━━━━━━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━┳━━━━━━━━━━┓
┃ Table            ┃ Records ┃ Size   ┃ Indexes  ┃
┡━━━━━━━━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━╇━━━━━━━━━━┩
│ users            │ 1,245   │ 5 MB   │ 3        │
│ weekly_plans     │ 3,456   │ 25 MB  │ 4        │
│ daily_workouts   │ 6,789   │ 45 MB  │ 5        │
│ user_settings    │ 1,234   │ 2 MB   │ 2        │
│ intervals_workouts│ 4,567   │ 58 MB  │ 4        │
│ audit_logs       │ 8,934   │ 8 MB   │ 3        │
└──────────────────┴─────────┴────────┴──────────┘

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚡ Performance

Query Avg Response Time: 45ms ✅
Slow Queries (>1s): 2 ⚠️
Cache Hit Rate: 87% ✅
Index Usage: 92% ✅

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔍 Issues Found

⚠️  Medium Priority:
1. Table 'intervals_workouts' missing index on 'user_id, workout_date'
2. Table 'audit_logs' growing rapidly (consider partitioning)

💡 Low Priority:
1. Table 'daily_workouts' has 5% NULL values in 'actual_name'
2. Consider archiving old audit_logs (>90 days)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 Recommendations

1. Add composite index:
   CREATE INDEX idx_intervals_user_date
   ON intervals_workouts(user_id, workout_date);

2. Partition audit_logs by month:
   ALTER TABLE audit_logs
   PARTITION BY RANGE (created_at);

3. Archive old data:
   - Move audit_logs older than 90 days to archive table
   - Estimated space savings: 15 MB
```

### Table-Specific Analysis
```bash
/db-analyze --table daily_workouts
```

Output:
```
🗄️  Table Analysis: daily_workouts

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 Basic Info
Records: 6,789
Size: 45 MB
Avg Row Size: 6.8 KB
Created: 2025-03-15

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔍 Column Analysis

┏━━━━━━━━━━━━━━━━┳━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━┓
┃ Column         ┃ Type  ┃ NULL %  ┃ Unique % ┃
┡━━━━━━━━━━━━━━━━╇━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━┩
│ id             │ uuid  │ 0%      │ 100%     │
│ plan_id        │ uuid  │ 0%      │ 15%      │
│ user_id        │ uuid  │ 0%      │ 18%      │
│ workout_date   │ date  │ 0%      │ 8%       │
│ planned_name   │ text  │ 0%      │ 45%      │
│ actual_name    │ text  │ 5% ⚠️   │ 42%      │
│ status         │ text  │ 0%      │ 0.1%     │
└────────────────┴───────┴─────────┴──────────┘

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📈 Growth Rate
Last 30 days: +2,345 records (+52%)
Projected 90 days: +7,000 records
Estimated size in 90 days: 115 MB

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔎 Indexes

1. idx_daily_workouts_pkey (PRIMARY)
   Columns: id
   Size: 2.1 MB
   Usage: 100%

2. idx_daily_workouts_plan_id
   Columns: plan_id
   Size: 1.8 MB
   Usage: 87%

3. idx_daily_workouts_user_date
   Columns: user_id, workout_date
   Size: 2.5 MB
   Usage: 95% ✅

4. idx_daily_workouts_status
   Columns: status
   Size: 0.8 MB
   Usage: 12% ⚠️  (Consider removing)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 Optimization Suggestions

1. Consider removing low-usage index 'idx_daily_workouts_status'
   - Only 12% query usage
   - Saves 0.8 MB
   - Improves INSERT performance

2. Actual_name has 5% NULL values
   - This is expected for future workouts
   - Consider adding CHECK constraint for completed workouts

3. Status column has low cardinality (0.1% unique)
   - Perfect for ENUM type
   - ALTER TABLE daily_workouts
     ALTER COLUMN status TYPE workout_status;

4. Add partial index for active workouts:
   CREATE INDEX idx_daily_workouts_active
   ON daily_workouts(user_id, workout_date)
   WHERE status IN ('planned', 'regenerated');
```

### Slow Query Analysis
```bash
/db-analyze --slow-queries
```

Output:
```
🐌 Slow Query Analysis

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Found 3 slow queries (>1s avg response time)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. ⚠️  GET /api/fitness
   Avg Time: 1.8s
   Calls: 456/day
   File: api/routers/fitness.py:64

   Query:
   SELECT * FROM intervals_activities
   WHERE user_id = $1
   ORDER BY start_date DESC
   LIMIT 42

   Issue: Missing index on (user_id, start_date DESC)

   Fix:
   CREATE INDEX idx_intervals_activities_user_date_desc
   ON intervals_activities(user_id, start_date DESC);

   Expected improvement: 1.8s → 0.3s (6x faster)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

2. ⚠️  GET /api/weekly-calendar
   Avg Time: 1.2s
   Calls: 234/day
   File: api/routers/fitness.py:371

   Query:
   SELECT e.*, w.*
   FROM events e
   LEFT JOIN daily_workouts w ON e.workout_id = w.id
   WHERE e.user_id = $1
   AND e.start_date BETWEEN $2 AND $3

   Issue: N+1 query pattern (fetching workout details)

   Fix: Use JOIN instead of separate queries
   - Refactor to single query with JOIN
   - Add index on daily_workouts.id

   Expected improvement: 1.2s → 0.4s (3x faster)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

3. ⚠️  POST /api/plans/weekly/generate
   Avg Time: 1.5s
   Calls: 89/day
   File: api/routers/plans.py:574

   Query:
   DELETE FROM daily_workouts
   WHERE user_id = $1
   AND workout_date BETWEEN $2 AND $3

   Issue: Sequential DELETEs for 7 days

   Fix: Use single DELETE with BETWEEN
   DELETE FROM daily_workouts
   WHERE user_id = $1
   AND workout_date BETWEEN $2 AND $3;

   Expected improvement: 1.5s → 0.2s (7x faster)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💰 Total Savings if all fixed:
- Time saved per day: 892 seconds
- Reduced load: ~4,500 db calls/day
- Cost savings: ~$15/month (estimated)
```

## Related

- [deploy-check](#deploy-check) - Pre-deployment checks
- [api-test](#api-test) - Test endpoints
