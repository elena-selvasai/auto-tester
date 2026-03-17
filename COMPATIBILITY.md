# AI 도구 호환성 가이드

Cursor와 Claude Code는 동일한 기능을 제공합니다. 차이점은 설정 폴더와 프로젝트 지침 파일 위치뿐입니다.

> **상세 사양**: [SPEC.md](SPEC.md) | **전체 가이드**: [README.md](README.md)

## 지원 AI 도구

| AI 도구 | 설정 폴더 | 프로젝트 지침 | 상태 |
|---------|----------|-------------|------|
| Cursor | `.cursor/` | `.cursor/skills/qa-automation/SKILL.md` | ✅ 완전 지원 |
| Claude Code | `.claude/` | `.claude/CLAUDE.md` (자동 로드) | ✅ 완전 지원 |

## 폴더 구조 차이

### Cursor
```
.cursor/
├── agents/
│   ├── qa-master.md, doc-analyst.md, test-architect.md
│   ├── qa-executor.md, auto-fixer.md
└── skills/qa-automation/
    ├── SKILL.md
    └── scripts/          # 공통 Python 스크립트
```

### Claude Code
```
.claude/
├── CLAUDE.md             # 프로젝트 지침 (자동 로드)
├── agents/
│   └── (Cursor와 동일)
└── skills/qa-automation/
    └── SKILL.md          # scripts/ 없음 (Cursor의 것 공유)
```

### 공통 (프로젝트 루트)
```
scripts/qa_cli.py                      # YAML+CLI 상태 관리 (양쪽 공유)
.cursor/skills/qa-automation/scripts/  # 공통 Python 스크립트 (양쪽 공유)
```

## 실제 차이점

| 항목 | Cursor | Claude Code |
|------|--------|-------------|
| 설정 폴더 | `.cursor/` | `.claude/` |
| 프로젝트 지침 | `SKILL.md` | `CLAUDE.md` (자동 로드) |
| Agent 메타데이터 | `model`, `description` | + `allowed-tools` 필드 추가 |
| Python 스크립트 경로 | 프로젝트 루트 기준 | 프로젝트 루트 기준 (동일) |

## 스크립트 경로 (공통)

**두 도구 모두 프로젝트 루트 기준으로 동일한 경로를 사용합니다.**

```bash
python .cursor/skills/qa-automation/scripts/extract_document.py inputs/ --output outputs
python .cursor/skills/qa-automation/scripts/validate_json.py outputs/test_plan.json
python .cursor/skills/qa-automation/scripts/compare_screenshot.py ref.png screenshot.png
python scripts/qa_cli.py status
```

## 빠른 시작

두 도구 모두 동일한 명령어로 시작합니다:

```bash
python scripts/qa_cli.py init
```

채팅창에서:
```
QA 자동화 시작해줘
```

또는 특정 에이전트 직접 호출:
```
@qa-master QA 자동화 시작해줘
@doc-analyst inputs/ 기획서 분석해줘
@test-architect test_plan.json 만들어줘
@qa-executor 테스트 실행해줘
@auto-fixer 실패 테스트 수정해줘
```

## 유지보수 (기능 추가 시 수정 순서)

1. `.cursor/agents/` 또는 `.cursor/skills/` 먼저 수정 (원본)
2. `.claude/agents/` 또는 `.claude/skills/`에 동일 변경 반영
3. 공유 Python 스크립트는 `.cursor/skills/qa-automation/scripts/`에서만 수정
4. `scripts/qa_cli.py`는 양쪽이 공유하므로 한 번만 수정

## 트러블슈팅

### 경로 오류

```
FileNotFoundError: '.cursor/skills/qa-automation/scripts/extract_document.py'
```

**해결**: 프로젝트 루트에서 실행했는지 확인합니다. Cursor와 Claude Code 모두 동일.

```bash
cd /path/to/auto-tester
python .cursor/skills/qa-automation/scripts/extract_document.py inputs/ --output outputs
```

### Agent를 찾을 수 없음

- **Cursor**: `.cursor/agents/qa-master.md` 파일 존재 확인 후 IDE 재시작
- **Claude Code**: `.claude/agents/qa-master.md` 파일 존재 확인 후 재시작

### Python 패키지 오류

```bash
pip install -r requirements.txt
playwright install chromium
```

### GitHub CLI 오류

```bash
gh auth login     # 로그인
gh auth status    # 상태 확인
```

Windows: `winget install GitHub.cli` / macOS: `brew install gh`

## 관련 문서

- [README.md](README.md) - 프로젝트 개요
- [SPEC.md](SPEC.md) - 기술 명세 (단일 원본)
- [.claude/CLAUDE.md](.claude/CLAUDE.md) - Claude Code 프로젝트 지침
- [.cursor/skills/qa-automation/SKILL.md](.cursor/skills/qa-automation/SKILL.md) - Cursor Skill 정의
