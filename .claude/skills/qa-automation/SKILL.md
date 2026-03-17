---
name: qa-automation
description: 시나리오 문서(PPTX/DOCX/PDF/이미지)를 분석하여 테스트 시나리오를 생성하고, 이미지 추출·화면 비교·구성 체크와 Playwright 웹 테스트를 자동 수행. "QA 자동화", "테스트 시작", "기획서 분석", "QA 테스트" 언급 시 자동 적용.
user-invocable: true
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
6. 중간 산출물·예상 템플릿·디버그 파일 정리

## Claude Code 에이전트 활용

이 Skill은 Claude Code의 Task 도구를 통해 서브에이전트를 호출합니다:

| 에이전트 | subagent_type | 역할 |
|----------|---------------|------|
| 문서 분석 | `doc-analyst` | PPTX/DOCX/PDF/이미지 분석 및 시나리오 추출 |
| 테스트 설계 | `test-architect` | Markdown 시나리오를 JSON 테스트 플랜으로 변환 |
| 테스트 실행 | `qa-executor` | Playwright 브라우저 자동화 테스트 수행 |
| 총괄 | `qa-master` | 전체 Phase를 순차적으로 실행 |
| 실패 수정 | `auto-fixer` | 실패 테스트 분석, 선택자/기대값 수정, 재실행 |

## 워크플로우

```
Phase 0: 사전 검증 → Phase 1: 문서 분석 → Phase 2: 테스트 설계 → Phase 3: 테스트 실행 → Phase 4: 리포트 생성 → Phase 5: 이슈 등록 → Phase 5.5: 실패 수정 → Phase 6: 정리
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
python .cursor/skills/qa-automation/scripts/extract_document.py inputs/ --output outputs
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

파일명 규칙: `screenshot_TC_{tc_id}_{description}.png`

```
outputs/screenshot_TC_001_initial.png        - 초기 화면
outputs/screenshot_TC_002_interaction.png    - 주요 인터랙션
outputs/screenshot_TC_051_button_state.png   - 버튼 상태 검증
outputs/screenshot_TC_101_navigation.png     - 네비게이션
outputs/screenshot_TC_151_edge_case.png      - 엣지 케이스
outputs/screenshot_TC_181_accessibility.png  - 접근성
```

**화면 비교·구성 체크:**
- 참조 이미지가 있으면: 해당 단계 스크린샷 촬영 후 `python .cursor/skills/qa-automation/scripts/compare_screenshot.py <참조경로> <스크린샷경로> [--threshold 10]` 실행. 일치 여부를 결과/리포트에 반영.
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

### Phase 5.5: 실패 테스트 자동 수정 (auto-fixer)

이슈 등록 후 실패한 테스트의 원인을 분석하고 자동 수정을 시도합니다.

**전제 조건:**
- `outputs/test_result.json`에 `status: "failed"` 항목 존재
- `outputs/issues_created.json`에 등록된 이슈 존재
- 사용자가 자동 수정 실행에 동의

**수행 단계:**
1. 실패 테스트 수집 및 GitHub 이슈 매핑
2. 테스트 URL로 브라우저 접속, `browser_snapshot`으로 실제 DOM 구조 확인
3. 실패 원인 분류:
   - **테스트 수정 가능**: 선택자 불일치(`selector_mismatch`), 텍스트/날짜 형식(`text_mismatch`, `date_format`), 타이밍(`timing_issue`), 스크롤 대상(`scroll_target`)
   - **앱 버그**(`app_bug`): 기능 미구현, 동작 오류 → 수정하지 않음
4. 수정 제안서를 사용자에게 제시 (before/after diff)
5. **사용자 승인 후** 수정 적용 (`run_all_tests.py`, `test_plan.json`)
6. 수정된 테스트만 재실행
7. 결과 업데이트 (`test_result.json`, `REPORT.md`)
8. GitHub 이슈 처리 (수정 완료 시 코멘트/닫기, 사용자 승인)

**출력:**
- `outputs/test_result.json` 업데이트 (수정된 테스트 `"fixed"` 상태)
- `outputs/fix_log.json` 수정 이력 기록
- `outputs/REPORT.md` 갱신 ("자동 수정 결과" 섹션 추가)

**주의:** 모든 수정은 사용자 승인 후에만 적용됩니다. 앱 버그로 판단되는 항목은 수정하지 않습니다.

### Phase 6: 정리 (Cleanup)

테스트 실행 및 GitHub 이슈 등록 완료 후, 중간 산출물·예상 템플릿·디버그 파일을 삭제하여 `outputs/` 폴더를 최종 결과물만 남긴다.

**삭제 대상:**

| 구분 | 파일/패턴 | 이유 |
|------|-----------|------|
| 예상 이슈 템플릿 | `outputs/issue_ISS_*` | 실행 전 예상으로 작성한 파일, 실제 이슈는 `issue_body.md`로 등록됨 |
| 중간 리포트 | `outputs/REPORT_EXECUTED.md` | 최종 `REPORT.md`로 통합됨 |
| 중간 요약 | `outputs/SUMMARY.md`, `outputs/TEST_EXECUTION_SUMMARY.md` | 최종 `REPORT.md`로 통합됨 |
| 중간 결과 | `outputs/test_result_executed.json` | 최종 `test_result.json`으로 통합됨 |
| 디버그 스크린샷 | `outputs/debug_*.png` | 선택자 탐색용 임시 파일 |
| 탐색/디버그 스크립트 | `explore_page.py`, `run_test_tc001.py`, `run_tests.py` | `run_all_tests.py`로 통합됨 |

**보존 대상 (최종 산출물):**

```
outputs/
├── extract_result.json          # Phase 1 문서 추출 결과
├── scenario_draft_source.md     # Phase 1 추출 요약 + 구성 체크 리스트
├── scenario_draft.md            # Phase 2 테스트 시나리오
├── test_plan.json               # Phase 2 테스트 플랜
├── test_result.json             # Phase 3 최종 실행 결과
├── REPORT.md                    # Phase 4 최종 리포트
├── issue_body.md                # Phase 5 GitHub 등록 이슈 본문
├── issues_created.json          # Phase 5 생성된 이슈 URL 목록
├── fix_log.json                 # Phase 5.5 자동 수정 이력 (수정 시)
├── reference/                   # Phase 1 기획서 참조 이미지
│   └── slide_*_img_*.png
└── screenshot_*.png             # Phase 3 테스트 스크린샷 (debug_ 제외)
```

**정리 명령:**
```bash
# outputs/ 내 불필요 파일 삭제
rm -f outputs/issue_ISS_*
rm -f outputs/REPORT_EXECUTED.md
rm -f outputs/SUMMARY.md
rm -f outputs/TEST_EXECUTION_SUMMARY.md
rm -f outputs/test_result_executed.json
rm -f outputs/debug_*.png

