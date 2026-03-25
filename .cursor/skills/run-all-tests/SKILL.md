---
name: run-all-tests
description: Use when executing QA test cases from test_plan.json with Playwright. Triggers on test execution, running TC, Phase 3 test run, parallel test execution, or re-running specific failed TCs.
---

# 테스트 실행기

`test_plan.json`의 TC를 Playwright로 실행하고 결과를 `test_result.json`에 저장합니다.

## 실행

```bash
# 기본 (4 workers 병렬)
python scripts/run_all_tests.py --base-url "http://..."

# 옵션
python scripts/run_all_tests.py --base-url "http://..." \
  --workers 4 \
  --headed \
  --tc "TC_003,TC_015" \
  --precondition '{"actions":[...],"success_checks":[...]}'
```

## 옵션

| 옵션 | 기본값 | 설명 |
|------|--------|------|
| `--base-url` | test_plan.json의 값 | 테스트 URL |
| `--workers` | 4 | 병렬 worker 수 (1이면 순차) |
| `--headed` | off | 브라우저 창 표시 (디버깅용) |
| `--tc` | 전체 | 실행할 TC ID (쉼표 구분) |
| `--precondition` | test_plan.json의 값 | precondition JSON 덮어쓰기 |
| `--test-plan` | outputs/test_plan.json | test plan 경로 |

## 병렬 실행

`--workers N`: TC를 N개 배치로 나누어 각각 별도 브라우저 프로세스에서 실행합니다.

- `--workers 4`: TC 20개 → 배치당 5개, 실행 시간 ~1/4
- `--workers 1`: 순차 실행 (기존 동작)
- 자동으로 `min(workers, TC수)`로 조정

## 지원 액션

| action | 필수 필드 | 설명 |
|--------|----------|------|
| `navigate` | url | 페이지 이동 |
| `click` | selector | 요소 클릭 (fallback: JS click) |
| `input` | selector, value | 텍스트 입력 |
| `check` | selector/expected | 요소/텍스트 존재 확인 |
| `check_attribute` | selector, attribute | 속성 값 검증 |
| `hover` | selector | 마우스 오버 |
| `scroll_into_view` | selector | 뷰포트로 스크롤 |
| `wait` | timeout | 밀리초 대기 |
| `wait_for_selector` | selector | 요소 출현 대기 |
| `screenshot` | filename | 스크린샷 저장 |
| `compare_with_reference` | reference | 참조 이미지 비교 |
| `evaluate` | expression | JS 실행 |

## 산출물

| 파일 | 설명 |
|------|------|
| `outputs/test_result.json` | TC별 상태, 메시지, 소요시간, 스크린샷 |
| `outputs/compare_results.json` | compare_with_reference 비교 결과 |
| `outputs/screenshot_*.png` | 에러/비교 스크린샷 |

## 재시도 정책

- 타임아웃 실패 시 최대 2회 재시도 (1.5초 → 2.25초 대기)
- 비타임아웃 에러는 즉시 실패 처리
