# AI QA Automation

시나리오 문서(PPTX, DOCX, PDF, 이미지)를 분석하여 자동으로 테스트 시나리오를 생성하고, 참조 이미지 추출·화면 비교·구성 체크와 Playwright 웹 테스트를 수행하는 **AI 기반** QA 자동화 도구입니다.

**지원 AI 도구**: Cursor, Claude Code

> **v2 신규**: YAML + CLI 상태 관리로 Phase 중단/재개, 검증 게이트, 자동 리마인더 지원

## 주요 기능

- **문서 분석**: PPTX/DOCX/PDF/이미지에서 텍스트, 표, 노트, **삽입 이미지** 자동 추출 (통합 스크립트 `extract_document.py`)
- **참조 이미지 저장**: 기획서 슬라이드/페이지별 이미지를 `outputs/reference/`에 저장 → 화면 비교·구성 체크에 활용
- **화면 비교**: 참조 이미지와 실제 스크린샷 유사도 비교 (`compare_screenshot.py`)
- **구성 체크**: 기획서 기준 예상 표시 요소 리스트 도출 → 테스트 시 해당 요소 존재 여부 확인
- **AI 시나리오 생성**: AI를 활용한 테스트 시나리오 자동 작성
- **웹 자동화 테스트**: Playwright 기반의 브라우저 자동화 테스트
- **리포트 생성**: 테스트 결과를 Markdown 형식으로 출력
- **스크린샷 캡처**: 테스트 단계별 스크린샷 자동 저장
- **GitHub 이슈 등록**: 테스트 실패 시 자동으로 이슈 생성
- **실패 자동 수정**: 이슈 분석 후 테스트 코드 오류 자동 수정 및 재테스트
- **YAML 상태 관리**: Phase별 진행 상태를 `qa_state.yaml`에 기록, 중단 후 재개 가능
- **CLI 검증 게이트**: 이전 Phase 미완료·필수 산출물 없으면 다음 Phase 자동 거부

## 다중 AI 도구 지원

이 프로젝트는 여러 AI 코딩 도구에서 동일하게 사용할 수 있도록 설계되었습니다.

| AI 도구 | 폴더 | 사용 방법 | 상태 |
|---------|------|-----------|------|
| **Cursor** | `.cursor/` | `@qa-master`, "QA 자동화 시작" | ✅ 지원 |
| **Claude Code** | `.claude/` | Skill 자동 적용, `@qa-master` | ✅ 지원 |

### 폴더 구조

각 AI 도구는 자신의 폴더에서 독립적으로 설정을 읽습니다:

```
auto-tester/
├── .cursor/                 # Cursor용 설정
│   ├── agents/              # 서브에이전트 정의
│   │   ├── qa-master.md     # 워크플로우 총괄
│   │   ├── doc-analyst.md   # 문서 분석
│   │   ├── test-architect.md # 테스트 설계
│   │   ├── qa-executor.md   # 테스트 실행
│   │   └── auto-fixer.md    # 실패 테스트 자동 수정
│   └── skills/              # Skill 정의
│       └── qa-automation/   # QA 자동화 통합 Skill
│           ├── SKILL.md
│           └── scripts/     # 공통 Python 스크립트
│               ├── extract_document.py  # 통합 진입점
│               ├── extract_pptx.py
│               ├── extract_docx.py
│               ├── extract_pdf.py
│               ├── extract_images.py
│               ├── compare_screenshot.py
│               └── validate_json.py
├── .claude/                 # Claude Code용 설정
│   ├── CLAUDE.md            # 프로젝트 지침
│   ├── agents/              # 서브에이전트 정의 (Cursor와 동일 구조)
│   └── skills/              # Skill 정의 (Cursor와 동일 구조)
├── scripts/
│   ├── qa_cli.py            # YAML+CLI 상태 관리 도구 (v2 신규)
│   ├── generate_report.py   # REPORT.md 생성
│   ├── create_github_issues.py # GitHub 이슈 자동 등록
│   ├── run_all_tests.py     # Action 기반 테스트 러너
│   └── run_test.py          # 간단한 URL 테스트 러너 (레거시)
├── inputs/                  # 입력 파일 (PPTX, DOCX, PDF, 이미지)
├── outputs/                 # 출력 결과물
│   └── qa_state.yaml        # Phase 진행 상태 DB (자동 생성)
└── README.md
```

**공유 리소스:**
- Python 스크립트(`.cursor/skills/qa-automation/scripts/`)는 모든 AI 도구가 공유
- Claude Code는 상대 경로(`../../.cursor/...`)로 스크립트 참조

**상세 가이드:** [COMPATIBILITY.md](COMPATIBILITY.md) 참조