# 프로젝트 루트 임시 스크립트 삭제
rm -f explore_page.py run_test_tc001.py run_tests.py
rm -f explore_dom*.py create_github_dir.py
```

**주의:**
- `issue_body.md`는 삭제하지 않는다 (GitHub에 실제 등록된 이슈 원본).
- `run_all_tests.py`는 보존한다 (재실행 가능한 최종 테스트 러너).
- 이전 테스트 결과 폴더(`outputs_/`, `outputs__/` 등)가 있으면 함께 삭제를 제안한다.

## 출력 파일 체크리스트

Phase 6 정리 완료 후 `outputs/` 폴더에 남아야 할 최종 산출물:
- [ ] extract_result.json - 문서 추출 결과
- [ ] scenario_draft_source.md - 추출 요약 + 구성 체크 리스트
- [ ] scenario_draft.md - 테스트 시나리오
- [ ] test_plan.json - JSON 테스트 플랜 (5개 카테고리 포함)
- [ ] test_result.json - 실행 결과 (카테고리별 요약 포함)
- [ ] REPORT.md - 최종 리포트
- [ ] issue_body.md - GitHub 등록 이슈 본문
- [ ] issues_created.json - 생성된 GitHub 이슈 목록 (이슈 발견 시)
- [ ] fix_log.json - 자동 수정 이력 (실패 건 수정 시)
- [ ] reference/ - 기획서 참조 이미지
- [ ] screenshot_TC_*.png - 테스트 스크린샷 (debug_ 제외)
- [ ] run_all_tests.py - 최종 테스트 러너 (생성된 경우)

**삭제 확인 (Phase 6 정리 대상이 남아있지 않은지):**
- [ ] `issue_ISS_*` 파일 없음
- [ ] `REPORT_EXECUTED.md` 없음
- [ ] `SUMMARY.md`, `TEST_EXECUTION_SUMMARY.md` 없음
- [ ] `test_result_executed.json` 없음
- [ ] `debug_*.png` 없음
- [ ] 루트의 `explore_page.py`, `run_test_tc001.py`, `run_tests.py` 없음
- [ ] 루트의 `explore_dom*.py`, `create_github_dir.py` 없음

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
python .cursor/skills/qa-automation/scripts/extract_document.py <path> [--output outputs] [--reference-dir outputs/reference]
```
- path: 파일 경로 또는 inputs/ 등 디렉터리 (지원: .pptx, .docx, .pdf, .png, .jpg, .jpeg)

**PPTX만 추출:**
```bash
python .cursor/skills/qa-automation/scripts/extract_pptx.py <pptx_path> [--reference-dir outputs/reference]
```

**화면 비교 (참조 vs 실제 스크린샷):**
```bash
python .cursor/skills/qa-automation/scripts/compare_screenshot.py <reference_image> <actual_screenshot> [--threshold 10] [--diff-out PATH]
```

**JSON 검증:**
```bash
python .cursor/skills/qa-automation/scripts/validate_json.py outputs/test_plan.json
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
