---
name: qa-automation
description: 시나리오 문서(PPTX/DOCX/PDF/이미지)를 분석하여 테스트 시나리오를 생성하고, 이미지 추출·화면 비교·구성 체크와 Playwright 웹 테스트를 자동 수행. "QA 자동화", "테스트 시작", "기획서 분석", "QA 테스트" 언급 시 자동 적용.
user-invocable: true
allowed-tools: Read, Shell, Write, Grep, Glob, StrReplace
disable-model-invocation: false
---

# QA 자동화

시나리오 문서(PPTX, DOCX, PDF, 이미지) 분석부터 참조 이미지 추출, 웹 테스트 실행, 화면 비교·구성 체크, 리포트 생성, GitHub 이슈 등록까지 전체 QA 워크플로우를 자동화합니다.

## 빠른 시작

사용자가 "QA 자동화 시작해줘"라고 하면:

1. **Phase 0**: 사전 검증 (GitHub CLI 설치/로그인 확인)
2. `inputs/` 폴더의 시나리오 문서 확인 (PPTX, DOCX, PDF, 이미지)
3. 사용자에게 요청:
   - 테스트 URL
   - 이슈 등록할 GitHub 리포지토리 (`owner/repo` 형식)
4. 전체 워크플로우 실행
5. 이슈 발견 시 지정된 리포지토리에 GitHub Issues 자동 생성

## 워크플로우

```
Phase 0: 사전 검증 → Phase 1: 문서 분석 → Phase 2: 테스트 설계 → Phase 3: 테스트 실행 → Phase 4: 리포트 생성 → Phase 5: 이슈 등록
```

### Phase 0: 사전 검증

**1. GitHub CLI 확인:**
```bash
gh --version        # GitHub CLI 설치 확인
gh auth status      # 로그인 상태 확인
```

**2. 사용자 입력 요청:**
- 테스트 URL (필수)
- 이슈 등록할 GitHub 리포지토리 (필수): `owner/repo` 형식
  - 예: `elena-selvasai/auto-tester`
  - 예: `company/project-name`

**필수 조건:**
- GitHub CLI (`gh`) 설치됨
- GitHub 계정 로그인됨 (`gh auth login`)
- 이슈 등록할 리포지토리에 대한 접근 권한

**사전 검증 실패 시:**
- GitHub CLI 미설치 → 설치 안내 제공
- 로그인 안됨 → `gh auth login` 실행 안내
- 리포지토리 미입력 → 이슈 등록 Phase 건너뛰기

### Phase 1: 문서 분석

**지원 포맷:** PPTX, DOCX, PDF, 이미지(PNG/JPG 등). 단일 진입 스크립트로 자동 감지:

```bash
python ../../.cursor/skills/qa-automation/scripts/extract_document.py inputs/ --output outputs
```

- 경로에 디렉터리를 주면 지원 확장자 첫 파일 사용. 단일 파일도 가능: `extract_document.py inputs/기획서.pptx --output outputs`

**출력:**
- `outputs/extract_result.json` - 공통 스키마 (pages[], reference_images[])
- `outputs/scenario_draft_source.md` - 추출 요약 + **구성 체크 리스트**(페이지별 예상 표시 요소)
- `outputs/reference/` - 기획서에서 추출·렌더한 참조 이미지 (슬라이드/페이지별)

**추출 항목:**
- 페이지/슬라이드별 텍스트, 표, 노트, 삽입 이미지
- 참조 이미지 저장 → 테스트 단계에서 화면 비교(compare_screenshot)에 사용
- 구성 체크 리스트 → 테스트 step에서 필수 문구/요소 존재 여부 check에 활용

### Phase 2: 테스트 설계

scenario_draft.md → test_plan.json 변환:

**테스트 케이스 카테고리 (필수 포함):**

| 카테고리 | 설명 | 필수 여부 |
|----------|------|-----------|
| `basic_function` | 기획서 기반 기본 기능 테스트 | 필수 |
| `button_state` | 버튼 활성화/비활성화 상태 검증 | 필수 |
| `navigation` | 화면 이동 및 상태 복원 테스트 | 필수 |
| `edge_case` | 경계값, 오류 처리 테스트 | 권장 |
| `accessibility` | 접근성 요소 확인 | 권장 |

**카테고리별 필수 테스트 항목:**

#### 1. basic_function (기본 기능)
- 초기 화면 로딩 및 UI 요소 표시
- 핵심 기능 동작 (정답/오답, 제출, 조회 등)
- 팝업/다이얼로그 동작
- 전체 플로우 완료 및 결과 화면

#### 2. button_state (버튼 상태)
- 초기 상태 버튼 활성화/비활성화 확인
- 조건에 따른 버튼 상태 변경 (예: 선택 후 다음 버튼 활성화)
- 스크롤/페이지네이션 버튼 상태 (첫 페이지/마지막 페이지)
- 완료 후 선택지/입력 필드 비활성화

