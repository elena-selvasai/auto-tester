# AI QA Automation — Claude Code 프로젝트 지침

시나리오 문서(PPTX/DOCX/PDF/이미지)를 분석하여 Playwright 웹 자동화 테스트를 수행하는 AI 기반 QA 자동화 도구입니다.

> **기술 명세 (단일 원본)**: [SPEC.md](../SPEC.md) — Phase 수행 가이드, Key Conventions, 산출물 정의
> **전체 가이드**: [README.md](../README.md) | **호환성**: [COMPATIBILITY.md](../COMPATIBILITY.md)

## 빠른 시작

```bash
python scripts/qa_cli.py init
```

채팅창에서: `QA 자동화 시작해줘`

## CLI 상태 관리

모든 Phase 전환은 `scripts/qa_cli.py`를 통해서만 수행합니다.
`start <N>` exit code 2 → 즉시 중단, 사유를 사용자에게 보고.

```bash
python scripts/qa_cli.py status          # 전체 Phase 현황
python scripts/qa_cli.py next            # 다음 할 일
python scripts/qa_cli.py resume          # 중단 지점 재개
python scripts/qa_cli.py start <N>       # Phase N 시작 (검증 게이트)
python scripts/qa_cli.py complete <N> [--files file1 file2 ...]
python scripts/qa_cli.py fail <N> "사유"
```

## 워크플로우

Phase 0 → 1 → 2 → 3 → 4 → 5 → 5.5(선택) → 6. 각 Phase의 상세 가이드는 [SPEC.md](../SPEC.md) 참조.

## Agent

| Agent | 역할 | Phase |
|-------|------|-------|
| `qa-master` | 전체 워크플로우 총괄 | 전체 |
| `doc-analyst` | 문서 분석 | 1 |
| `test-architect` | 테스트 설계 | 2 |
| `qa-executor` | 테스트 실행 | 3 |
| `auto-fixer` | 실패 테스트 수정 | 5.5 |

## 스크립트 경로

```bash
# 문서 추출
python .cursor/skills/qa-automation/scripts/extract_document.py inputs/ --output outputs
# 화면 비교
python .cursor/skills/qa-automation/scripts/compare_screenshot.py reference.png screenshot.png --threshold 10
# JSON 검증
python .cursor/skills/qa-automation/scripts/validate_json.py outputs/test_plan.json
# 스켈레톤 생성 (Phase 2 Step 1)
python scripts/generate_test_skeleton.py [--output-dir outputs]
# 카테고리별 병합 (Phase 2 Step 3)
python scripts/merge_test_plans.py [--output-dir outputs] [--skeleton path]
```

## 기여 가이드

1. `.cursor/` 버전 먼저 수정 (원본)
2. `.claude/` 버전에 동일 변경 사항 반영
3. 공유 스크립트는 `.cursor/skills/qa-automation/scripts/`에서만 수정
4. `scripts/qa_cli.py`는 양쪽 공유 — 한 번만 수정
