# deploy-check

배포 전 체크리스트를 실행하고 잠재적 문제를 식별합니다.

## Usage

```bash
/deploy-check [--env ENV] [--fix-issues]
```

## Arguments

- `--env` - Target environment (dev, staging, production)
- `--fix-issues` - 자동으로 수정 가능한 문제 해결

## What it does

1. **코드 품질 검사**
   - Linting 오류 확인
   - Type checking
   - Import 순환 참조 검사

2. **환경 설정 검증**
   - 필수 환경 변수 확인
   - API 키 검증
   - 데이터베이스 연결 테스트

3. **캐시 구현 검사**
   - 캐시 무효화 누락 확인
   - TTL 설정 검증

4. **보안 검사**
   - 하드코딩된 시크릿 검색
   - 취약한 의존성 확인

5. **성능 검사**
   - N+1 쿼리 패턴 확인
   - 무거운 동기 작업 검사

## Examples

### Basic Check
```bash
/deploy-check --env production
```

Output:
```
🚀 Deployment Readiness Check (Production)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 1. Code Quality
✅ Linting: 0 errors, 3 warnings
✅ Type checking: Passed
✅ No circular imports
⚠️  3 TODO comments found

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔧 2. Environment Configuration
✅ SUPABASE_URL configured
✅ SUPABASE_SERVICE_KEY configured
✅ OPENAI_API_KEY configured
✅ DATABASE_URL configured
⚠️  SENTRY_DSN not configured (optional)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💾 3. Cache Implementation
✅ All mutation endpoints have cache invalidation
✅ TTL settings are appropriate
✅ Cache keys are consistent
⚠️  Consider Redis for production

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔒 4. Security
✅ No hardcoded secrets
✅ All dependencies up to date
✅ CORS configured correctly
✅ Rate limiting enabled

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚡ 5. Performance
✅ No obvious N+1 queries
✅ Database indexes present
⚠️  3 synchronous API calls in async context
💡 Consider using asyncio.gather()

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🧪 6. Tests
✅ Unit tests: 45/45 passing
✅ Integration tests: 12/12 passing
⚠️  Coverage: 78% (target: 80%)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 Overall Score: 8.5/10

Status: ✅ READY TO DEPLOY

⚠️  Warnings (Non-blocking):
1. Add coverage for cache_service.py
2. Configure Sentry for error tracking
3. Optimize async API calls in workout_generator.py

💡 Recommendations:
1. Run load tests before deployment
2. Set up monitoring alerts
3. Create rollback plan
```

### With Auto-Fix
```bash
/deploy-check --env production --fix-issues
```

Output:
```
🚀 Deployment Check with Auto-Fix

🔧 Fixing Issues...

1. Formatting code with black...
   ✅ Fixed 5 files

2. Organizing imports with isort...
   ✅ Fixed 3 files

3. Removing unused imports...
   ✅ Cleaned 2 files

4. Updating type hints...
   ✅ Added 8 type hints

5. Optimizing async calls...
   ✅ Converted 3 sequential calls to parallel

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 Re-running Checks...

✅ All checks passed!

Changes made:
  M api/routers/plans.py
  M api/routers/workout.py
  M api/services/cache_service.py

Please review and commit these changes.
```

### Detailed Report
```bash
/deploy-check --env production > deployment_report.txt
```

## Implementation

```python
import subprocess
from pathlib import Path
from typing import List, Dict

class DeploymentCheck:
    def __init__(self, env: str):
        self.env = env
        self.issues = []
        self.warnings = []

    async def run_all_checks(self) -> Dict:
        """Run all deployment checks."""
        results = {
            'code_quality': await self.check_code_quality(),
            'env_config': await self.check_environment(),
            'cache': await self.check_cache_implementation(),
            'security': await self.check_security(),
            'performance': await self.check_performance(),
            'tests': await self.run_tests(),
        }

        return self.generate_report(results)

    async def check_code_quality(self) -> Dict:
        """Check code quality."""
        # Run linters
        ruff_result = subprocess.run(
            ['ruff', 'check', '.'],
            capture_output=True,
            text=True
        )

        # Run type checker
        mypy_result = subprocess.run(
            ['mypy', 'api/', 'src/'],
            capture_output=True,
            text=True
        )

        # Check circular imports
        circular = self.find_circular_imports()

        return {
            'lint_errors': len(ruff_result.stderr.split('\n')),
            'type_errors': len(mypy_result.stderr.split('\n')),
            'circular_imports': circular,
        }

    async def check_cache_implementation(self) -> Dict:
        """Verify cache implementation."""
        from skills.cache_check import audit_cache_implementation

        issues = audit_cache_implementation()

        return {
            'missing_invalidation': len(issues),
            'issues': issues,
        }

    async def check_security(self) -> Dict:
        """Check for security issues."""
        # Scan for hardcoded secrets
        secrets = self.find_hardcoded_secrets()

        # Check dependencies
        safety_result = subprocess.run(
            ['safety', 'check'],
            capture_output=True,
            text=True
        )

        return {
            'hardcoded_secrets': secrets,
            'vulnerable_deps': len(safety_result.stdout.split('\n')),
        }

    def find_hardcoded_secrets(self) -> List[str]:
        """Find hardcoded secrets in code."""
        patterns = [
            r'sk-[a-zA-Z0-9]{48}',  # OpenAI keys
            r'supabase\.co.*anon',   # Supabase anon keys
            r'password\s*=\s*["\'][^"\']+["\']',  # Passwords
        ]

        secrets = []
        for file in Path('api').rglob('*.py'):
            content = file.read_text()
            for pattern in patterns:
                if re.search(pattern, content):
                    secrets.append(f"{file}:{pattern}")

        return secrets

    async def check_performance(self) -> Dict:
        """Check for performance issues."""
        # Find N+1 queries
        n_plus_one = self.find_n_plus_one_queries()

        # Find synchronous calls in async context
        sync_in_async = self.find_sync_in_async()

        return {
            'n_plus_one_queries': n_plus_one,
            'sync_in_async': sync_in_async,
        }

    def find_sync_in_async(self) -> List[str]:
        """Find synchronous API calls in async functions."""
        issues = []

        for file in Path('api').rglob('*.py'):
            content = file.read_text()

            # Find async functions
            async_funcs = re.findall(
                r'async def (\w+)\(.*?\):.*?(?=async def|\Z)',
                content,
                re.DOTALL
            )

            for func in async_funcs:
                # Check for sync API calls
                if 'requests.get(' in func or 'requests.post(' in func:
                    issues.append(f"{file.name}:{func}")

        return issues
```

## Pre-Deploy Checklist

- [ ] All tests passing
- [ ] Code quality checks pass
- [ ] Environment variables configured
- [ ] Database migrations applied
- [ ] Cache implementation verified
- [ ] Security scan clean
- [ ] Performance optimized
- [ ] Documentation updated
- [ ] Rollback plan ready
- [ ] Monitoring configured

## Related

- [cache-check](#cache-check) - Cache implementation audit
- [api-test](#api-test) - Test endpoints
