# AI 도구 호환성 가이드

이 문서는 AI QA Automation 프로젝트를 다양한 AI 코딩 도구에서 사용하는 방법을 설명합니다.

## 지원 AI 도구

| AI 도구 | 버전 | 상태 | 폴더 |
|---------|------|------|------|
| Cursor (Antigravity) | 최신 | ✅ 완전 지원 | `.cursor/` |
| Claude Code | 최신 | ✅ 완전 지원 | `.claude/` |

## 빠른 시작

### Cursor (Antigravity)

1. **프로젝트 열기**
   ```
   Cursor IDE에서 프로젝트 폴더 열기
   ```

2. **QA 자동화 시작**
   ```
   QA 자동화 시작해줘
   ```
   또는
   ```
   @qa-master 워크플로우 실행해줘
   ```

3. **Skill 자동 트리거**
   - "QA 자동화"
   - "테스트 시작"
   - "기획서 분석"
   - "QA 테스트"

### Claude Code

1. **프로젝트 열기**
   ```
   Claude Code에서 프로젝트 폴더 열기
   ```

2. **QA 자동화 시작**
   ```
   QA 자동화 시작해줘
   ```
   또는
   ```
   @qa-master 워크플로우 실행해줘
   ```

3. **프로젝트 지침 참조**
   - `.claude/CLAUDE.md` 파일이 자동으로 로드됨
   - 프로젝트 컨텍스트가 AI에게 전달됨

## 상세 사용 가이드

### 1. 문서 분석 (Phase 1)

#### Cursor
```
@doc-analyst inputs/ 기획서 분석해줘
```

#### Claude Code
```
@doc-analyst inputs/ 기획서 분석해줘
```

**공통 동작:**
- `inputs/` 폴더에서 시나리오 문서 찾기
- 통합 스크립트로 내용 추출:
  ```bash
  # Cursor
  python .cursor/skills/qa-automation/scripts/extract_document.py inputs/ --output outputs
  
  # Claude Code
  python ../../.cursor/skills/qa-automation/scripts/extract_document.py inputs/ --output outputs
  ```
- `outputs/scenario_draft.md` 생성

### 2. 테스트 설계 (Phase 2)

#### Cursor
```
@test-architect test_plan.json 생성해줘
```

#### Claude Code
```
@test-architect test_plan.json 생성해줘
```

**공통 동작:**
- `outputs/scenario_draft.md` 읽기
- JSON 테스트 플랜으로 변환
- `outputs/test_plan.json` 저장

### 3. 테스트 실행 (Phase 3)

#### Cursor
```
@qa-executor 테스트 실행해줘
```

#### Claude Code
```
@qa-executor 테스트 실행해줘
```

**공통 동작:**
- 사용자에게 URL, 사전 동작 요청
- Playwright로 브라우저 자동화 테스트 수행
- 스크린샷 캡처 및 화면 비교
- `outputs/test_result.json` 저장

### 4. 실패 테스트 자동 수정 (Phase 5.5)

#### Cursor
```
@auto-fixer 실패 테스트 수정해줘
```

#### Claude Code
```
@auto-fixer 실패 테스트 수정해줘
```

**공통 동작:**
- GitHub 이슈 확인하여 실패 테스트 파악
- 실제 DOM 분석으로 실패 원인 분류 (테스트 코드 오류 vs 앱 버그)
- 사용자 승인 후 선택자/기대값 수정 적용
- 수정된 테스트만 재실행
- `outputs/fix_log.json` 생성

### 5. 전체 워크플로우 실행

#### Cursor
```
@qa-master QA 자동화 시작해줘
```
또는
```
QA 자동화 시작해줘
```

#### Claude Code
```
@qa-master QA 자동화 시작해줘
```
또는
```
QA 자동화 시작해줘
```

**공통 동작:**
- Phase 0: 사전 검증
- Phase 1: 문서 분석
- Phase 2: 테스트 설계
- Phase 3: 테스트 실행
- Phase 4: 리포트 생성
- Phase 5: GitHub 이슈 등록
- Phase 5.5: 실패 자동 수정 (선택, 사용자 승인 필요)

## 기능 비교표

| 기능 | Cursor | Claude Code | 차이점 |
|------|--------|-------------|--------|
| Agent 호출 | `@agent-name` | `@agent-name` | 동일 |
| Skill 자동 트리거 | ✅ 지원 | ✅ 지원 | 동일 |
| 문서 분석 | ✅ 지원 | ✅ 지원 | 동일 |
| 테스트 설계 | ✅ 지원 | ✅ 지원 | 동일 |
| 테스트 실행 | ✅ 지원 | ✅ 지원 | 동일 |
| 화면 비교 | ✅ 지원 | ✅ 지원 | 동일 |
| 구성 체크 | ✅ 지원 | ✅ 지원 | 동일 |
| GitHub 이슈 등록 | ✅ 지원 | ✅ 지원 | 동일 |
| 실패 자동 수정 | ✅ 지원 | ✅ 지원 | 동일 |
| 스크립트 경로 | `.cursor/...` | `../../.cursor/...` | 상대 경로 차이 |
| 프로젝트 지침 | `.cursor/skills/qa-automation/SKILL.md` | `.claude/CLAUDE.md` | 파일 위치 차이 |

