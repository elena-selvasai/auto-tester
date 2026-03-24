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

# HTML 불리언 속성: 존재 여부로 상태를 나타냄 (값이 아닌 존재/부재로 true/false 판단)
BOOLEAN_ATTRIBUTES = {
    "disabled", "checked", "readonly", "selected", "required",
    "multiple", "autofocus", "hidden", "autoplay", "controls",
    "loop", "muted", "open", "reversed", "default",
}

MAX_RETRIES = 2
RETRY_TIMEOUT_MULTIPLIER = 2


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


def normalize_precondition(precondition, source_label):
    """Validate and normalize one precondition block."""
    if precondition is None:
        return None
    if not isinstance(precondition, dict):
        raise ValueError(f"{source_label}: precondition은 객체여야 합니다.")

    actions = precondition.get("actions")
    success_checks = precondition.get("success_checks")
    if not isinstance(actions, list) or len(actions) == 0:
        raise ValueError(f"{source_label}: precondition.actions는 비어 있지 않은 배열이어야 합니다.")
    if not isinstance(success_checks, list) or len(success_checks) == 0:
        raise ValueError(f"{source_label}: precondition.success_checks는 비어 있지 않은 배열이어야 합니다.")

    return {
        "description": precondition.get("description", ""),
        "actions": actions,
        "success_checks": success_checks,
    }


def merge_preconditions(global_precondition, test_precondition):
    """Merge root-level and test-level preconditions."""
    normalized_blocks = []
    if global_precondition is not None:
        normalized_blocks.append(normalize_precondition(global_precondition, "root.precondition"))
    if test_precondition is not None:
        normalized_blocks.append(normalize_precondition(test_precondition, "tc.precondition"))

    if not normalized_blocks:
        return None

    merged = {
        "description": " / ".join(block["description"] for block in normalized_blocks if block.get("description")),
        "actions": [],
        "success_checks": [],
    }
    for block in normalized_blocks:
        merged["actions"].extend(block["actions"])
        merged["success_checks"].extend(block["success_checks"])
    return merged


def execute_action_sequence(page, tc_id, actions, base_url, compare_func, compare_records):
    """Execute a list of actions and collect success messages/screenshots."""
    action_messages = []
    screenshots = []
    for idx, action in enumerate(actions):
        msg = execute_action(page, tc_id, action, idx, base_url, compare_func, compare_records)
        action_messages.append(msg)
        if msg.startswith("screenshot:"):
            screenshots.append(msg[len("screenshot:"):].strip())
    return action_messages, screenshots


def run_precondition(page, tc_id, precondition, base_url, compare_func, compare_records):
    """Run precondition actions and verify success before the main test."""
    if precondition is None:
        return [], []

    precondition_messages = []
    screenshots = []

    action_messages, action_screenshots = execute_action_sequence(
        page,
        f"{tc_id}.precondition",
        precondition["actions"],
        base_url,
        compare_func,
        compare_records,
    )
    precondition_messages.extend(action_messages)
    screenshots.extend(action_screenshots)

    check_messages, check_screenshots = execute_action_sequence(
        page,
        f"{tc_id}.precondition_check",
        precondition["success_checks"],
        base_url,
        compare_func,
        compare_records,
    )
    precondition_messages.extend(check_messages)
    screenshots.extend(check_screenshots)
    return precondition_messages, screenshots


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
        wait_until = action.get("wait_until", "networkidle")
        page.goto(url, timeout=30000)
        try:
            page.wait_for_load_state(wait_until, timeout=15000)
        except PlaywrightTimeoutError:
            pass  # SPA 등에서 networkidle 타임아웃은 무시
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
            elif visible is False:
                if locator.first.is_visible():
                    raise AssertionError(
                        f"{tc_id}.actions[{action_index}]: 요소가 숨김 상태여야 하지만 보임: {selector}"
                    )
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
        if expected is not None:
            if attribute.lower() in BOOLEAN_ATTRIBUTES and str(expected).lower() in ("true", "false"):
                # 불리언 속성: 속성 존재 여부로 true/false 판단 (값이 아닌 존재/부재)
                actual_bool = "true" if actual is not None else "false"
                if actual_bool != str(expected).lower():
                    raise AssertionError(
                        f"{tc_id}.actions[{action_index}]: boolean attribute mismatch "
                        f"({attribute} present={actual is not None}, expected={expected})"
                    )
            elif str(actual) != str(expected):
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


def _capture_error_screenshot(page, tc_id, execution_stage, screenshots):
    """Capture error screenshot and append to screenshots list."""
    suffix = "precondition_error" if execution_stage == "precondition" else "error"
    error_shot = OUTPUT_DIR / f"screenshot_{tc_id}_{suffix}.png"
    try:
        page.screenshot(path=str(error_shot))
        screenshots.append(str(error_shot))
    except PlaywrightError:
        pass


