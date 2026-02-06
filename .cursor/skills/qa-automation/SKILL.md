---
name: qa-automation
description: PPTX 기획서를 분석하여 테스트 시나리오를 생성하고 Playwright로 웹 테스트를 자동 수행. "QA 자동화", "테스트 시작", "기획서 분석", "QA 테스트" 언급 시 자동 적용.
---

# QA 자동화

PPTX 기획서 분석부터 웹 테스트 실행, 리포트 생성, GitHub 이슈 등록까지 전체 QA 워크플로우를 자동화합니다.

## 빠른 시작

사용자가 "QA 자동화 시작해줘"라고 하면:

1. **Phase 0**: 사전 검증 (GitHub CLI 설치/로그인 확인)
2. `inputs/` 폴더의 PPTX 파일 확인
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

PPTX에서 테스트 시나리오 추출:

```bash
python .cursor/skills/qa-automation/scripts/extract_pptx.py inputs/파일명.pptx
```

출력: `outputs/scenario_draft.md`

**추출 항목:**
- 슬라이드별 텍스트, 표, 노트
- 기능별 분류 (Critical/High/Medium/Low)
- 테스트 케이스 도출 (정상/에러/경계값)

### Phase 2: 테스트 설계

scenario_draft.md → test_plan.json 변환:

**JSON 구조:**
```json
{
  "test_plan_id": "TP_001",
  "base_url": "${base_url}",
  "test_cases": [
    {
      "tc_id": "TC_001",
      "name": "테스트명",
      "priority": "high",
      "actions": [
        {"action": "navigate", "url": "${base_url}"},
        {"action": "click", "selector": "#btn"},
        {"action": "check", "selector": ".result", "expected": "값"}
      ]
    }
  ]
}
```

**지원 액션:** navigate, click, input, check, wait, screenshot, hover

**선택자 우선순위:** data-testid > id > aria-label > class

### Phase 3: 테스트 실행

**필수 단계:**
1. 사용자에게 URL, 사전 동작 요청
2. `browser_snapshot`으로 실제 DOM 구조 확인
3. 테스트 실행 및 스크린샷 캡처

**스크린샷 저장:**
```
outputs/screenshot_01_initial.png     - 초기 화면
outputs/screenshot_02_interaction.png - 주요 인터랙션
outputs/screenshot_03_correct.png     - 정답/성공 처리
outputs/screenshot_04_wrong.png       - 오답/에러 처리
outputs/screenshot_05_popup.png       - 팝업/다이얼로그
outputs/screenshot_06_result.png      - 결과 화면
```

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

## 상세 결과
| TC ID | Name | Status | Message |

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
- [ ] test_plan.json - JSON 테스트 플랜
- [ ] test_result.json - 실행 결과
- [ ] REPORT.md - 최종 리포트
- [ ] screenshot_*.png - 스크린샷 (최소 6개)
- [ ] issues_created.json - 생성된 GitHub 이슈 목록 (이슈 발견 시)

## 유틸리티 스크립트

**PPTX 추출:**
```bash
python .cursor/skills/qa-automation/scripts/extract_pptx.py <pptx_path>
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
