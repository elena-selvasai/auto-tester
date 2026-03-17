#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Create GitHub issues from outputs/test_result.json failures.
Writes outputs/issues_created.json.
"""

import argparse
import json
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

import yaml

DEFAULT_RESULT = Path("outputs") / "test_result.json"
DEFAULT_STATE = Path("outputs") / "qa_state.yaml"
DEFAULT_OUTPUT = Path("outputs") / "issues_created.json"


def severity_from_priority(priority):
    p = str(priority or "").lower()
    if p == "critical":
        return "Critical"
    if p == "high":
        return "High"
    if p == "medium":
        return "Medium"
    return "Low"


def load_state_config(state_path):
    if not state_path.exists():
        return {}
    with open(state_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return data.get("config", {}) or {}


def create_issue_body(output_dir, tc, base_url, severity):
    tc_id = tc.get("tc_id", "UNKNOWN")
    canonical_issue_body_path = output_dir / "issue_body.md"
    issue_body_path = output_dir / f"issue_body_{tc_id}.md"
    body = [
        "## 이슈 정보",
        "",
        f"- **TC ID**: {tc_id}",
        f"- **심각도**: {severity}",
        f"- **카테고리**: {tc.get('category', '')}",
        f"- **테스트 URL**: {base_url}",
        "",
        "## 문제 설명",
        "",
        tc.get("message", ""),
        "",
        "## 기대 결과",
        "",
        str(tc.get("expected", "")),
        "",
        "## 실제 결과",
        "",
        tc.get("message", ""),
        "",
    ]
    content = "\n".join(body)
    issue_body_path.write_text(content, encoding="utf-8")
    canonical_issue_body_path.write_text(content, encoding="utf-8")
    return issue_body_path


def create_issue_via_gh(repo, title, body_file):
    cmd = ["gh", "issue", "create", "-R", repo, "--title", title, "--body-file", str(body_file), "--label", "bug"]
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        output = (result.stderr or result.stdout or "").strip()
        raise RuntimeError(f"gh issue create 실패: {output}")
    return (result.stdout or "").strip()


def parse_issue_number(issue_url):
    last = issue_url.rstrip("/").split("/")[-1]
    return int(last) if last.isdigit() else None


def create_issues(result_path=DEFAULT_RESULT, state_path=DEFAULT_STATE, repo=None, output_path=DEFAULT_OUTPUT, dry_run=False):
    result_path = Path(result_path)
    output_path = Path(output_path)
    output_dir = output_path.parent
    output_dir.mkdir(parents=True, exist_ok=True)

    if not result_path.exists():
        raise FileNotFoundError(f"test_result.json 파일이 없습니다: {result_path}")

    with open(result_path, "r", encoding="utf-8") as f:
        test_result = json.load(f)

    config = load_state_config(Path(state_path))
    skip_github = bool(config.get("skip_github", False))
    resolved_repo = repo or config.get("github_repo")
    base_url = test_result.get("base_url", config.get("test_url", ""))

    failed_items = [
        tc for tc in test_result.get("results", [])
        if str(tc.get("status", "")).lower() in ("failed", "error")
    ]

    payload = {
        "created_at": datetime.now().strftime("%Y-%m-%d"),
        "repository": resolved_repo,
        "issues": [],
    }

    if skip_github:
        payload["skipped"] = True
        payload["reason"] = "skip_github=true"
        output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return payload

    if not resolved_repo:
        raise ValueError("GitHub 리포지토리가 없습니다. --repo 또는 outputs/qa_state.yaml config.github_repo를 설정하세요.")

    if not dry_run and shutil.which("gh") is None:
        raise RuntimeError("gh CLI가 설치되어 있지 않습니다. 설치 후 다시 시도하거나 --dry-run을 사용하세요.")

    for idx, tc in enumerate(failed_items, 1):
        tc_id = tc.get("tc_id", f"TC_UNKNOWN_{idx}")
        severity = severity_from_priority(tc.get("priority"))
        issue_id = f"ISS_{idx:03d}"
        title = f"[QA] {tc_id}: {tc.get('name', '')} 실패"
        body_file = create_issue_body(output_dir, tc, base_url, severity)

        if dry_run:
            issue_url = f"https://github.com/{resolved_repo}/issues/dry-run-{idx}"
            issue_number = None
            status = "dry_run"
        else:
            issue_url = create_issue_via_gh(resolved_repo, title, body_file)
            issue_number = parse_issue_number(issue_url)
            status = "open"

        payload["issues"].append(
            {
                "issue_id": issue_id,
                "tc_id": tc_id,
                "github_issue_number": issue_number,
                "url": issue_url,
                "title": title,
                "severity": severity,
                "category": tc.get("category", ""),
                "status": status,
            }
        )

    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload


def main():
    parser = argparse.ArgumentParser(description="Create GitHub issues from failed QA tests")
    parser.add_argument("--result", default=str(DEFAULT_RESULT), help="Path to test_result.json")
    parser.add_argument("--state", default=str(DEFAULT_STATE), help="Path to qa_state.yaml")
    parser.add_argument("--repo", default=None, help="GitHub repository owner/repo")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT), help="Path to issues_created.json")
    parser.add_argument("--dry-run", action="store_true", help="Do not call gh CLI, only write expected outputs")
    args = parser.parse_args()

    result = create_issues(
        result_path=args.result,
        state_path=args.state,
        repo=args.repo,
        output_path=args.output,
        dry_run=args.dry_run,
    )
    print(f"[OK] 이슈 목록 생성: {args.output} ({len(result.get('issues', []))}건)")


if __name__ == "__main__":
    main()