def execute_test_case(page, tc, base_url, compare_func, compare_records, global_precondition=None):
    """Execute one test case with retry on timeout errors."""
    tc_id = tc.get("tc_id", "UNKNOWN")
    actions = tc.get("actions", [])
    if not isinstance(actions, list) or len(actions) == 0:
        return "skipped", "actions가 비어 있어 실행을 건너뜀", 0, []

    last_status, last_message, last_elapsed, last_screenshots = "failed", "", 0, []

    for attempt in range(1 + MAX_RETRIES):
        start_time = time.time()
        screenshots = []
        execution_stage = "actions"
        try:
            action_messages = []

            precondition = merge_preconditions(global_precondition, tc.get("precondition"))
            if precondition is not None:
                execution_stage = "precondition"
                precondition_messages, precondition_screenshots = run_precondition(
                    page, tc_id, precondition, base_url, compare_func, compare_records,
                )
                screenshots.extend(precondition_screenshots)
                if precondition_messages:
                    action_messages.append("precondition: ok")

            execution_stage = "actions"
            sequence_messages, sequence_screenshots = execute_action_sequence(
                page, tc_id, actions, base_url, compare_func, compare_records,
            )
            action_messages.extend(sequence_messages)
            screenshots.extend(sequence_screenshots)
            elapsed_ms = int((time.time() - start_time) * 1000)
            return "passed", "; ".join(action_messages), elapsed_ms, screenshots

        except PlaywrightTimeoutError as exc:
            elapsed_ms = int((time.time() - start_time) * 1000)
            last_screenshots = screenshots
            _capture_error_screenshot(page, tc_id, execution_stage, last_screenshots)
            last_elapsed = elapsed_ms
            if execution_stage == "precondition":
                last_message = f"precondition failed: {exc}"
            else:
                last_message = str(exc)
            if attempt < MAX_RETRIES:
                wait_ms = 1000 * RETRY_TIMEOUT_MULTIPLIER ** (attempt + 1)
                print(f"  [{tc_id}] 타임아웃 재시도 {attempt + 1}/{MAX_RETRIES} (대기 {wait_ms}ms)")
                page.wait_for_timeout(wait_ms)
                continue
            last_status = "failed"
            return last_status, last_message, last_elapsed, last_screenshots

        except (PlaywrightError, AssertionError, ValueError, RuntimeError, TypeError, AttributeError) as exc:
            elapsed_ms = int((time.time() - start_time) * 1000)
            _capture_error_screenshot(page, tc_id, execution_stage, screenshots)
            msg = f"precondition failed: {exc}" if execution_stage == "precondition" else str(exc)
            return "failed", msg, elapsed_ms, screenshots

    return last_status, last_message, last_elapsed, last_screenshots


def run_all_tests(test_plan_path=DEFAULT_TEST_PLAN_PATH, base_url=None, headless=True, cli_precondition=None, tc_filter=None):
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
    # CLI로 전달된 precondition이 있으면 test_plan의 precondition보다 우선
    global_precondition = cli_precondition if cli_precondition is not None else test_plan.get("precondition")
    compare_func = load_compare_function()
    compare_records = []

    summary = {"total": 0, "passed": 0, "failed": 0, "skipped": 0, "errors": 0}
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

            # TC 필터링: --tc 옵션이 있으면 해당 TC만 실행
            if tc_filter and tc_id not in tc_filter:
                continue

            summary["total"] += 1
            name = tc.get("name", "")
            category = tc.get("category", "basic_function")
            priority = tc.get("priority", "medium")
            expected = tc.get("expected", "")

            if category not in category_summary:
                category_summary[category] = {"total": 0, "passed": 0, "failed": 0, "skipped": 0, "errors": 0}
            category_summary[category]["total"] += 1

            status, message, elapsed_ms, screenshots = execute_test_case(
                page,
                tc,
                resolved_base_url,
                compare_func,
                compare_records,
                global_precondition=global_precondition,
            )
            summary[status] += 1
            category_summary[category][status] += 1

            print(f"[{tc_id}] {name} -> {status.upper()}: {message}")
            result_entry = {
                "tc_id": tc_id,
                "category": category,
                "name": name,
                "status": status,
                "message": message,
                "expected": expected,
                "priority": priority,
                "elapsed_ms": elapsed_ms,
            }
            if screenshots:
                result_entry["screenshots"] = screenshots
            results.append(result_entry)

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
    parser.add_argument("--precondition", default=None, help="Precondition JSON string (overrides test_plan precondition)")
    parser.add_argument("--tc", default=None, help="Comma-separated TC IDs to run (e.g. TC_003,TC_015)")
    args = parser.parse_args()

    cli_precondition = None
    if args.precondition:
        try:
            cli_precondition = json.loads(args.precondition)
        except json.JSONDecodeError as e:
            print(f"ERROR: --precondition 인자가 유효한 JSON이 아닙니다: {e}")
            sys.exit(1)

    tc_filter = None
    if args.tc:
        tc_filter = [t.strip() for t in args.tc.split(",")]

    run_all_tests(
        test_plan_path=args.test_plan,
        base_url=args.base_url,
        headless=not args.headed,
        cli_precondition=cli_precondition,
        tc_filter=tc_filter,
    )


if __name__ == "__main__":
    main()