#### 3. navigation (네비게이션)
- 이전/다음 이동 버튼 동작
- 완료된 항목 재방문 시 상태 유지
- 팝업 닫은 후 원래 상태 복원
- 브레드크럼/탭 네비게이션 (있는 경우)

#### 4. edge_case (엣지 케이스)
- 토글 버튼 반복 클릭 시 상태 정상 유지
- 오답/에러 후 재시도 가능 여부
- 빈 입력/최대 길이 입력 처리
- 빠른 연속 클릭 처리

#### 5. accessibility (접근성)
- 이미지 alt 텍스트 존재
- 버튼 레이블 명확성
- 키보드 네비게이션 (선택적)
- 색상 대비 (선택적)

**JSON 구조:**
```json
{
  "test_plan_id": "TP_001",
  "base_url": "${base_url}",
  "test_cases": [
    {
      "tc_id": "TC_001",
      "name": "테스트명",
      "category": "basic_function",
      "priority": "critical",
      "actions": [
        {"action": "navigate", "url": "${base_url}"},
        {"action": "click", "selector": "#btn"},
        {"action": "check", "selector": ".result", "expected": "값"}
      ]
    },
    {
      "tc_id": "TC_051",
      "name": "초기 상태 버튼 검증",
      "category": "button_state",
      "priority": "high",
      "actions": [
        {"action": "check", "expected": "이전 버튼 비활성화, 다음 버튼 활성화"}
      ]
    }
  ]
}
```

**테스트 케이스 번호 규칙 (최소 20개 ~ 최대 200개):**
- TC_001~050: 기본 기능 (basic_function) - 최소 8개
- TC_051~100: 버튼 상태 (button_state) - 최소 4개
- TC_101~150: 네비게이션 (navigation) - 최소 3개
- TC_151~180: 엣지 케이스 (edge_case) - 최소 3개
- TC_181~200: 접근성 (accessibility) - 최소 2개

**지원 액션:** navigate, click, input, check, wait, screenshot, hover, check_attribute, compare_with_reference

**compare_with_reference:** 참조 이미지(기획서)와 현재 스크린샷 유사도 비교. 액션 예: `{"action": "compare_with_reference", "reference": "outputs/reference/slide_6.png", "screenshot": "outputs/screenshot_01_initial.png"}` → `compare_screenshot.py` 호출로 일치 여부 판정.

**선택자 우선순위:** data-testid > id > aria-label > class

### Phase 3: 테스트 실행

**필수 단계:**
1. 사용자에게 URL, 사전 동작 요청
2. `browser_snapshot`으로 실제 DOM 구조 확인
3. 테스트 실행 및 스크린샷 캡처

**스크린샷 저장:**
```
# 기본 기능 테스트
outputs/screenshot_01_initial.png     - 초기 화면
outputs/screenshot_02_interaction.png - 주요 인터랙션
outputs/screenshot_03_correct.png     - 정답/성공 처리
outputs/screenshot_04_wrong.png       - 오답/에러 처리
outputs/screenshot_05_popup.png       - 팝업/다이얼로그
outputs/screenshot_06_result.png      - 결과 화면

# 추가 테스트 (버튼 상태, 네비게이션, 엣지 케이스)
outputs/screenshot_tc051_*.png        - 버튼 상태 검증
outputs/screenshot_tc052_*.png        - 스크롤/페이지네이션 상태
outputs/screenshot_tc053_*.png        - 완료 후 비활성화 상태
outputs/screenshot_tc101_*.png        - 항목 재방문
outputs/screenshot_tc151_*.png        - 토글 동작
outputs/screenshot_tc152_*.png        - 오류 후 재시도
```

**화면 비교·구성 체크:**
- 참조 이미지가 있으면: 해당 단계 스크린샷 촬영 후 `python ../../.cursor/skills/qa-automation/scripts/compare_screenshot.py <참조경로> <스크린샷경로> [--threshold 10]` 실행. 일치 여부를 결과/리포트에 반영.
- 구성 체크: `outputs/scenario_draft_source.md`의 "구성 체크 리스트"에 있는 페이지별 예상 요소를 DOM/스크린샷에서 확인 (check 액션 또는 텍스트 존재 여부).

**오답 테스트:** 정오답 채점 시 오답 TC는 정답으로 대체하지 말고, 새로고침 또는 해당 화면 이동 후 실제 오답 선택 → '오답입니다' 표시·피드백 검증 필수.

**에러 핸들링:**
- 요소 못 찾음 → 대체 선택자 시도
- 타임아웃 → 대기 시간 2배 후 재시도 (최대 2회)

### Phase 4: 리포트 생성

`outputs/REPORT.md` 생성:

