# GitHub Copilot Instructions

AI 기반 QA 자동화 도구. 시나리오 문서(PPTX/DOCX/PDF/이미지) 분석 → Playwright 웹 테스트 → 리포트/이슈 자동화.

> **기술 명세 (단일 원본)**: [SPEC.md](../SPEC.md) — Phase 수행 가이드, Key Conventions, 산출물 정의

## Setup

```bash
pip install -r requirements.txt
playwright install chromium
```

## Key Commands

```bash
# QA 세션 초기화 및 상태 관리
python scripts/qa_cli.py init
python scripts/qa_cli.py status / next / resume
python scripts/qa_cli.py start <N> / complete <N> [--files ...] / fail <N> "사유"
python scripts/qa_cli.py set test_url "http://localhost:3000"
python scripts/qa_cli.py set github_repo "owner/repo"

# 유틸리티 스크립트
python .cursor/skills/qa-automation/scripts/extract_document.py inputs/ --output outputs
python .cursor/skills/qa-automation/scripts/compare_screenshot.py <ref.png> <actual.png> [--threshold 10]
python .cursor/skills/qa-automation/scripts/validate_json.py outputs/test_plan.json
python scripts/generate_test_skeleton.py [--output-dir outputs]
python scripts/merge_test_plans.py [--output-dir outputs]
```

## Architecture

```
scripts/
  qa_cli.py                  # Phase 검증 게이트 + YAML 상태 DB
  run_all_tests.py           # Action 기반 테스트 러너
  generate_test_skeleton.py  # extract_result → test_plan_skeleton.json
  merge_test_plans.py        # 카테고리별 JSON → test_plan.json 병합
  generate_report.py         # REPORT.md 생성
  create_github_issues.py    # GitHub 이슈 자동 등록
.cursor/skills/qa-automation/scripts/  # 공유 Python 스크립트
.cursor/agents/ / .claude/agents/      # AI 에이전트 정의 (구조 동일)
outputs/                               # 산출물 + qa_state.yaml
```

## 6-Phase 워크플로우

Phase 0(사전 검증) → 1(문서 분석) → 2(테스트 설계) → 3(테스트 실행) → 4(리포트) → 5(이슈 등록) → 5.5(실패 수정, 선택) → 6(정리)

**[GATE]**: `qa_cli.py start <N>`이 exit code 2 → 즉시 중단, 사유 보고. Phase별 상세는 [SPEC.md](../SPEC.md) 참조.

## 코드 스타일

- Python: PEP 8, 함수/클래스에 docstring, 타입 힌트 사용
- JSON: 들여쓰기 2칸, 쌍따옴표, 마지막 요소에 쉼표 없음

## 기능 추가 시 수정 순서

1. `.cursor/` 버전 먼저 수정 (원본)
2. `.claude/` 버전에 동일 변경 반영
3. 공유 Python 스크립트는 `.cursor/skills/qa-automation/scripts/`에서 한 번만 수정