## 사전 준비

### 1. 필수 패키지 설치

```bash
pip install -r requirements.txt
playwright install chromium
```

또는 개별 설치:
```bash
pip install playwright python-pptx python-docx PyMuPDF Pillow imagehash pyyaml
playwright install chromium
```

### 2. 시나리오 문서 준비

테스트할 기획서를 `inputs/` 폴더에 배치합니다. 지원 포맷: **PPTX**, **DOCX**, **PDF**, **이미지**(PNG/JPG).

---

## 사용 방법

### 전체 자동화 실행

```bash
# 1. 세션 초기화
python scripts/qa_cli.py init
```

**Cursor 채팅:**
```
@qa-master QA 자동화 시작해줘
```

**Claude Code 채팅:**
```
QA 자동화 시작해줘
```

### 단계별 직접 실행

```bash
# Phase 0: 사전 검증
python scripts/qa_cli.py start 0
python scripts/qa_cli.py set test_url http://localhost:3000
python scripts/qa_cli.py set github_repo owner/repo
python scripts/qa_cli.py complete 0
```

**Phase 1: 문서 분석**

Cursor: `@doc-analyst inputs/ 기획서 분석해줘`
Claude Code: `@doc-analyst inputs/ 기획서 분석해줘`
```bash
python scripts/qa_cli.py start 1
python .cursor/skills/qa-automation/scripts/extract_document.py inputs/ --output outputs
python scripts/qa_cli.py complete 1 --files outputs/scenario_draft.md
```

**Phase 2: 테스트 설계**

Cursor: `@test-architect test_plan.json 만들어줘`
Claude Code: `@test-architect test_plan.json 만들어줘`
```bash
python scripts/qa_cli.py start 2
python scripts/qa_cli.py complete 2 --files outputs/test_plan.json
```

**Phase 3: 테스트 실행**

Cursor: `@qa-executor 테스트 실행해줘`
Claude Code: `@qa-executor 테스트 실행해줘`
```bash
python scripts/qa_cli.py start 3
python scripts/run_all_tests.py --test-plan outputs/test_plan.json --base-url "http://localhost:3000"
python scripts/qa_cli.py complete 3 --files outputs/test_result.json
```

```bash
# Phase 4: 리포트 생성
python scripts/qa_cli.py start 4
python scripts/generate_report.py --result outputs/test_result.json --output outputs/REPORT.md
python scripts/qa_cli.py complete 4 --files outputs/REPORT.md

# Phase 5: GitHub 이슈 등록
python scripts/qa_cli.py start 5
python scripts/create_github_issues.py --result outputs/test_result.json --state outputs/qa_state.yaml
python scripts/qa_cli.py complete 5 --files outputs/issues_created.json
```

**Phase 5.5: 실패 자동 수정 (선택)**

Cursor: `@auto-fixer 실패 테스트 수정해줘`
Claude Code: `@auto-fixer 실패 테스트 수정해줘`
```bash
python scripts/qa_cli.py start 5.5
python scripts/qa_cli.py complete 5.5 --files outputs/fix_log.json
```

```bash
# Phase 6: 정리
python scripts/qa_cli.py start 6
python scripts/qa_cli.py complete 6
```

### 상태 확인 및 재개

```bash
python scripts/qa_cli.py status          # 전체 Phase 현황
python scripts/qa_cli.py next            # 다음 할 일 안내
python scripts/qa_cli.py resume          # 중단 지점 재개
python scripts/qa_cli.py fail <N> "사유" # Phase 실패 기록
```

---

## 워크플로우

