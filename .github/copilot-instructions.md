# GitHub Copilot Instructions

이 프로젝트는 시나리오 문서(PPTX/DOCX/PDF/이미지)를 분석하여 Playwright 웹 자동화 테스트를 수행하는 **AI 기반 QA 자동화 도구**입니다.

> **상세 사양**: [SPEC.md](../SPEC.md) 참조 (단일 원본 — Phase 수행 가이드, Key Conventions, 산출물 목록 포함)

## Setup

```bash
pip install -r requirements.txt
playwright install chromium
```

## Key Commands

```bash
# QA 세션 초기화
python scripts/qa_cli.py init

# Phase 상태 확인 및 워크플로우 탐색
python scripts/qa_cli.py status
python scripts/qa_cli.py next
python scripts/qa_cli.py resume

# Phase 전환 (반드시 qa_cli.py를 통해서만)
python scripts/qa_cli.py start <N>
python scripts/qa_cli.py complete <N> [--files file1 file2 ...]
python scripts/qa_cli.py fail <N> "사유"

# 설정값 저장
python scripts/qa_cli.py set test_url "http://localhost:3000"
python scripts/qa_cli.py set github_repo "owner/repo"
python scripts/qa_cli.py set skip_github true

# 유틸리티 스크립트
python .cursor/skills/qa-automation/scripts/extract_document.py inputs/ --output outputs
python .cursor/skills/qa-automation/scripts/compare_screenshot.py <ref.png> <actual.png> [--threshold 10]
python .cursor/skills/qa-automation/scripts/validate_json.py outputs/test_plan.json
```

## Architecture

```
inputs/                                          # 입력 문서 (PPTX/DOCX/PDF/이미지)
scripts/
  qa_cli.py                                      # Phase 검증 게이트 + YAML 상태 DB
  generate_report.py                             # REPORT.md 생성
  create_github_issues.py                        # GitHub 이슈 자동 등록
  run_all_tests.py                               # Action 기반 테스트 러너
  run_test.py                                    # 간단한 URL 테스트 러너 (레거시)
.cursor/skills/qa-automation/scripts/            # 공유 Python 스크립트 (모든 AI 도구 공유)
.cursor/agents/  /  .claude/agents/              # AI 에이전트 정의 (구조 동일)
outputs/                                         # 산출물 + qa_state.yaml (상태 DB)
```

**다중 AI 도구 지원**: `.cursor/` (Cursor용), `.claude/` (Claude Code용). 두 버전은 동일 Python 스크립트(`.cursor/skills/qa-automation/scripts/`)를 공유합니다.

### 6-Phase 워크플로우

```
Phase 0: 사전 검증 (GitHub CLI, 테스트 URL)
  ↓ [GATE]
Phase 1: 문서 분석 → doc-analyst → outputs/scenario_draft.md + reference/*.png
  ↓ [GATE: scenario_draft.md 필요]
Phase 2: 테스트 설계 → test-architect → outputs/test_plan.json (5개 카테고리)
  ↓ [GATE: test_plan.json 필요]
Phase 3: 테스트 실행 → qa-executor → outputs/test_result.json + screenshot_*.png
  ↓ [GATE: test_result.json 필요]
Phase 4: 리포트 생성 → outputs/REPORT.md
  ↓ [GATE: REPORT.md 필요]
Phase 5: GitHub 이슈 등록 → gh issue create → outputs/issues_created.json
Phase 5.5: 실패 자동 수정 [선택] → auto-fixer → outputs/fix_log.json
Phase 6: 정리 (임시 파일 삭제)
```

**[GATE]**: `qa_cli.py start <N>`이 exit code 2를 반환하면 즉시 중단하고 사용자에게 사유를 보고합니다.

### 에이전트 역할

| 에이전트 | 역할 |
|---------|------|
| `qa-master` | 전체 워크플로우 총괄 오케스트레이터 |
| `doc-analyst` | PPTX/DOCX/PDF/이미지 분석 및 시나리오 추출 |
| `test-architect` | scenario_draft.md → test_plan.json 변환 |
| `qa-executor` | Playwright 브라우저 자동화 테스트 실행 |
| `auto-fixer` | 실패 테스트 원인 분석 및 자동 수정 |

## Key Conventions

### Phase 전환 규칙
- **모든 Phase 전환은 반드시 `scripts/qa_cli.py`를 통해서만 수행**합니다.
- `start <N>` exit code 2 → 즉시 중단, 사유 보고
- `complete <N>` exit code 2 → 필수 산출물 미생성, 해당 Phase 재실행
- CLI 명령 실행 후 출력되는 `[REMINDER]` 블록을 읽고 따릅니다.

### test_plan.json 구조

5개 카테고리와 TC 번호 범위가 고정되어 있습니다:

| 카테고리 | TC 범위 | 최소 수 |
|---------|---------|--------|
| `basic_function` | TC_001~050 | 8개 |
| `button_state` | TC_051~100 | 4개 |
| `navigation` | TC_101~150 | 3개 |
| `edge_case` | TC_151~180 | 3개 |
| `accessibility` | TC_181~200 | 2개 |

`base_url`은 항상 `"${base_url}"` 플레이스홀더로 설정합니다.

지원 액션: `navigate`, `click`, `input`, `check`, `wait`, `screenshot`, `hover`, `check_attribute`, `compare_with_reference`

### 선택자 우선순위
`data-testid` > `id` > `aria-label` > `class`

### auto-fixer 수정 범위
- **수정 가능**: `selector_mismatch`, `text_mismatch`, `date_format`, `timing_issue`, `scroll_target`
- **수정 불가** (`app_bug`): 기능 미구현, 동작 오류 → 사용자에게 보고만
- **모든 수정은 사용자 승인 후에만 적용**

### 코드 스타일
- Python: PEP 8, 함수/클래스에 docstring, 타입 힌트 사용
- JSON: 들여쓰기 2칸, 쌍따옴표, 마지막 요소에 쉼표 없음

### 기능 추가 시 수정 순서
1. `.cursor/` 버전 먼저 수정 (원본)
2. `.claude/` 버전에 동일 변경 반영
3. 공유 Python 스크립트는 `.cursor/skills/qa-automation/scripts/`에서 한 번만 수정

### Phase 6 정리 대상 (임시 파일)

삭제 대상 (outputs/ 내 임시 파일):
- `outputs/issue_ISS_*`, `outputs/issue_body_TC*.md`, `outputs/REPORT_EXECUTED.md`, `outputs/SUMMARY.md`
- `outputs/TEST_EXECUTION_SUMMARY.md`, `outputs/test_result_executed.json`, `outputs/debug_*.png`

삭제 대상 (루트 임시 스크립트 — AI가 세션 중 생성한 것):
- `explore_page.py`, `explore_dom*.py`, `run_test_tc*.py`, `run_tests.py`, `create_github_dir.py`, `run_commands.bat`

보존 대상:
- `scripts/run_all_tests.py`, `outputs/issue_body.md` — 프로젝트 스크립트이므로 삭제 금지

### GitHub 이슈 등록
```bash
gh issue create -R {owner/repo} --title "[QA] {이슈ID}: {제목}" --body-file "outputs/issue_body.md" --label "bug"
```

### 오류 처리
- 요소 찾기 실패 → 대체 선택자 시도
- 타임아웃 → 대기 시간 2배 후 최대 2회 재시도
- 네트워크 오류 → 5초 간격 최대 3회 재시도
- 오답 테스트 → 새로고침 후 실제 오답 선택, 정답으로 대체 금지
