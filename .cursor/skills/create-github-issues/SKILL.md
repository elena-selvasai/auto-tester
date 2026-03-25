---
name: create-github-issues
description: Use when creating GitHub issues from failed QA test results. Triggers on issue creation, Phase 5 issue registration, failed TC reporting to GitHub, or bug tracking from test failures.
---

# GitHub 이슈 생성

`test_result.json`의 실패 TC를 GitHub 이슈로 등록합니다.

## 실행

```bash
# 실제 이슈 생성
python scripts/create_github_issues.py --repo "owner/repo"

# dry-run (gh CLI 호출 없이 결과만 확인)
python scripts/create_github_issues.py --repo "owner/repo" --dry-run
```

## 옵션

| 옵션 | 기본값 | 설명 |
|------|--------|------|
| `--result` | outputs/test_result.json | 테스트 결과 |
| `--state` | outputs/qa_state.yaml | QA 상태 (repo, URL 설정) |
| `--repo` | qa_state.yaml의 github_repo | GitHub 리포지토리 |
| `--output` | outputs/issues_created.json | 생성 결과 |
| `--dry-run` | off | gh CLI 호출 없이 시뮬레이션 |

## 사전 조건

- `gh` CLI 설치 및 인증 (`gh auth status`)
- `qa_state.yaml`에 `github_repo` 설정 또는 `--repo` 인자
- `skip_github=true` 설정 시 이슈 생성 건너뜀

## 이슈 형식

| 항목 | 값 |
|------|-----|
| 제목 | `[QA] TC_XXX: 테스트명 실패` |
| 라벨 | `bug` |
| 심각도 | priority → Critical/High/Medium/Low 매핑 |
| 본문 | TC ID, 심각도, 카테고리, 기대/실제 결과 |

## 산출물

```json
{
  "created_at": "2026-03-25",
  "repository": "owner/repo",
  "issues": [
    {
      "issue_id": "ISS_001",
      "tc_id": "TC_003",
      "github_issue_number": 42,
      "url": "https://github.com/owner/repo/issues/42",
      "title": "[QA] TC_003: 버튼 클릭 실패",
      "severity": "High",
      "status": "open"
    }
  ]
}
```

## 트러블슈팅

| 증상 | 해결 |
|------|------|
| `gh` 미설치 | `--dry-run`으로 시뮬레이션 또는 gh 설치 |
| 인증 실패 | `gh auth login` 실행 |
| repo 없음 | `--repo` 지정 또는 `qa_cli.py set github_repo "owner/repo"` |