```
사용자 → "QA 자동화 시작해줘"
         │
         ▼
[CLI] qa_cli.py init → outputs/qa_state.yaml 생성
         │
         ▼  [GATE] Phase 0 완료 확인
┌────────────────────────────────────────────────┐
│  Phase 0: 사전 검증                             │
│  • GitHub CLI 설치/로그인 확인                  │
│  ★ 사용자 입력: 테스트 URL, GitHub Repo         │
│  • qa_cli.py set test_url / set github_repo     │
└────────────────────────────────────────────────┘
         │
         ▼  [GATE] Phase 0 completed + inputs/ 문서 존재
┌────────────────────────────────────────────────┐
│  Phase 1: 문서 분석 (doc-analyst)               │
│  • inputs/ PPTX/DOCX/PDF/이미지 분석            │
│  • outputs/scenario_draft.md 생성               │
│  • outputs/reference/ 참조 이미지 저장           │
└────────────────────────────────────────────────┘
         │
         ▼  [GATE] Phase 1 completed + scenario_draft.md 존재
┌────────────────────────────────────────────────┐
│  Phase 2: 테스트 설계 (test-architect)          │
│  • outputs/test_plan.json 생성 (5개 카테고리)   │
│  • validate_json.py로 유효성 검증               │
└────────────────────────────────────────────────┘
         │
         ▼  [GATE] Phase 2 completed + test_plan.json 존재
┌────────────────────────────────────────────────┐
│  Phase 3: 테스트 실행 (qa-executor)             │
│  • Playwright로 브라우저 자동화 테스트           │
│  • 화면 비교(참조 이미지 vs 스크린샷)            │
│  • outputs/test_result.json 생성                │
└────────────────────────────────────────────────┘
         │
         ▼  [GATE] Phase 3 completed + test_result.json 존재
┌────────────────────────────────────────────────┐
│  Phase 4: 리포트 생성                           │
│  • outputs/REPORT.md 생성                       │
└────────────────────────────────────────────────┘
         │
         ▼  [GATE] Phase 4 completed + REPORT.md 존재
┌────────────────────────────────────────────────┐
│  Phase 5: GitHub 이슈 등록                      │
│  • 실패 테스트 → GitHub Issues 자동 등록         │
│  • outputs/issues_created.json 생성             │
└────────────────────────────────────────────────┘
         │
         ▼  [GATE] Phase 5 completed (선택)
┌────────────────────────────────────────────────┐
│  Phase 5.5: 실패 자동 수정 (auto-fixer) [선택]  │
│  ★ 사용자 승인 필요                             │
│  • 실패 원인 분석 (테스트 코드 vs 앱 버그)       │
│  • outputs/fix_log.json 생성                    │
└────────────────────────────────────────────────┘
         │
         ▼  [GATE] Phase 4 completed (최소 조건)
┌────────────────────────────────────────────────┐
│  Phase 6: 정리 (Cleanup)                        │
│  • 임시 파일 삭제, 최종 산출물 확인              │
└────────────────────────────────────────────────┘

[GATE] = qa_cli.py가 이전 Phase 미완료 시 exit code 2로 자동 거부
```

---

## 서브에이전트 직접 호출

특정 단계만 실행하고 싶을 때 사용합니다.
(각 에이전트는 내부적으로 `qa_cli.py start/complete`를 호출하여 상태를 관리합니다.)

### 문서 분석만 실행
```
@doc-analyst inputs/ 기획서 분석해줘
```

### 테스트 설계만 실행
```
@test-architect test_plan.json 만들어줘
```

### 테스트만 실행
```
@qa-executor 테스트 실행해줘
```

### 실패 테스트 자동 수정
```
@auto-fixer 실패 테스트 수정해줘
```

### CLI 상태 직접 확인/조작
```bash
python scripts/qa_cli.py status           # 전체 Phase 현황
python scripts/qa_cli.py next             # 다음 할 일 안내
python scripts/qa_cli.py resume           # 중단 지점 재개
python scripts/qa_cli.py start <N>        # Phase N 시작 (검증 게이트 통과 시)
python scripts/qa_cli.py complete <N>     # Phase N 완료 처리
python scripts/qa_cli.py fail <N> "사유"  # Phase N 실패 기록
```

---

## 주의 사항

1. **테스트 URL 형식**: 전체 URL을 입력해야 합니다 (프로토콜 포함)
   - 올바른 예: `http://localhost:3000/page`
   - 잘못된 예: `localhost:3000/page`

2. **사전 동작 선택자**: CSS 선택자 형식으로 입력합니다
   - `button.start` - class가 start인 button
   - `#login-btn` - id가 login-btn인 요소
   - `[data-testid="submit"]` - data-testid 속성 선택

3. **인증이 필요한 페이지**: URL에 쿼리 파라미터로 인증 정보를 포함하거나, 사전 동작으로 로그인 버튼 클릭을 지정합니다.

---

## Skill vs 서브에이전트

본 프로젝트는 두 가지 방식으로 QA 자동화를 실행할 수 있습니다.

| 방식 | 경로 | 특징 |
|------|------|------|
| **Skill** | `.cursor/skills/qa-automation/` | 전체 워크플로우 자동 적용, 빠른 실행 |
| **서브에이전트** | `.cursor/agents/` | 개별 Phase 실행, 세밀한 커스터마이징 |

### Skill 자동 트리거 키워드

다음 키워드 입력 시 qa-automation skill이 자동 적용됩니다:
- "QA 자동화"
- "테스트 시작"
- "기획서 분석"
- "QA 테스트"

---

## YAML + CLI 상태 관리 (v2)

QA 자동화 워크플로우의 신뢰성을 위해 `scripts/qa_cli.py` 가 상태 DB 역할을 합니다.

### 핵심 동작 원리

