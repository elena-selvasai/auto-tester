# AI QA Automation

시나리오 문서(PPTX, DOCX, PDF, 이미지)를 분석하여 자동으로 테스트 시나리오를 생성하고, Playwright 웹 테스트를 수행하는 **AI 기반** QA 자동화 도구입니다.

**지원 AI 도구**: Cursor, Claude Code | **기술 명세**: [SPEC.md](SPEC.md) | **호환성**: [COMPATIBILITY.md](COMPATIBILITY.md)

## 주요 기능

- **문서 분석**: PPTX/DOCX/PDF/이미지에서 텍스트, 표, 노트, 삽입 이미지 자동 추출
- **참조 이미지 저장**: 기획서 슬라이드/페이지별 이미지를 `outputs/reference/`에 저장
- **화면 비교**: 참조 이미지와 실제 스크린샷 유사도 비교
- **AI 시나리오 생성**: AI를 활용한 테스트 시나리오 자동 작성
- **웹 자동화 테스트**: Playwright 기반 브라우저 자동화
- **리포트 생성 / GitHub 이슈 등록 / 실패 자동 수정**
- **YAML 상태 관리**: Phase별 진행 상태 기록, 중단 후 재개, 검증 게이트

## 사전 준비

```bash
pip install -r requirements.txt
playwright install chromium
```

시나리오 문서를 `inputs/` 폴더에 배치합니다. (PPTX, DOCX, PDF, PNG/JPG)

## 빠른 시작

```bash
python scripts/qa_cli.py init
```

**Cursor**: `@qa-master QA 자동화 시작해줘`
**Claude Code**: `QA 자동화 시작해줘`

## 워크플로우

```
Phase 0: 사전 검증 (GitHub CLI, 테스트 URL)
  ↓ [GATE]
Phase 1: 문서 분석 → doc-analyst → scenario_draft.md + reference/
  ↓ [GATE: scenario_draft.md 필요]
Phase 2: 테스트 설계 → test-architect → test_plan.json (5개 카테고리)
  ↓ [GATE: test_plan.json 필요]
Phase 3: 테스트 실행 → qa-executor → test_result.json + screenshot_*.png
  ↓ [GATE: test_result.json 필요]
Phase 4: 리포트 생성 → REPORT.md
  ↓ [GATE: REPORT.md 필요]
Phase 5: GitHub 이슈 등록 → issues_created.json
Phase 5.5: 실패 자동 수정 [선택] → auto-fixer → fix_log.json
Phase 6: 정리 (임시 파일 삭제)
```

**[GATE]**: `qa_cli.py start <N>`이 exit code 2를 반환하면 즉시 중단.

Phase별 상세 가이드는 [SPEC.md](SPEC.md) 참조.

## 단계별 직접 실행

```bash
# Phase 0: 사전 검증
python scripts/qa_cli.py start 0
python scripts/qa_cli.py set test_url http://localhost:3000
python scripts/qa_cli.py set github_repo owner/repo
python scripts/qa_cli.py complete 0

# Phase 1: 문서 분석
python scripts/qa_cli.py start 1
python .cursor/skills/qa-automation/scripts/extract_document.py inputs/ --output outputs
python scripts/qa_cli.py complete 1 --files outputs/scenario_draft.md

# Phase 2: 테스트 설계 (AI가 test_plan.json 생성)
python scripts/qa_cli.py start 2
python scripts/qa_cli.py complete 2 --files outputs/test_plan.json

# Phase 3: 테스트 실행
python scripts/qa_cli.py start 3
python scripts/run_all_tests.py --test-plan outputs/test_plan.json --base-url "http://localhost:3000"
python scripts/qa_cli.py complete 3 --files outputs/test_result.json

# Phase 4~6
python scripts/qa_cli.py start 4
python scripts/generate_report.py --result outputs/test_result.json --output outputs/REPORT.md
python scripts/qa_cli.py complete 4 --files outputs/REPORT.md
```

## 서브에이전트 직접 호출

```
@doc-analyst inputs/ 기획서 분석해줘
@test-architect test_plan.json 만들어줘
@qa-executor 테스트 실행해줘
@auto-fixer 실패 테스트 수정해줘
```

## CLI 상태 관리

```bash
python scripts/qa_cli.py status          # 전체 Phase 현황
python scripts/qa_cli.py next            # 다음 할 일 안내
python scripts/qa_cli.py resume          # 중단 지점 재개
python scripts/qa_cli.py fail <N> "사유" # Phase 실패 기록
```

## 유틸리티 스크립트

```bash
# 문서 추출 (통합)
python .cursor/skills/qa-automation/scripts/extract_document.py inputs/ --output outputs
# 화면 비교
python .cursor/skills/qa-automation/scripts/compare_screenshot.py ref.png screenshot.png --threshold 10
# JSON 검증
python .cursor/skills/qa-automation/scripts/validate_json.py outputs/test_plan.json
# 테스트 실행
python scripts/run_all_tests.py --test-plan outputs/test_plan.json --base-url "http://localhost:3000"
# 리포트 생성
python scripts/generate_report.py --result outputs/test_result.json --output outputs/REPORT.md
# GitHub 이슈 생성
python scripts/create_github_issues.py --result outputs/test_result.json --state outputs/qa_state.yaml
```

## 폴더 구조

```
auto-tester/
├── .cursor/                 # Cursor용 설정
│   ├── agents/              # 서브에이전트 정의
│   └── skills/qa-automation/
│       ├── SKILL.md
│       └── scripts/         # 공통 Python 스크립트
├── .claude/                 # Claude Code용 설정 (구조 동일)
├── scripts/                 # 프로젝트 스크립트
│   ├── qa_cli.py            # YAML+CLI 상태 관리
│   ├── run_all_tests.py     # Action 기반 테스트 러너
│   ├── generate_report.py   # REPORT.md 생성
│   ├── create_github_issues.py
│   └── run_test.py          # 레거시
├── inputs/                  # 입력 파일
├── outputs/                 # 산출물
└── SPEC.md                  # 기술 명세 (단일 원본)
```

## 주의 사항

1. **테스트 URL**: 전체 URL 입력 필요 (예: `http://localhost:3000/page`)
2. **GitHub CLI**: Phase 5 사용 시 `gh auth login` 필요
3. **공유 스크립트**: `.cursor/skills/qa-automation/scripts/`는 모든 AI 도구가 공유

## 추가 문서

- [SPEC.md](SPEC.md) — 기술 명세 (Phase 수행 가이드, Key Conventions, 산출물)
- [COMPATIBILITY.md](COMPATIBILITY.md) — AI 도구별 상세 사용 방법
