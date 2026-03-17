#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Action-based QA test runner.

Reads outputs/test_plan.json, executes each test case action sequentially,
and writes:
- outputs/test_result.json
- outputs/compare_results.json (when compare_with_reference action is used)
"""

import argparse
import importlib.util
import json
import sys
import time
from datetime import datetime
from pathlib import Path

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

OUTPUT_DIR = Path("outputs")
DEFAULT_TEST_PLAN_PATH = OUTPUT_DIR / "test_plan.json"
DEFAULT_TEST_RESULT_PATH = OUTPUT_DIR / "test_result.json"
DEFAULT_COMPARE_RESULT_PATH = OUTPUT_DIR / "compare_results.json"
SUPPORTED_CATEGORIES = [
    "basic_function",
    "button_state",
    "navigation",
    "edge_case",
    "accessibility",
]


def load_compare_function():
    """Load compare_screenshot function from shared script if available."""
    compare_script = Path(".cursor") / "skills" / "qa-automation" / "scripts" / "compare_screenshot.py"
    if not compare_script.exists():
        return None

    spec = importlib.util.spec_from_file_location("compare_screenshot_mod", str(compare_script))
    if spec is None or spec.loader is None:
        return None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return getattr(mod, "compare_screenshot", None)


def resolve_path(value, default_to_outputs=False):
    """Resolve a path string with optional outputs/ prefix behavior."""
    p = Path(value)
    if p.is_absolute():
        return p
    value_norm = value.replace("/", "\\")
    if value_norm.startswith("outputs\\"):
        return Path(value)
    if default_to_outputs:
        return OUTPUT_DIR / value
    return Path(value)


def resolve_base_url(test_plan, cli_base_url=None):
    """Resolve base URL from CLI arg > test_plan.base_url > test_plan.meta.base_url."""
    if cli_base_url:
        return cli_base_url
    base = test_plan.get("base_url")
    if isinstance(base, str) and base and base != "${base_url}":
        return base
    meta_base = test_plan.get("meta", {}).get("base_url")
    if isinstance(meta_base, str) and meta_base:
        return meta_base
    return ""


def expand_placeholders(value, base_url):
    """Replace known placeholders in action fields."""
    if not isinstance(value, str):
        return value
    return value.replace("${base_url}", base_url or "")


def ensure_outputs_dir():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def execute_action(page, tc_id, action, action_index, base_url, compare_func, compare_records):
    """Execute one action and return a short success message."""
    action_type = action.get("action")
    if not action_type:
        raise ValueError(f"{tc_id}.actions[{action_index}]: action 필드가 없습니다.")

    if action_type == "navigate":
        raw_url = action.get("url")
        if not raw_url:
            raise ValueError(f"{tc_id}.actions[{action_index}]: navigate 액션에 url이 필요합니다.")
        url = expand_placeholders(raw_url, base_url)
        page.goto(url, timeout=30000)
        page.wait_for_load_state("networkidle", timeout=15000)
        return f"navigate: {url}"

    if action_type == "click":
        selector = action.get("selector")
        if not selector:
            raise ValueError(f"{tc_id}.actions[{action_index}]: click 액션에 selector가 필요합니다.")
        wait_before = action.get("wait_before")
        if wait_before:
            wait_selector = wait_before.get("selector")
            wait_state = wait_before.get("state", "hidden")
            wait_timeout = int(wait_before.get("timeout", 5000))
            if wait_selector:
                page.wait_for_selector(wait_selector, state=wait_state, timeout=wait_timeout)
        locator = page.locator(selector).first
        locator.scroll_into_view_if_needed(timeout=5000)
        locator.click(timeout=5000)
        return f"click: {selector}"

    if action_type == "input":
        selector = action.get("selector")
        if not selector:
            raise ValueError(f"{tc_id}.actions[{action_index}]: input 액션에 selector가 필요합니다.")
        value = action.get("value")
        if value is None:
            raise ValueError(f"{tc_id}.actions[{action_index}]: input 액션에 value가 필요합니다.")
        locator = page.locator(selector).first
        locator.scroll_into_view_if_needed(timeout=5000)
        locator.fill(str(value), timeout=5000)
        return f"input: {selector}"

    if action_type == "check":
        selector = action.get("selector")
        expected = action.get("expected")
        expected_count = action.get("count")
        visible = action.get("visible")

        if selector:
            locator = page.locator(selector)
            if visible is not False:
                locator.first.wait_for(state="visible", timeout=5000)
            count = locator.count()
            if expected_count is not None and count != int(expected_count):
                raise AssertionError(
                    f"{tc_id}.actions[{action_index}]: selector count mismatch ({count} != {expected_count})"
                )
            if expected is not None:
                text_sample = locator.first.inner_text(timeout=3000)
                if str(expected) not in text_sample:
                    raise AssertionError(
                        f"{tc_id}.actions[{action_index}]: expected text '{expected}' not found in '{text_sample}'"
                    )
            return f"check: {selector}"

        if expected is None:
            raise ValueError(f"{tc_id}.actions[{action_index}]: check 액션은 selector 또는 expected가 필요합니다.")
        content = page.content()
        if str(expected) not in content:
            raise AssertionError(f"{tc_id}.actions[{action_index}]: expected text '{expected}' not found in page content.")
        return "check: page content"

    if action_type == "check_attribute":
        selector = action.get("selector")
        attribute = action.get("attribute")
        if not selector or not attribute:
            raise ValueError(f"{tc_id}.actions[{action_index}]: check_attribute 액션에 selector/attribute가 필요합니다.")
        locator = page.locator(selector).first
        locator.wait_for(state="visible", timeout=5000)
        actual = locator.get_attribute(attribute)
        expected = action.get("expected")
        if expected is not None and str(actual) != str(expected):
            raise AssertionError(
                f"{tc_id}.actions[{action_index}]: attribute mismatch ({attribute}={actual}, expected={expected})"
            )
        return f"check_attribute: {selector}[{attribute}]={actual}"

    if action_type == "wait":
        timeout = int(action.get("timeout", 1000))
        page.wait_for_timeout(timeout)
        return f"wait: {timeout}ms"

    if action_type == "hover":
        selector = action.get("selector")
        if not selector:
            raise ValueError(f"{tc_id}.actions[{action_index}]: hover 액션에 selector가 필요합니다.")
        locator = page.locator(selector).first
        locator.scroll_into_view_if_needed(timeout=5000)
        locator.hover(timeout=5000)
        return f"hover: {selector}"

    if action_type == "screenshot":
        raw_filename = action.get("filename") or f"screenshot_{tc_id}_{action_index + 1}.png"
        screenshot_path = resolve_path(raw_filename, default_to_outputs=True)
        screenshot_path.parent.mkdir(parents=True, exist_ok=True)
        page.screenshot(path=str(screenshot_path))
        return f"screenshot: {screenshot_path}"

    if action_type == "compare_with_reference":
        if compare_func is None:
            raise RuntimeError("compare_screenshot.py를 로드할 수 없어 compare_with_reference를 실행할 수 없습니다.")
        raw_reference = action.get("reference") or action.get("reference_path")
        if not raw_reference:
            raise ValueError(f"{tc_id}.actions[{action_index}]: compare_with_reference에 reference가 필요합니다.")
        raw_actual = action.get("screenshot") or action.get("actual_path")
        if raw_actual:
            actual_path = resolve_path(raw_actual, default_to_outputs=True)
        else:
            actual_path = OUTPUT_DIR / f"screenshot_{tc_id}_compare_{action_index + 1}.png"
            page.screenshot(path=str(actual_path))
        reference_path = resolve_path(raw_reference)
        threshold = int(action.get("threshold", 10))
        diff_path = OUTPUT_DIR / f"diff_{tc_id}_{action_index + 1}.png"
        result = compare_func(str(reference_path), str(actual_path), threshold=threshold, diff_out_path=str(diff_path))
        if result is None:
            raise RuntimeError(f"{tc_id}.actions[{action_index}]: compare_screenshot 실행 실패")
        compare_records.append(
            {
                "tc_id": tc_id,
                "action_index": action_index,
                "reference": str(reference_path),
                "actual": str(actual_path),
                "result": result,
            }
        )
        if not result.get("match", False):
            raise AssertionError(
                f"{tc_id}.actions[{action_index}]: reference mismatch (score={result.get('score')}, threshold={threshold})"
            )
        return f"compare_with_reference: {reference_path} vs {actual_path}"

    raise ValueError(f"{tc_id}.actions[{action_index}]: 지원하지 않는 action '{action_type}'")


def execute_test_case(page, tc, base_url, compare_func, compare_records):
    """Execute one test case and return status/message/elapsed."""
    tc_id = tc.get("tc_id", "UNKNOWN")
    actions = tc.get("actions", [])
    if not isinstance(actions, list) or len(actions) == 0:
        return "skipped", "actions가 비어 있어 실행을 건너뜀", 0

    start_time = time.time()
    try:
        action_messages = []
        for idx, action in enumerate(actions):
            action_messages.append(execute_action(page, tc_id, action, idx, base_url, compare_func, compare_records))
        elapsed_ms = int((time.time() - start_time) * 1000)
        return "passed", "; ".join(action_messages[-3:]), elapsed_ms
    except (PlaywrightTimeoutError, PlaywrightError, AssertionError, ValueError, RuntimeError, TypeError, AttributeError) as exc:
        error_shot = OUTPUT_DIR / f"screenshot_{tc_id}_error.png"
        try:
            page.screenshot(path=str(error_shot))
        except PlaywrightError:
            pass
        elapsed_ms = int((time.time() - start_time) * 1000)
        return "failed", str(exc), elapsed_ms


def run_all_tests(test_plan_path=DEFAULT_TEST_PLAN_PATH, base_url=None, headless=True):
    """Run all test cases in test_plan.json."""
    ensure_outputs_dir()
    test_plan_path = Path(test_plan_path)
    if not test_plan_path.exists():
        raise FileNotFoundError(f"test_plan.json 파일이 없습니다: {test_plan_path}")

    with open(test_plan_path, "r", encoding="utf-8") as f:
        test_plan = json.load(f)

    test_cases = test_plan.get("test_cases")
    if not isinstance(test_cases, list):
        raise ValueError("test_plan.json의 test_cases는 배열이어야 합니다.")

    resolved_base_url = resolve_base_url(test_plan, cli_base_url=base_url)
    compare_func = load_compare_function()
    compare_records = []

    summary = {"total": len(test_cases), "passed": 0, "failed": 0, "skipped": 0, "errors": 0}
    category_summary = {
        cat: {"total": 0, "passed": 0, "failed": 0, "skipped": 0, "errors": 0} for cat in SUPPORTED_CATEGORIES
    }
    results = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context(viewport={"width": 1280, "height": 800})
        page = context.new_page()

        for tc in test_cases:
            tc_id = tc.get("tc_id", "")
            name = tc.get("name", "")
            category = tc.get("category", "basic_function")
            priority = tc.get("priority", "medium")
            expected = tc.get("expected", "")

            if category not in category_summary:
                category_summary[category] = {"total": 0, "passed": 0, "failed": 0, "skipped": 0, "errors": 0}
            category_summary[category]["total"] += 1

            status, message, elapsed_ms = execute_test_case(page, tc, resolved_base_url, compare_func, compare_records)
            summary[status] += 1
            category_summary[category][status] += 1

            print(f"[{tc_id}] {name} -> {status.upper()}: {message}")
            results.append(
                {
                    "tc_id": tc_id,
                    "category": category,
                    "name": name,
                    "status": status,
                    "message": message,
                    "expected": expected,
                    "priority": priority,
                    "elapsed_ms": elapsed_ms,
                }
            )

        browser.close()

    test_result = {
        "test_plan_id": test_plan.get("test_plan_id", ""),
        "executed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "base_url": resolved_base_url,
        "summary": summary,
        "category_summary": category_summary,
        "results": results,
    }

    with open(DEFAULT_TEST_RESULT_PATH, "w", encoding="utf-8") as f:
        json.dump(test_result, f, ensure_ascii=False, indent=2)

    with open(DEFAULT_COMPARE_RESULT_PATH, "w", encoding="utf-8") as f:
        json.dump({"generated_at": datetime.now().isoformat(), "items": compare_records}, f, ensure_ascii=False, indent=2)

    print("\n=== 테스트 완료 ===")
    print(f"결과 저장: {DEFAULT_TEST_RESULT_PATH}")
    print(f"비교 결과 저장: {DEFAULT_COMPARE_RESULT_PATH}")
    print(
        f"총: {summary['total']}, 통과: {summary['passed']}, 실패: {summary['failed']}, "
        f"스킵: {summary['skipped']}, 오류: {summary['errors']}"
    )
    return test_result


def main():
    parser = argparse.ArgumentParser(description="Action-based QA test runner")
    parser.add_argument("--test-plan", default=str(DEFAULT_TEST_PLAN_PATH), help="Path to test_plan.json")
    parser.add_argument("--base-url", default=None, help="Base URL override")
    parser.add_argument("--headed", action="store_true", help="Run browser in headed mode")
    args = parser.parse_args()
    run_all_tests(test_plan_path=args.test_plan, base_url=args.base_url, headless=not args.headed)


if __name__ == "__main__":
    main()
