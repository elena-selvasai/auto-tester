# 🤖 AI QA Automation

PPTX 기획서를 분석하여 자동으로 테스트 시나리오를 생성하고, Playwright로 웹 테스트를 수행하는 AI 기반 QA 자동화 도구입니다.

## 📋 목차

- [주요 기능](#-주요-기능)
- [프로젝트 구조](#-프로젝트-구조)
- [설치 방법](#-설치-방법)
- [환경 설정](#-환경-설정)
- [사용 방법](#-사용-방법)
- [워크플로우](#-워크플로우)

## ✨ 주요 기능

- **📄 문서 분석**: PPTX 기획서에서 텍스트, 표, 노트를 자동 추출
- **🧠 AI 시나리오 생성**: Google Gemini AI를 활용한 테스트 시나리오 자동 작성
- **🎭 웹 자동화 테스트**: Playwright 기반의 브라우저 자동화 테스트
- **📊 리포트 생성**: 테스트 결과를 HTML/Excel 형식으로 출력

## 📁 프로젝트 구조

```
auto-tester/
├── 📁 scripts/              # 실행 스크립트
│   ├── doc_analyst.py       # PPTX 분석 및 시나리오 생성
│   └── setup_project.py     # 프로젝트 초기화
├── 📁 ai-qa-automation/     # 생성된 프로젝트 폴더
│   ├── agents/              # 에이전트 스펙 문서
│   ├── protocols/           # JSON 스키마 정의
│   ├── inputs/              # 입력 파일 (PPTX)
│   ├── outputs/             # 출력 결과물
│   └── logs/screenshots/    # 로그 및 스크린샷
├── 📁 venv/                 # Python 가상환경
├── 📄 .env                  # 환경변수 설정 (Git 무시)
├── 📄 .env.example          # 환경변수 템플릿
├── 📄 requirements.txt      # Python 의존성
└── 📄 README.md             # 프로젝트 문서
```

## 🚀 설치 방법

### 1. 저장소 클론

```bash
git clone <repository-url>
cd auto-tester
```

### 2. Python 가상환경 생성 및 활성화

```powershell
# 가상환경 생성
python -m venv venv

# 가상환경 활성화 (PowerShell)
.\venv\Scripts\Activate.ps1

# 가상환경 활성화 (CMD)
.\venv\Scripts\activate.bat
```

### 3. 의존성 설치

```bash
pip install -r requirements.txt
```

### 4. Playwright 브라우저 설치

```bash
playwright install chromium
```

## ⚙️ 환경 설정

### 환경변수 파일 (.env) 설정

이 프로젝트는 API 키와 같은 민감한 정보를 `.env` 파일에서 관리합니다.

#### 1. 환경변수 파일 생성

```bash
# .env.example을 복사하여 .env 파일 생성
copy .env.example .env
```

#### 2. API 키 설정

`.env` 파일을 열고 실제 API 키를 입력합니다:

```env
# Google Gemini API Key
GOOGLE_API_KEY=AIzaSy...실제_API_키_입력
```

#### 3. Google API 키 발급 방법

1. [Google AI Studio](https://aistudio.google.com/app/apikey) 접속
2. Google 계정으로 로그인
3. **"Create API Key"** 클릭
4. 생성된 API 키를 `.env` 파일에 붙여넣기

### 환경변수 목록

| 변수명 | 설명 | 필수 |
|--------|------|:----:|
| `GOOGLE_API_KEY` | Google Gemini API 키 | ✅ |

> ⚠️ **보안 주의사항**
> - `.env` 파일은 `.gitignore`에 포함되어 Git에 커밋되지 않습니다.
> - API 키를 코드에 직접 하드코딩하지 마세요.
> - `.env` 파일을 다른 사람과 공유하지 마세요.

## 📖 사용 방법

### 1. 프로젝트 폴더 구조 초기화

```bash
python scripts/setup_project.py
```

### 2. PPTX 시나리오 분석

```bash
# inputs/ 폴더에 PPTX 파일을 넣은 후 실행
python scripts/doc_analyst.py
```

생성된 시나리오는 `outputs/scenario_draft.md`에 저장됩니다.

## 🔄 워크플로우

```
┌─────────────────┐
│  PPTX 기획서    │
│  (inputs/)      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  DocAnalyst     │  ← Gemini AI 분석
│  (문서 분석)    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  TestArchitect  │  ← 테스트 케이스 설계
│  (테스트 설계)  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  QAExecutor     │  ← Playwright 실행
│  (테스트 수행)  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  테스트 리포트  │
│  (outputs/)     │
└─────────────────┘
```

## 🛠️ 기술 스택

- **Python 3.10+**
- **Google Gemini AI** - 문서 분석 및 시나리오 생성
- **Playwright** - 웹 브라우저 자동화
- **python-pptx** - PPTX 파일 파싱
- **pytest** - 테스트 프레임워크

## 📄 라이선스

이 프로젝트는 MIT 라이선스를 따릅니다.
