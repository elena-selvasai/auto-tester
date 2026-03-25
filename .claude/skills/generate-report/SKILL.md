---
name: generate-report
description: Use when generating QA test report from test results. Triggers on report generation, REPORT.md creation, Phase 4 reporting, or test result summarization.
---

# QA 리포트 생성

`test_result.json`에서 마크다운 리포트(`REPORT.md`)를 생성합니다.

## 실행

```bash
python scripts/generate_report.py [--result PATH] [--output PATH]
```

| 옵션 | 기본값 | 설명 |
|------|--------|------|
| `--result` | outputs/test_result.json | 입력 파일 |
| `--output` | outputs/REPORT.md | 출력 파일 |

## 리포트 구성

1. **Summary** — Total / Passed / Failed / Skipped / Errors / Pass Rate
2. **카테고리별 결과** — 카테고리별 통과율 테이블
3. **상세 결과** — TC별 상태·메시지 테이블
4. **발견 사항** — 실패/스킵 항목 검토 안내
5. **실패 케이스 스크린샷** — 스크린샷이 있는 실패 TC 목록

## 입력 요건

`test_result.json`은 `run_all_tests.py` 실행 후 자동 생성됩니다. 필수 필드: `summary`, `category_summary`, `results`.

## 산출물

`outputs/REPORT.md` — GitHub/사내 위키에 바로 올릴 수 있는 마크다운 형식.
