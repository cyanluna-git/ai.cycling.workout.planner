# whatsonzwift.com 스크래퍼 완성

## 개요
whatsonzwift.com 스크래퍼를 전면 재작성하여 동적 컬렉션 탐색, 텍스트 기반 추출, 리줌 지원을 구현했다. 고장난 v2 스크래퍼를 삭제하고, import_zwo.py에 source_url 중복 체크를 추가했으며, 39개 정규식 유닛 테스트를 작성했다.

## 주요 변경사항
- **재작성**: `scrape_whatsonzwift.py` — CSS 셀렉터 의존 제거, 텍스트 노드 스캔 방식으로 전환. 동적 컬렉션 발견, 리줌, rate limiting, CLI 옵션 추가
- **수정**: `import_zwo.py` — `source_url`, `source` 파라미터 추가, source_url 기반 중복 체크
- **삭제**: `scrape_whatsonzwift_v2.py` — 이중 이스케이프 버그로 완전 고장, 불필요
- **신규**: `tests/test_scraper_regex.py` — 39개 테스트 (정규식, ZWO 생성, URL 필터링)

## 핵심 코드

```python
# 텍스트 기반 추출 전략 — CSS 클래스 대신 모든 텍스트 노드 스캔
def extract_step_texts(tree):
    candidates = []
    for node in tree.iter():
        if node.text:
            for line in node.text.splitlines():
                line = line.strip()
                if line and ("% FTP" in line or "free ride" in line.lower()):
                    candidates.append(line)
```

```python
# source_url 기반 리줌 — 이미 임포트된 운동 스킵
def get_imported_source_urls(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT source_url FROM workout_profiles WHERE source_url IS NOT NULL")
    return {row[0] for row in cursor.fetchall()}
```

## 결과
- ✅ 39/39 테스트 통과 (0.21초)
- ✅ CLI 옵션: `--list-collections`, `--collection`, `--dry-run`, `--limit`, `--delay`, `--no-resume`, `--verbose`
- ✅ v1/v2 통합 완료, v2 삭제

## 다음 단계
- `--list-collections`로 실제 사이트 컬렉션 목록 확인
- `--collection sweet-spot --dry-run --limit 3`으로 단일 컬렉션 dry-run 테스트
- 실제 임포트 실행 (`--collection sweet-spot --limit 5`)으로 DB 저장 검증
- 사이트 HTML 구조 변경 시 `extract_step_texts()` 텍스트 패턴 업데이트 필요
- 대량 임포트 후 카테고리 자동 분류 정확도 검증 (sweetspot vs threshold 경계 등)
