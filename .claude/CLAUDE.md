# AI QA Automation - Claude Code 프로젝트 지침

이 프로젝트는 시나리오 문서(PPTX, DOCX, PDF, 이미지)를 분석하여 자동으로 테스트 시나리오를 생성하고, 참조 이미지 추출·화면 비교·구성 체크와 Playwright 웹 테스트를 수행하는 QA 자동화 도구입니다.

## 프로젝트 개요

### 주요 기능
- 문서 분석: PPTX/DOCX/PDF/이미지에서 텍스트, 표, 노트, 삽입 이미지 자동 추출
- 참조 이미지 저장: 기획서 슬라이드/페이지별 이미지를 저장하여 화면 비교에 활용
- 화면 비교: 참조 이미지와 실제 스크린샷 유사도 비교
- 구성 체크: 기획서 기준 예상 표시 요소 확인
- AI 시나리오 생성: AI를 활용한 테스트 시나리오 자동 작성
- 웹 자동화 테스트: Playwright 기반의 브라우저 자동화 테스트
- 리포트 생성: 테스트 결과를 Markdown 형식으로 출력
- GitHub 이슈 등록: 테스트 실패 시 자동으로 이슈 생성

### 기술 스택
- **Claude Code Skills & Agents**: AI 기반 워크플로우 자동화
- **Playwright**: 웹 브라우저 자동화
- **python-pptx**: PPTX 파싱 및 이미지 추출
- **python-docx**: DOCX 파싱
- **PyMuPDF**: PDF 파싱 및 페이지 렌더
- **Pillow, imagehash**: 화면 비교(참조 vs 스크린샷)

## 폴더 구조

```
auto-tester/
├── .claude/                    # Claude Code 전용 설정
│   ├── CLAUDE.md               # 이 파일 - 프로젝트 지침
│   ├── agents/                 # 서브에이전트 정의
│   │   ├── qa-master.md        # 워크플로우 총괄
│   │   ├── doc-analyst.md      # 문서 분석 전문가
│   │   ├── test-architect.md   # 테스트 설계 전문가
│   │   ├── qa-executor.md      # 테스트 실행 전문가
│   │   └── auto-fixer.md       # 실패 테스트 자동 수정 전문가
│   └── skills/
│       └── qa-automation/
│           └── SKILL.md        # QA 자동화 통합 Skill
├── .cursor/                    # Cursor/Antigravity용 설정 (원본)
│   ├── agents/                 # 동일한 구조
│   └── skills/
│       └── qa-automation/
│           ├── SKILL.md
│           └── scripts/        # 공통 Python 스크립트
│               ├── extract_document.py
│               ├── extract_pptx.py
│               ├── extract_docx.py
│               ├── extract_pdf.py
│               ├── extract_images.py
│               ├── compare_screenshot.py
│               └── validate_json.py
├── inputs/                     # 입력 파일 (PPTX, DOCX, PDF, 이미지)
├── outputs/                    # 출력 결과물
└── README.md
```

## 사용 방법

### 빠른 시작

Claude Code 채팅창에서 다음과 같이 입력:

```
QA 자동화 시작해줘
```

또는 특정 Agent를 직접 호출:

```
@qa-master 전체 워크플로우 실행해줘
```

### 단계별 실행

특정 Phase만 실행하려면 해당 Agent를 직접 호출:

#### 1. 문서 분석만 실행
```
@doc-analyst inputs/ 폴더의 기획서 분석해줘
```

#### 2. 테스트 설계만 실행
```
@test-architect scenario_draft.md를 test_plan.json으로 변환해줘
```

#### 3. 테스트 실행만 실행
```
@qa-executor 테스트 실행해줘
```

### 워크플로우 단계

```
Phase 0: 사전 검증
  ↓
Phase 1: 문서 분석 (doc-analyst)
  ↓
Phase 2: 테스트 설계 (test-architect)
  ↓
Phase 3: 테스트 실행 (qa-executor)
  ↓
Phase 4: 리포트 생성
  ↓
Phase 5: GitHub 이슈 등록
  ↓
Phase 5.5: 실패 수정 (auto-fixer) [선택]
```

#### Phase 0: 사전 검증
- GitHub CLI 설치 및 로그인 확인
- 테스트 URL 입력 요청
- GitHub 리포지토리 정보 입력 요청 (이슈 등록용)

#### Phase 1: 문서 분석
- `inputs/` 폴더에서 시나리오 문서 확인 (PPTX/DOCX/PDF/이미지)
- 통합 스크립트로 내용 및 참조 이미지 추출
- `outputs/scenario_draft.md` 생성
- `outputs/reference/` 폴더에 참조 이미지 저장

#### Phase 2: 테스트 설계
- scenario_draft.md를 읽어 JSON 테스트 플랜으로 변환
- 5개 카테고리 테스트 케이스 생성:
  - basic_function (기본 기능)
  - button_state (버튼 상태)
  - navigation (네비게이션)
  - edge_case (엣지 케이스)
  - accessibility (접근성)
- `outputs/test_plan.json` 생성

#### Phase 3: 테스트 실행
- 브라우저 자동화로 테스트 수행
- 각 단계별 스크린샷 캡처
- 참조 이미지와 화면 비교
- 구성 체크 리스트 검증
- `outputs/test_result.json` 생성

#### Phase 4: 리포트 생성
- 테스트 결과 취합
- `outputs/REPORT.md` 생성
- 카테고리별 통계 포함
- 스크린샷 목록 포함

#### Phase 5: GitHub 이슈 등록
- 테스트 실패 또는 불일치 발견 시
- 지정된 리포지토리에 이슈 자동 생성
- `outputs/issues_created.json`에 이슈 목록 저장

