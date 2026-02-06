# AI QA Automation

시나리오 문서(PPTX, DOCX, PDF, 이미지)를 분석하여 자동으로 테스트 시나리오를 생성하고, 참조 이미지 추출·화면 비교·구성 체크와 Playwright 웹 테스트를 수행하는 **Cursor 서브에이전트 및 Skill 기반** QA 자동화 도구입니다.

## 주요 기능

- **문서 분석**: PPTX/DOCX/PDF/이미지에서 텍스트, 표, 노트, **삽입 이미지** 자동 추출 (통합 스크립트 `extract_document.py`)
- **참조 이미지 저장**: 기획서 슬라이드/페이지별 이미지를 `outputs/reference/`에 저장 → 화면 비교·구성 체크에 활용
- **화면 비교**: 참조 이미지와 실제 스크린샷 유사도 비교 (`compare_screenshot.py`)
- **구성 체크**: 기획서 기준 예상 표시 요소 리스트 도출 → 테스트 시 해당 요소 존재 여부 확인
- **AI 시나리오 생성**: AI를 활용한 테스트 시나리오 자동 작성
- **웹 자동화 테스트**: Playwright 기반의 브라우저 자동화 테스트
- **리포트 생성**: 테스트 결과를 Markdown 형식으로 출력
- **스크린샷 캡처**: 테스트 단계별 스크린샷 자동 저장

## 프로젝트 구조

```
auto-tester/
├── .cursor/
│   ├── agents/              # Cursor 서브에이전트 정의
│   │   ├── qa-master.md     # 워크플로우 총괄
│   │   ├── doc-analyst.md   # PPTX 문서 분석
│   │   ├── test-architect.md # 테스트 케이스 설계
│   │   └── qa-executor.md   # 테스트 실행
│   └── skills/              # Cursor Skill 정의
│       └── qa-automation/   # QA 자동화 통합 Skill
│           ├── SKILL.md
│           └── scripts/
│               ├── extract_document.py  # 통합 진입점 (PPTX/DOCX/PDF/이미지)
│               ├── extract_pptx.py
│               ├── extract_docx.py
│               ├── extract_pdf.py
│               ├── extract_images.py
│               ├── compare_screenshot.py
│               └── validate_json.py
├── inputs/                  # 입력 파일 (PPTX, DOCX, PDF, 이미지)
├── outputs/                 # 출력 결과물
├── scripts/
│   └── run_test.py          # Playwright 테스트 스크립트
└── README.md
```

## 사전 준비

### 1. 필수 패키지 설치

```bash
pip install -r requirements.txt
playwright install chromium
```

또는 개별 설치:
```bash
pip install playwright python-pptx python-docx PyMuPDF Pillow imagehash
playwright install chromium
```

### 2. 시나리오 문서 준비

테스트할 기획서를 `inputs/` 폴더에 배치합니다. 지원 포맷: **PPTX**, **DOCX**, **PDF**, **이미지**(PNG/JPG).

---

## 사용 방법

### Step 1: QA 자동화 시작

Cursor 채팅창에 다음과 같이 입력합니다:

```
QA 자동화 시작해줘
```

### Step 2: 테스트 URL 및 사전 동작 입력

에이전트가 테스트 실행을 위해 다음 정보를 요청합니다:

| 항목 | 설명 | 예시 |
|------|------|------|
| **테스트 URL** | 테스트할 웹사이트 주소 | `http://localhost:3000` |
| **사전 동작** | 테스트 전 클릭할 요소 (선택) | `button.start`, `#login-btn` |

**입력 예시:**
```
url: http://localhost:3000

사전 동작: button.quiz-start (퀴즈 시작 버튼 클릭)
```

### Step 3: 결과 확인

테스트 완료 후 결과물이 생성됩니다:
- `outputs/scenario_draft.md` - 테스트 시나리오
- `outputs/extract_result.json` - 문서 추출 결과 (페이지/참조 이미지)
- `outputs/reference/` - 기획서에서 추출한 참조 이미지 (화면 비교용)
- `outputs/test_plan.json` - 테스트 플랜
- `outputs/REPORT.md` - 테스트 리포트
- `outputs/screenshot_*.png` - 스크린샷

---

## 워크플로우

```
┌─────────────────────────────────────────────────────────────────┐
│                    사용자 → "QA 자동화 시작해줘"                 │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│  Phase 1: 문서 분석 (doc-analyst)                               │
│  • inputs/ 시나리오 문서(PPTX/DOCX/PDF/이미지) 분석             │
│  • 참조 이미지 추출 → outputs/reference/                        │
│  • outputs/scenario_draft.md, extract_result.json 생성          │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│  Phase 2: 테스트 설계 (test-architect)                          │
│  • scenario_draft.md 분석                                       │
│  • outputs/test_plan.json 생성                                  │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│  Phase 3: 테스트 실행 (qa-executor)                             │
│  ★ 사용자 입력 필요: URL, 사전 동작                             │
│  • Playwright로 UI 테스트 수행, 스크린샷 캡처                   │
│  • 화면 비교(참조 이미지 vs 스크린샷), 구성 체크                 │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│  Phase 4: 리포트 생성                                           │
│  • outputs/REPORT.md 생성                                       │
└─────────────────────────────────────────────────────────────────┘
```

---

## 서브에이전트 직접 호출

특정 단계만 실행하고 싶을 때 사용합니다.

### 문서 분석만 실행
```
@doc-analyst inputs/ 기획서 분석해줘
```
(또는 `inputs/기획서.pptx`, `inputs/기획서.docx` 등 단일 파일 경로)

### 테스트만 실행
```
@qa-executor 테스트 실행해줘
```

에이전트가 URL과 사전 동작을 질문하면 다음과 같이 응답합니다:
```
url: http://localhost:3000/app
사전 동작: #start-button 클릭
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

---

## 출력 파일

테스트 완료 후 `outputs/` 폴더에 생성되는 파일:

| 파일 | 설명 |
|------|------|
| `scenario_draft.md` | 테스트 시나리오 |
| `extract_result.json` | 문서 추출 결과 (페이지/참조 이미지) |
| `scenario_draft_source.md` | 추출 요약 + 구성 체크 리스트 |
| `reference/*.png` | 기획서 참조 이미지 (화면 비교용) |
| `test_plan.json` | JSON 테스트 플랜 |
| `test_result.json` | 테스트 실행 결과 |
| `REPORT.md` | 최종 테스트 리포트 |
| `screenshot_*.png` | 테스트 스크린샷 (6개) |

---

## 기술 스택

- **Cursor Skills & Subagents** - AI 기반 워크플로우 자동화
- **Playwright** - 웹 브라우저 자동화
- **python-pptx** - PPTX 파싱 및 이미지 추출
- **python-docx** - DOCX 파싱
- **PyMuPDF** - PDF 파싱 및 페이지 렌더
- **Pillow, imagehash** - 화면 비교(참조 vs 스크린샷)
