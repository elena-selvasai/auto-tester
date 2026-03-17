# AI QA Automation - Claude Code 프로젝트 지침

이 프로젝트는 시나리오 문서(PPTX/DOCX/PDF/이미지)를 분석하여 Playwright 웹 자동화 테스트를 수행하는 AI 기반 QA 자동화 도구입니다.

> **상세 사양**: [SPEC.md](../SPEC.md) | **전체 가이드**: [README.md](../README.md)

## 주요 기능

- **문서 분석**: PPTX/DOCX/PDF/이미지에서 텍스트, 표, 노트, 삽입 이미지 자동 추출
- **참조 이미지 저장**: 기획서 슬라이드/페이지별 이미지를 `outputs/reference/`에 저장 → 화면 비교·구성 체크에 활용
- **화면 비교**: 참조 이미지와 실제 스크린샷 유사도 비교
- **구성 체크**: 기획서 기준 예상 표시 요소 확인
- **AI 시나리오 생성**: AI를 활용한 테스트 시나리오 자동 작성
- **웹 자동화 테스트**: Playwright 기반의 브라우저 자동화 테스트
- **리포트 생성**: 테스트 결과를 Markdown 형식으로 출력
- **GitHub 이슈 등록**: 테스트 실패 시 자동으로 이슈 생성
- **실패 자동 수정**: 이슈 분석 후 테스트 코드 오류 자동 수정 및 재테스트
- **YAML 상태 관리**: Phase별 진행 상태를 `qa_state.yaml`에 기록, 중단 후 재개 가능
- **CLI 검증 게이트**: 이전 Phase 미완료·필수 산출물 없으면 다음 Phase 자동 거부

## 기술 스택

- **Claude Code Skills & Agents**: AI 기반 워크플로우 자동화
- **qa_cli.py**: YAML + CLI 상태 관리 (Phase 게이트, 리마인더)
- **Playwright**: 웹 브라우저 자동화
- **python-pptx / python-docx / PyMuPDF**: 문서 파싱
- **Pillow, imagehash**: 화면 비교
- **PyYAML**: 상태 파일 읽기/쓰기

## 폴더 구조

```
auto-tester/
├── .claude/                    # Claude Code 전용 설정
│   ├── CLAUDE.md               # 이 파일
│   ├── agents/                 # 서브에이전트 정의
│   │   ├── qa-master.md
│   │   ├── doc-analyst.md
│   │   ├── test-architect.md
│   │   ├── qa-executor.md
│   │   └── auto-fixer.md
│   └── skills/
│       └── qa-automation/
│           └── SKILL.md
├── .cursor/                    # Cursor 전용 설정 (구조 동일)
│   └── skills/qa-automation/scripts/  # 공통 Python 스크립트
├── scripts/
│   ├── qa_cli.py               # YAML+CLI 상태 관리 도구
│   ├── run_all_tests.py        # Action 기반 테스트 러너
│   ├── generate_report.py      # REPORT.md 생성
│   ├── create_github_issues.py # GitHub 이슈 자동 등록
│   └── run_test.py             # 간단한 URL 테스트 러너 (레거시)
├── inputs/                     # 입력 파일 (PPTX, DOCX, PDF, 이미지)
├── outputs/                    # 출력 결과물
│   └── qa_state.yaml           # Phase 진행 상태 DB (자동 생성)
├── SPEC.md                     # 기술 명세 (단일 원본)
└── README.md
```

## 사용 방법

### 빠른 시작

```bash
python scripts/qa_cli.py init
```

채팅창에서:
```
QA 자동화 시작해줘
```

### 상태 확인

```bash
python scripts/qa_cli.py status          # 전체 Phase 현황
python scripts/qa_cli.py next            # 다음 할 일
python scripts/qa_cli.py resume          # 중단 지점 재개
python scripts/qa_cli.py fail <N> "사유" # Phase 실패 기록
```

### 워크플로우

모든 Phase 전환은 `scripts/qa_cli.py`를 통해서만 수행합니다.
`start <N>` exit code 2 → 즉시 중단, 사유를 사용자에게 보고.

```
Phase 0: 사전 검증         → qa_cli.py start 0 / complete 0
  ↓ [GATE]
Phase 1: 문서 분석          → qa_cli.py start 1 / complete 1
  ↓ [GATE: scenario_draft.md 필요]
Phase 2: 테스트 설계        → qa_cli.py start 2 / complete 2
  ↓ [GATE: test_plan.json 필요]
Phase 3: 테스트 실행        → qa_cli.py start 3 / complete 3
  ↓ [GATE: test_result.json 필요]
Phase 4: 리포트 생성        → qa_cli.py start 4 / complete 4
  ↓ [GATE: REPORT.md 필요]
Phase 5: GitHub 이슈 등록   → qa_cli.py start 5 / complete 5
  ↓
Phase 5.5: 실패 수정 [선택] → qa_cli.py start 5.5 / complete 5.5
  ↓
Phase 6: 정리               → qa_cli.py start 6 / complete 6
```

