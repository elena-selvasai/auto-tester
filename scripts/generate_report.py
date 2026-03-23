#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Generate outputs/REPORT.md from outputs/test_result.json.
"""

import argparse
import json
from datetime import datetime
from pathlib import Path

DEFAULT_RESULT = Path("outputs") / "test_result.json"
DEFAULT_REPORT = Path("outputs") / "REPORT.md"


def _pct(part, total):
    if total == 0:
        return "0%"
    return f"{(part / total) * 100:.1f}%"


def generate_report(result_path=DEFAULT_RESULT, report_path=DEFAULT_REPORT):
    result_path = Path(result_path)
    report_path = Path(report_path)
    if not result_path.exists():
        raise FileNotFoundError(f"test_result.json 파일이 없습니다: {result_path}")

    with open(result_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    summary = data.get("summary", {})
    category_summary = data.get("category_summary", {})
    results = data.get("results", [])

    total = int(summary.get("total", len(results)))
    passed = int(summary.get("passed", 0))
    failed = int(summary.get("failed", 0))
    skipped = int(summary.get("skipped", 0))
    errors = int(summary.get("errors", 0))

    lines = []
    lines.append("# QA 테스트 리포트")
    lines.append("")
    lines.append(f"**URL**: {data.get('base_url', '')}")
    lines.append(f"**Date**: {datetime.now().strftime('%Y-%m-%d')}")
    lines.append(f"**테스트 플랜 ID**: {data.get('test_plan_id', '')}")
    lines.append(f"**실행 일시**: {data.get('executed_at', '')}")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append("| Total | Passed | Failed | Skipped | Errors | Pass Rate |")
    lines.append("|-------|--------|--------|---------|--------|-----------|")
    lines.append(f"| {total} | {passed} | {failed} | {skipped} | {errors} | {_pct(passed, total)} |")
    lines.append("")
    lines.append("## 카테고리별 결과")
    lines.append("")
    lines.append("| 카테고리 | 테스트 수 | 통과 | 실패 | 스킵 | 오류 | 통과율 |")
    lines.append("|----------|-----------|------|------|------|------|--------|")

    for category, cat in category_summary.items():
        cat_total = int(cat.get("total", 0))
        cat_passed = int(cat.get("passed", 0))
        cat_failed = int(cat.get("failed", 0))
        cat_skipped = int(cat.get("skipped", 0))
        cat_errors = int(cat.get("errors", 0))
        lines.append(
            f"| {category} | {cat_total} | {cat_passed} | {cat_failed} | {cat_skipped} | {cat_errors} | {_pct(cat_passed, cat_total)} |"
        )

    lines.append("")
    lines.append("## 상세 결과")
    lines.append("")
    lines.append("| TC ID | Category | Name | Status | Message |")
    lines.append("|-------|----------|------|--------|---------|")
    for item in results:
        message = str(item.get("message", "")).replace("\n", " ").replace("|", "\\|")
        lines.append(
            f"| {item.get('tc_id', '')} | {item.get('category', '')} | {item.get('name', '')} | {str(item.get('status', '')).upper()} | {message} |"
        )

    lines.append("")
    lines.append("## 발견 사항")
    lines.append("")
    lines.append("- 실패/스킵 항목은 `outputs/test_result.json`의 상세 메시지와 스크린샷을 함께 검토하세요.")

    failed_with_shots = [
        item for item in results
        if item.get("status") == "failed" and item.get("screenshots")
    ]
    if failed_with_shots:
        lines.append("")
        lines.append("## 실패 케이스 스크린샷")
        lines.append("")
        for item in failed_with_shots:
            lines.append(f"### {item.get('tc_id', '')} — {item.get('name', '')}")
            for shot in item["screenshots"]:
                lines.append(f"- `{shot}`")

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report_path


def main():
    parser = argparse.ArgumentParser(description="Generate REPORT.md from test_result.json")
    parser.add_argument("--result", default=str(DEFAULT_RESULT), help="Path to test_result.json")
    parser.add_argument("--output", default=str(DEFAULT_REPORT), help="Path to REPORT.md")
    args = parser.parse_args()
    output = generate_report(result_path=args.result, report_path=args.output)
    print(f"[OK] 리포트 생성: {output}")


if __name__ == "__main__":
    main()