```markdown
# QA 테스트 리포트

**URL**: [테스트 URL]
**Date**: YYYY-MM-DD

## Summary
| Total | Passed | Failed |
|-------|--------|--------|
| N     | N      | N      |

## 카테고리별 결과
| 카테고리 | 테스트 수 | 통과 | 실패 |
|----------|-----------|------|------|
| 기본 기능 (TC_001~050) | N | N | N |
| 버튼 상태 (TC_051~100) | N | N | N |
| 네비게이션 (TC_101~150) | N | N | N |
| 엣지 케이스 (TC_151~180) | N | N | N |
| 접근성 (TC_181~200) | N | N | N |

## 상세 결과
| TC ID | Category | Name | Status | Message |

## 스크린샷
| 파일명 | 설명 |

## 발견 사항
- 기획서 vs 실제 구현 차이점
```

### Phase 5: GitHub 이슈 자동 등록

테스트 실패 또는 기획서와 불일치 발견 시, **사용자가 지정한 리포지토리**에 GitHub Issues 자동 생성:

**이슈 생성 명령:**
```bash
gh issue create -R {owner/repo} --title "[QA] {이슈ID}: {제목}" --body-file "outputs/issue_body.md" --label "bug"
```

- `-R owner/repo`: Phase 0에서 사용자에게 입력받은 리포지토리
- 예: `gh issue create -R elena-selvasai/auto-tester --title "..." --body-file "..."`

**이슈 본문 템플릿 (`outputs/issue_body.md`):**
```markdown
## 이슈 정보
| 항목 | 내용 |
|------|------|
| **이슈 ID** | ISS_XXX |
| **심각도** | Critical/High/Medium/Low |
| **테스트 URL** | {url} |

## 문제 설명
{description}

## 재현 단계
1. {step1}
2. {step2}

## 기대 결과
{expected}

## 실제 결과
{actual}
```

**이슈 생성 후:**
- `outputs/issues_created.json`에 생성된 이슈 목록 저장
- 이슈 URL 사용자에게 제공

## 출력 파일 체크리스트

테스트 완료 후 `outputs/` 폴더:
- [ ] scenario_draft.md - 테스트 시나리오
- [ ] test_plan.json - JSON 테스트 플랜 (5개 카테고리 포함)
- [ ] test_result.json - 실행 결과 (카테고리별 요약 포함)
- [ ] REPORT.md - 최종 리포트
- [ ] screenshot_01~06_*.png - 기본 기능 스크린샷 (최소 6개)
- [ ] screenshot_tc009~*.png - 추가 테스트 스크린샷
- [ ] issues_created.json - 생성된 GitHub 이슈 목록 (이슈 발견 시)

**테스트 케이스 기준:**

| 카테고리 | 최소 | 권장 | 최대 |
|----------|------|------|------|
| 기본 기능 (TC_001~050) | 8개 | 15~30개 | 50개 |
| 버튼 상태 (TC_051~100) | 4개 | 8~15개 | 50개 |
| 네비게이션 (TC_101~150) | 3개 | 5~10개 | 50개 |
| 엣지 케이스 (TC_151~180) | 3개 | 5~10개 | 30개 |
| 접근성 (TC_181~200) | 2개 | 3~5개 | 20개 |
| **총합** | **20개** | **36~70개** | **200개** |

**테스트 케이스 수 결정 기준:**
- 화면/페이지 수 × 3~5개
- 버튼/인터랙션 요소 수 × 2~3개
- 입력 필드 수 × 3개 (정상/경계/오류)
- 주요 플로우 당 5~10개

## 유틸리티 스크립트

**문서 추출 (통합, 다중 포맷):**
```bash
python ../../.cursor/skills/qa-automation/scripts/extract_document.py <path> [--output outputs] [--reference-dir outputs/reference]
```
- path: 파일 경로 또는 inputs/ 등 디렉터리 (지원: .pptx, .docx, .pdf, .png, .jpg, .jpeg)

**PPTX만 추출:**
```bash
python ../../.cursor/skills/qa-automation/scripts/extract_pptx.py <pptx_path> [--reference-dir outputs/reference]
```

**화면 비교 (참조 vs 실제 스크린샷):**
```bash
python ../../.cursor/skills/qa-automation/scripts/compare_screenshot.py <reference_image> <actual_screenshot> [--threshold 10] [--diff-out PATH]
```

**JSON 검증:**
```bash
python ../../.cursor/skills/qa-automation/scripts/validate_json.py outputs/test_plan.json
```

## 에러 대응

| 상황 | 대응 |
|------|------|
| PPTX 없음 | inputs/ 폴더 확인 요청 |
| URL 접속 불가 | URL 유효성 확인 |
| 요소 찾기 실패 | DOM 재분석 후 선택자 수정 |
| 테스트 실패 | 스크린샷 캡처 후 원인 기록 |
| GitHub CLI 미설치 | `winget install GitHub.cli` 또는 https://cli.github.com 안내 |
| GitHub 미로그인 | `gh auth login` 실행 안내 |
| 리포지토리 미입력 | 이슈 등록 Phase 건너뛰기, 수동 등록 안내 |
| 리포지토리 접근 권한 없음 | 권한 확인 요청 또는 다른 리포지토리 입력 요청 |