| 원칙 | 설명 |
|------|------|
| **YAML = 상태 DB** | `outputs/qa_state.yaml`에 Phase별 status, 설정값, 산출물 경로 기록 |
| **CLI = 검증 게이트** | 이전 Phase 미완료·필수 파일 없으면 exit code 2로 거부 |
| **CLI = 다음 행동 결정** | `next` 명령이 현재 상태를 읽어 "다음 할 일 1개"를 지시 |
| **자동 리마인더** | 모든 명령 실행 후 다음 할 일 + 경고 + 랜덤 팁 2개 출력 |

### qa_state.yaml 구조

```yaml
session:
  id: "QA_20260316_090000"
  overall_status: "in_progress"
config:
  test_url: "http://localhost:3000"
  github_repo: "owner/repo"
  skip_github: false
phases:
  "0": { name: "사전 검증", status: "completed", ... }
  "1": { name: "문서 분석",  status: "in_progress", ... }
  "2": { name: "테스트 설계", status: "pending", ... }
  ...
```

### 검증 게이트 예시

```bash
# Phase 2 시작 시도 → Phase 1 미완료면 자동 거부
python scripts/qa_cli.py start 2

# [GATE BLOCKED] Phase 2 시작 거부
# 사유: Phase 1 (문서 분석)이(가) 완료되지 않았습니다.
# 해결 방법: python scripts/qa_cli.py complete 1
```

---

## 유틸리티 스크립트

### 시나리오 문서 추출 (통합, 다중 포맷)

```bash
python .cursor/skills/qa-automation/scripts/extract_document.py inputs/ --output outputs
```

### PPTX만 추출

```bash
python .cursor/skills/qa-automation/scripts/extract_pptx.py inputs/파일명.pptx
```

### 화면 비교 (참조 이미지 vs 스크린샷)

```bash
python .cursor/skills/qa-automation/scripts/compare_screenshot.py outputs/reference/slide_6.png outputs/screenshot_01_initial.png --threshold 10
```

### test_plan.json 검증

```bash
python .cursor/skills/qa-automation/scripts/validate_json.py outputs/test_plan.json
```

### 테스트 실행 (Action 기반 러너)

```bash
python scripts/run_all_tests.py --test-plan outputs/test_plan.json --base-url "http://localhost:3000"
```

### REPORT.md 생성

```bash
python scripts/generate_report.py --result outputs/test_result.json --output outputs/REPORT.md
```

### GitHub 이슈 생성

```bash
python scripts/create_github_issues.py --result outputs/test_result.json --state outputs/qa_state.yaml
# gh 없이 확인만 하려면:
python scripts/create_github_issues.py --dry-run
```

---

## 출력 파일

테스트 완료 후 `outputs/` 폴더에 생성되는 파일:

| 파일 | 설명 |
|------|------|
| `qa_state.yaml` | Phase 진행 상태 DB (자동 생성/관리) |
| `scenario_draft.md` | 테스트 시나리오 |
| `extract_result.json` | 문서 추출 결과 (페이지/참조 이미지) |
| `scenario_draft_source.md` | 추출 요약 + 구성 체크 리스트 |
| `reference/*.png` | 기획서 참조 이미지 (화면 비교용) |
| `test_plan.json` | JSON 테스트 플랜 |
| `test_result.json` | 테스트 실행 결과 |
| `REPORT.md` | 최종 테스트 리포트 |
| `screenshot_TC_*.png` | 테스트 스크린샷 (`screenshot_TC_{tc_id}_{description}.png`) |
| `issues_created.json` | 생성된 GitHub 이슈 목록 |
| `fix_log.json` | 자동 수정 이력 (수정 시) |

---

## 기술 스택

- **AI Skills & Agents** - Cursor, Claude Code 지원
- **qa_cli.py** - YAML+CLI 상태 관리 (Phase 게이트, 리마인더)
- **Playwright** - 웹 브라우저 자동화
- **python-pptx** - PPTX 파싱 및 이미지 추출
- **python-docx** - DOCX 파싱
- **PyMuPDF** - PDF 파싱 및 페이지 렌더
- **Pillow, imagehash** - 화면 비교(참조 vs 스크린샷)
- **PyYAML** - 상태 파일 읽기/쓰기

---

## 추가 문서

- [기술 명세](SPEC.md) - Phase별 수행 가이드 및 산출물 정의
- [호환성 가이드](COMPATIBILITY.md) - 각 AI 도구별 상세 사용 방법
- [Claude Code 프로젝트 지침](.claude/CLAUDE.md) - Claude Code 사용자용 가이드
- [Cursor Skills 문서](.cursor/skills/qa-automation/SKILL.md) - Cursor 사용자용 가이드