Phase별 수행 내용은 [SPEC.md](../SPEC.md) 참조.

## 스크립트 경로

모든 명령은 **프로젝트 루트**에서 실행합니다.

```bash
# 상태 관리
python scripts/qa_cli.py init
python scripts/qa_cli.py start <N>
python scripts/qa_cli.py complete <N> [--files file1 file2 ...]

# 문서 추출
python .cursor/skills/qa-automation/scripts/extract_document.py inputs/ --output outputs

# 화면 비교
python .cursor/skills/qa-automation/scripts/compare_screenshot.py reference.png screenshot.png --threshold 10

# JSON 검증
python .cursor/skills/qa-automation/scripts/validate_json.py outputs/test_plan.json
```

## 출력 파일

| 파일 | Phase | 설명 |
|------|-------|------|
| `qa_state.yaml` | 전체 | Phase 진행 상태 DB |
| `scenario_draft.md` | 1 | 테스트 시나리오 |
| `extract_result.json` | 1 | 문서 추출 결과 |
| `scenario_draft_source.md` | 1 | 추출 요약 + 구성 체크 |
| `reference/*.png` | 1 | 기획서 참조 이미지 |
| `test_plan.json` | 2 | JSON 테스트 플랜 |
| `test_result.json` | 3 | 테스트 실행 결과 |
| `screenshot_TC_{tc_id}_{description}.png` | 3 | 테스트 스크린샷 |
| `REPORT.md` | 4 | 최종 리포트 |
| `issues_created.json` | 5 | 생성된 GitHub 이슈 목록 |
| `fix_log.json` | 5.5 | 자동 수정 이력 |

## Agent 사용 가이드

| Agent | 역할 | 호출 예 |
|-------|------|---------|
| `@qa-master` | 전체 워크플로우 총괄 | `@qa-master QA 자동화 시작해줘` |
| `@doc-analyst` | 문서 분석 | `@doc-analyst inputs/기획서.pptx 분석해줘` |
| `@test-architect` | 테스트 설계 | `@test-architect test_plan.json 만들어줘` |
| `@qa-executor` | 테스트 실행 | `@qa-executor 테스트 실행해줘` |
| `@auto-fixer` | 실패 테스트 수정 | `@auto-fixer 실패 테스트 수정해줘` |

## 주의사항

1. **테스트 URL 형식**: 전체 URL 입력 필요 (예: `http://localhost:3000/page`)
2. **GitHub CLI**: Phase 5 사용 시 `gh auth login` 필요
3. **Python 의존성**:
   ```bash
   pip install playwright python-pptx python-docx PyMuPDF Pillow imagehash pyyaml
   playwright install chromium
   ```

## Phase 6 정리 대상

삭제 대상 (`outputs/` 내 임시 파일):
- `issue_ISS_*`, `issue_body_TC*.md`, `REPORT_EXECUTED.md`, `SUMMARY.md`
- `TEST_EXECUTION_SUMMARY.md`, `test_result_executed.json`, `debug_*.png`

삭제 대상 (루트 임시 스크립트 — AI가 세션 중 생성한 것):
- `explore_page.py`, `explore_dom*.py`, `run_test_tc*.py`, `run_tests.py`, `create_github_dir.py`, `run_commands.bat`

보존 대상 (삭제 금지):
- `scripts/run_all_tests.py`, `outputs/issue_body.md`

## 추가 리소스

- [README.md](../README.md) - 프로젝트 개요 및 전체 가이드
- [SPEC.md](../SPEC.md) - 기술 명세 (단일 원본, Phase별 상세 가이드)
- [COMPATIBILITY.md](../COMPATIBILITY.md) - AI 도구 호환성 가이드
- [Cursor Skills 문서](../.cursor/skills/qa-automation/SKILL.md) - Cursor 사용자용 가이드

## 기여 가이드

1. `.cursor/` 버전 먼저 수정 (원본)
2. `.claude/` 버전에 동일 변경 사항 반영
3. 공유 스크립트는 `.cursor/skills/qa-automation/scripts/`에서만 수정
4. `scripts/qa_cli.py`는 양쪽 공유 — 한 번만 수정