## 주요 차이점

### 1. 폴더 구조

#### Cursor
```
.cursor/
├── agents/
│   ├── qa-master.md
│   ├── doc-analyst.md
│   ├── test-architect.md
│   ├── qa-executor.md
│   └── auto-fixer.md
└── skills/
    └── qa-automation/
        ├── SKILL.md
        └── scripts/        # 공통 스크립트
```

#### Claude Code
```
.claude/
├── CLAUDE.md               # 프로젝트 지침
├── agents/
│   ├── qa-master.md
│   ├── doc-analyst.md
│   ├── test-architect.md
│   ├── qa-executor.md
│   └── auto-fixer.md
└── skills/
    └── qa-automation/
        └── SKILL.md
```

### 2. 메타데이터 필드

#### Cursor Agent
```yaml
---
name: doc-analyst
model: default
description: 시나리오 문서 분석 전문가...
---
```

#### Claude Code Agent
```yaml
---
name: doc-analyst
model: default
description: 시나리오 문서 분석 전문가...
allowed-tools: Read, Shell, Write, Glob, Grep
---
```

**차이점:** Claude Code는 `allowed-tools` 필드 추가

### 3. 스크립트 경로

#### Cursor
```bash
python .cursor/skills/qa-automation/scripts/extract_document.py inputs/ --output outputs
```

#### Claude Code
```bash
python ../../.cursor/skills/qa-automation/scripts/extract_document.py inputs/ --output outputs
```

**이유:** Claude Code는 `.claude/` 폴더에서 실행되므로 상대 경로로 `.cursor/` 폴더의 스크립트 참조

### 4. 프로젝트 지침 파일

| AI 도구 | 파일 위치 | 설명 |
|---------|----------|------|
| Cursor | `.cursor/skills/qa-automation/SKILL.md` | Skill 정의 파일에 전체 가이드 포함 |
| Claude Code | `.claude/CLAUDE.md` | 별도 프로젝트 지침 파일, 자동 로드됨 |

## 공통 리소스

### Python 스크립트
모든 AI 도구가 동일한 Python 스크립트를 공유합니다:

```
.cursor/skills/qa-automation/scripts/
├── extract_document.py     # 통합 진입점
├── extract_pptx.py         # PPTX 추출
├── extract_docx.py         # DOCX 추출
├── extract_pdf.py          # PDF 추출
├── extract_images.py       # 이미지 추출
├── compare_screenshot.py   # 화면 비교
└── validate_json.py        # JSON 검증
```

**장점:**
- 중복 없이 한 번만 관리
- 버그 수정 시 모든 AI 도구에 자동 반영
- 일관된 동작 보장

### 출력 파일
모든 AI 도구가 동일한 출력 파일을 생성합니다:

```
outputs/
├── scenario_draft.md           # 테스트 시나리오
├── extract_result.json         # 문서 추출 결과
├── scenario_draft_source.md    # 추출 요약 + 구성 체크
├── reference/                  # 참조 이미지
│   ├── slide_*.png
│   └── page_*.png
├── test_plan.json              # JSON 테스트 플랜
├── test_result.json            # 테스트 실행 결과
├── REPORT.md                   # 최종 리포트
├── screenshot_*.png            # 스크린샷
├── issues_created.json         # 생성된 이슈 목록
└── fix_log.json               # 자동 수정 이력 (수정 시)
```

## 제약사항

### Cursor (Antigravity)
- 제약 없음: 모든 기능 완전 지원

### Claude Code
- **브라우저 자동화**: MCP 서버를 통한 브라우저 제어 필요
- **로컬 네트워크**: 제한 없음 (전체 접근 가능)
- **패키지 설치**: 사전에 Python 패키지 설치 필요

## 트러블슈팅

### 경로 오류

#### 증상
```
FileNotFoundError: [Errno 2] No such file or directory: '.cursor/skills/qa-automation/scripts/extract_document.py'
```

#### 해결 방법

**Cursor:**
```bash
# 절대 경로 확인
cd /path/to/auto-tester
python .cursor/skills/qa-automation/scripts/extract_document.py inputs/ --output outputs
```

**Claude Code:**
```bash
# 상대 경로 확인 (.claude/ 폴더 기준)
python ../../.cursor/skills/qa-automation/scripts/extract_document.py inputs/ --output outputs
```

### Agent를 찾을 수 없음

#### 증상
```
Agent 'qa-master' not found
```

#### 해결 방법

**Cursor:**
1. `.cursor/agents/qa-master.md` 파일 존재 확인
2. Cursor IDE 재시작

**Claude Code:**
1. `.claude/agents/qa-master.md` 파일 존재 확인
2. Claude Code 재시작

### 스크립트 실행 오류

#### 증상
```
ModuleNotFoundError: No module named 'pptx'
```