#### Phase 5.5: 실패 테스트 자동 수정 (선택)
- 이슈 등록 후 실패 건이 있으면 사용자에게 자동 수정 여부 확인
- 실제 DOM 분석으로 실패 원인 분류 (테스트 코드 오류 vs 앱 버그)
- 사용자 승인 후 선택자/기대값 수정 적용
- 수정된 테스트만 재실행
- `outputs/fix_log.json`에 수정 이력 기록

## 스크립트 경로 참조

Claude Code에서는 공통 Python 스크립트를 상대 경로로 참조합니다:

```bash
# 문서 추출
python ../../.cursor/skills/qa-automation/scripts/extract_document.py inputs/ --output outputs

# 화면 비교
python ../../.cursor/skills/qa-automation/scripts/compare_screenshot.py reference.png screenshot.png --threshold 10

# JSON 검증
python ../../.cursor/skills/qa-automation/scripts/validate_json.py outputs/test_plan.json
```

## 출력 파일

테스트 완료 후 `outputs/` 폴더에 생성되는 파일:

| 파일 | 설명 |
|------|------|
| `scenario_draft.md` | 테스트 시나리오 |
| `extract_result.json` | 문서 추출 결과 |
| `scenario_draft_source.md` | 추출 요약 + 구성 체크 리스트 |
| `reference/*.png` | 기획서 참조 이미지 |
| `test_plan.json` | JSON 테스트 플랜 (5개 카테고리) |
| `test_result.json` | 테스트 실행 결과 |
| `REPORT.md` | 최종 테스트 리포트 |
| `screenshot_*.png` | 테스트 스크린샷 |
| `issues_created.json` | 생성된 GitHub 이슈 목록 |
| `fix_log.json` | 자동 수정 이력 (수정 시) |

## Agent 사용 가이드

### @qa-master
- 역할: 전체 워크플로우 총괄
- 용도: 전체 Phase를 순차적으로 실행
- 호출 예: `@qa-master QA 자동화 시작해줘`

### @doc-analyst
- 역할: 시나리오 문서 분석 전문가
- 용도: PPTX/DOCX/PDF/이미지 분석 및 시나리오 추출
- 호출 예: `@doc-analyst inputs/기획서.pptx 분석해줘`

### @test-architect
- 역할: 테스트 케이스 설계 전문가
- 용도: Markdown 시나리오를 JSON 테스트 플랜으로 변환
- 호출 예: `@test-architect test_plan.json 생성해줘`

### @qa-executor
- 역할: 웹 테스트 실행 전문가
- 용도: Playwright로 브라우저 자동화 테스트 수행
- 호출 예: `@qa-executor 테스트 실행해줘`

### @auto-fixer
- 역할: 실패 테스트 분석 및 자동 수정 전문가
- 용도: GitHub 이슈 확인 후 테스트 코드 오류 분석, 사용자 승인 후 수정 적용 및 재테스트
- 호출 예: `@auto-fixer 실패 테스트 수정해줘`

## 주의사항

### 1. 스크립트 경로
Claude Code 버전은 `.cursor/skills/qa-automation/scripts/`의 Python 스크립트를 상대 경로(`../../.cursor/...`)로 참조합니다.

### 2. GitHub CLI 필수
GitHub 이슈 자동 등록 기능을 사용하려면:
- GitHub CLI 설치 필요
- `gh auth login`으로 로그인 필요
- 이슈 등록할 리포지토리 접근 권한 필요

### 3. Python 의존성
다음 패키지가 설치되어 있어야 합니다:
```bash
pip install playwright python-pptx python-docx PyMuPDF Pillow imagehash
playwright install chromium
```

### 4. 테스트 URL
- 전체 URL 입력 필요 (프로토콜 포함)
- 올바른 예: `http://localhost:3000/page`
- 잘못된 예: `localhost:3000/page`

### 5. 호환성
- 이 `.claude/` 폴더는 Claude Code 전용입니다
- Cursor/Antigravity 사용자는 `.cursor/` 폴더를 사용합니다
- 두 버전 모두 동일한 Python 스크립트를 공유합니다

## 코딩 스타일 가이드

### Python 스크립트
- PEP 8 스타일 가이드 준수
- 함수/클래스에 docstring 포함
- 타입 힌트 사용 권장
- 에러 핸들링 철저히 수행

### JSON 형식
- 들여쓰기 2칸 사용
- 키는 쌍따옴표 사용
- 배열/객체 마지막 요소에 쉼표 없음

### Markdown 문서
- 명확한 제목 계층 구조
- 코드 블록에 언어 명시
- 표는 가독성 있게 정렬

## 트러블슈팅

### GitHub CLI 오류
```bash
# 설치 확인
gh --version

# 로그인
gh auth login

# 상태 확인
gh auth status
```

### Python 스크립트 오류
```bash
# 의존성 재설치
pip install -r requirements.txt

# Playwright 브라우저 재설치
playwright install chromium
```

### 경로 오류
- 상대 경로가 올바른지 확인
- 작업 디렉토리가 프로젝트 루트인지 확인

## 추가 리소스

- [프로젝트 README](../../README.md)
- [호환성 가이드](../../COMPATIBILITY.md)
- [Cursor Skills 문서](../.cursor/skills/qa-automation/SKILL.md)

## 기여 가이드

이 프로젝트는 Cursor와 Claude Code 모두를 지원합니다. 기능 추가 시:

1. `.cursor/` 버전을 먼저 수정 (원본)
2. `.claude/` 버전에 동일 변경 사항 반영
3. 스크립트는 `.cursor/skills/qa-automation/scripts/`에서 한 번만 수정
4. 경로 참조가 올바른지 확인

## 라이선스

이 프로젝트는 MIT 라이선스를 따릅니다.