#### 해결 방법
```bash
# 의존성 재설치
pip install -r requirements.txt
playwright install chromium
```

### GitHub CLI 오류

#### 증상
```
gh: command not found
```

#### 해결 방법

**Windows:**
```powershell
winget install GitHub.cli
```

**macOS:**
```bash
brew install gh
```

**Linux:**
```bash
# Debian/Ubuntu
sudo apt install gh

# Fedora
sudo dnf install gh
```

**로그인:**
```bash
gh auth login
```

## 성능 비교

| 항목 | Cursor | Claude Code | 비고 |
|------|--------|-------------|------|
| Agent 로딩 속도 | ⚡ 빠름 | ⚡ 빠름 | 비슷함 |
| 스크립트 실행 속도 | ⚡ 빠름 | ⚡ 빠름 | 동일 |
| 브라우저 자동화 | ⚡ 빠름 | ⚡ 빠름 | 동일 |
| 메모리 사용량 | 낮음 | 낮음 | 동일 |

## 마이그레이션 가이드

### Cursor에서 Claude Code로

1. **프로젝트 구조 확인**
   - `.claude/` 폴더가 이미 생성되어 있음
   - 추가 작업 필요 없음

2. **사용 방법**
   - Cursor에서 사용하던 명령어 그대로 사용 가능
   - `@agent-name` 호출 방식 동일
   - "QA 자동화 시작해줘" 동일하게 동작

3. **차이점 인지**
   - 프로젝트 지침은 `.claude/CLAUDE.md` 참조
   - Agent 정의는 `.claude/agents/` 참조

### Claude Code에서 Cursor로

1. **프로젝트 구조 확인**
   - `.cursor/` 폴더가 이미 생성되어 있음
   - 추가 작업 필요 없음

2. **사용 방법**
   - Claude Code에서 사용하던 명령어 그대로 사용 가능
   - `@agent-name` 호출 방식 동일
   - "QA 자동화 시작해줘" 동일하게 동작

3. **차이점 인지**
   - 프로젝트 지침은 `.cursor/skills/qa-automation/SKILL.md` 참조
   - Agent 정의는 `.cursor/agents/` 참조

## 유지보수 가이드

### 기능 추가 시

1. **Cursor 버전 수정 (원본)**
   - `.cursor/agents/` 또는 `.cursor/skills/` 수정
   - 테스트 수행

2. **Claude Code 버전 동기화**
   - `.claude/agents/` 또는 `.claude/skills/`에 동일 변경 사항 반영
   - 스크립트 경로 확인 (상대 경로 조정)
   - 테스트 수행

3. **공통 스크립트 수정**
   - `.cursor/skills/qa-automation/scripts/`에서 한 번만 수정
   - 모든 AI 도구에 자동 반영됨

### 버전 관리

```bash
# Git에 모두 커밋
git add .cursor/ .claude/
git commit -m "Update: QA automation agents and skills"
git push
```

**주의:** 
- `.claude/settings.local.json`은 gitignore에 포함됨 (개인 설정)
- 나머지 파일은 모두 버전 관리됨

## FAQ

### Q1. 두 AI 도구를 동시에 사용할 수 있나요?
**A.** 네, 가능합니다. 각 도구는 자신의 폴더(`.cursor/`, `.claude/`)에서 독립적으로 동작하며, 공통 스크립트를 공유합니다.

### Q2. Cursor 버전과 Claude Code 버전의 기능이 다른가요?
**A.** 아니요, 완전히 동일합니다. 폴더 구조와 스크립트 경로만 다르고, 모든 기능은 동일하게 작동합니다.

### Q3. 어떤 AI 도구를 사용해야 하나요?
**A.** 현재 사용 중인 AI 코딩 도구를 그대로 사용하시면 됩니다. 둘 다 동일한 경험을 제공합니다.

### Q4. 다른 팀원이 다른 AI 도구를 사용해도 되나요?
**A.** 네, 문제없습니다. Git으로 프로젝트를 공유하면 각자 선호하는 AI 도구로 작업할 수 있습니다.

### Q5. Python 스크립트를 수정하면 어떻게 되나요?
**A.** `.cursor/skills/qa-automation/scripts/`의 스크립트를 수정하면 Cursor와 Claude Code 모두에 자동으로 반영됩니다.

### Q6. 새로운 AI 도구 지원 계획이 있나요?
**A.** 현재는 Cursor와 Claude Code만 지원합니다. 향후 다른 AI 도구 지원이 필요하면 동일한 패턴으로 추가할 수 있습니다.

## 지원 및 문의

- **이슈 보고**: GitHub Issues
- **문서 개선 제안**: Pull Request 환영
- **질문**: GitHub Discussions

## 관련 문서

- [README.md](README.md) - 프로젝트 개요
- [.claude/CLAUDE.md](.claude/CLAUDE.md) - Claude Code 프로젝트 지침
- [.cursor/skills/qa-automation/SKILL.md](.cursor/skills/qa-automation/SKILL.md) - Cursor Skill 정의
