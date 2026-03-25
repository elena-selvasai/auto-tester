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
from concurrent.futures import ProcessPoolExecutor
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
RETRY_TIMEOUT_MULTIPLIER = 1.5
DEFAULT_WORKERS = 4


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
    """Resolve base URL from CLI arg > test_plan.base_url > test_plan.test_url > test_plan.meta.base_url."""
    if cli_base_url:
        return cli_base_url
    base = test_plan.get("base_url")
    if isinstance(base, str) and base and base != "${base_url}":
        return base
    test_url = test_plan.get("test_url")
    if isinstance(test_url, str) and test_url:
        return test_url
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


DEFAULT_TIMEOUT_MS = 10000


def _try_success_checks(page, tc_id, success_checks, base_url, compare_func, compare_records, timeout_ms=2000):
    """Quickly test if precondition success_checks already pass (shorter timeouts)."""
    try:
        page.set_default_timeout(timeout_ms)
        execute_action_sequence(
            page,
            f"{tc_id}.precondition_precheck",
            success_checks,
            base_url,
            compare_func,
            compare_records,
        )
        return True
    except (PlaywrightTimeoutError, PlaywrightError, AssertionError, ValueError, RuntimeError):
        return False
    finally:
        page.set_default_timeout(DEFAULT_TIMEOUT_MS)


def run_precondition(page, tc_id, precondition, base_url, compare_func, compare_records):
    """Run precondition actions and verify success before the main test.

    Optimization: checks success_checks first; if already satisfied, skips
    the (expensive) precondition actions entirely.
    """
    if precondition is None:
        return [], []

    if _try_success_checks(page, tc_id, precondition["success_checks"],
                           base_url, compare_func, compare_records):
        return ["precondition: already satisfied (skipped)"], []

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
        wait_until = action.get("wait_until", "domcontentloaded")
        page.goto(url, timeout=15000)
        try:
            page.wait_for_load_state(wait_until, timeout=8000)
        except PlaywrightTimeoutError:
            pass
        # SPA에서 API 데이터가 필요한 경우 test_plan에 wait_until: "networkidle" 명시 가능
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
        force = action.get("force", False)
        locator = page.locator(selector).first
        try:
            if not force:
                locator.scroll_into_view_if_needed(timeout=3000)
            locator.click(timeout=3000, force=bool(force))
        except (PlaywrightError, PlaywrightTimeoutError):
            safe_sel = json.dumps(selector.split(",")[0].strip())
            page.evaluate(f"""() => {{
                const el = document.querySelector({safe_sel});
                if (el) el.click();
            }}""")
        return f"click: {selector}"

    if action_type == "input":
        selector = action.get("selector")
        if not selector:
            raise ValueError(f"{tc_id}.actions[{action_index}]: input 액션에 selector가 필요합니다.")
        value = action.get("value")
        if value is None:
            raise ValueError(f"{tc_id}.actions[{action_index}]: input 액션에 value가 필요합니다.")
        locator = page.locator(selector).first
        try:
            locator.scroll_into_view_if_needed(timeout=3000)
        except (PlaywrightError, PlaywrightTimeoutError):
            pass
        try:
            locator.fill(str(value), timeout=3000)
        except (PlaywrightError, PlaywrightTimeoutError):
            css_sel = selector.split(",")[0].strip()
            try:
                locator.click(timeout=2000)
            except (PlaywrightError, PlaywrightTimeoutError):
                safe_sel = json.dumps(css_sel)
                page.evaluate(f"""() => {{
                    const el = document.querySelector({safe_sel});
                    if (el) {{ el.focus(); el.click(); }}
                }}""")
            page.keyboard.insert_text(str(value))
        return f"input: {selector}"

    if action_type == "check":
        selector = action.get("selector")
        expected = action.get("expected")
        expected_count = action.get("count")
        visible = action.get("visible")

        if selector:
            locator = page.locator(selector)
            if visible is not False:
                wait_state = action.get("wait_state", "visible")
                try:
                    locator.first.wait_for(state=wait_state, timeout=3000)
                except PlaywrightTimeoutError:
                    if wait_state == "visible":
                        locator.first.evaluate("el => el.scrollIntoView({block: 'center'})")
                        page.wait_for_timeout(500)
                        locator.first.wait_for(state="visible", timeout=2000)
                    else:
                        raise
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
                text_sample = locator.first.inner_text(timeout=2000)
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
        wait_state = action.get("wait_state", "visible")
        locator = page.locator(selector).first
        try:
            locator.wait_for(state=wait_state, timeout=3000)
        except PlaywrightTimeoutError:
            if wait_state == "visible":
                locator.evaluate("el => el.scrollIntoView({block: 'center'})")
                page.wait_for_timeout(500)
                locator.wait_for(state="visible", timeout=2000)
            else:
                raise
        actual = locator.get_attribute(attribute)
        expected = action.get("expected")
        if expected is not None:
            if attribute.lower() in BOOLEAN_ATTRIBUTES and str(expected).lower() in ("true", "false"):
                # 불리언 속성: 속성 존재 여부로 true/false 판단 (값이 아닌 존재/부재)
                actual_bool = "true" if actual is not None else "false"
                if actual_bool != str(expected).lower():
                    hint = ""
                    if attribute.lower() == "disabled":
                        if str(expected).lower() == "true":
                            hint = " (요소가 비활성화 상태여야 하지만 활성화되어 있음)"
                        else:
                            hint = " (요소가 활성화 상태여야 하지만 비활성화되어 있음)"
                    elif attribute.lower() == "checked":
                        if str(expected).lower() == "true":
                            hint = " (체크되어야 하지만 체크되지 않음)"
                        else:
                            hint = " (체크되지 않아야 하지만 체크되어 있음)"
                    raise AssertionError(
                        f"{tc_id}.actions[{action_index}]: boolean attribute mismatch "
                        f"({attribute} present={actual is not None}, expected={expected}){hint}"
                    )
            else:
                match_mode = action.get("match_mode", "exact")
                if match_mode == "contains":
                    if str(expected) not in str(actual or ""):
                        raise AssertionError(
                            f"{tc_id}.actions[{action_index}]: attribute '{attribute}' does not contain '{expected}' (actual='{actual}')"
                        )
                elif match_mode == "not_contains":
                    if str(expected) in str(actual or ""):
                        raise AssertionError(
                            f"{tc_id}.actions[{action_index}]: attribute '{attribute}' should not contain '{expected}' (actual='{actual}')"
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

    if action_type == "wait_for_selector":
        selector = action.get("selector")
        if not selector:
            raise ValueError(f"{tc_id}.actions[{action_index}]: wait_for_selector 액션에 selector가 필요합니다.")
        state = action.get("state", "visible")
        timeout = int(action.get("timeout", 5000))
        page.wait_for_selector(selector, state=state, timeout=timeout)
        return f"wait_for_selector: {selector} ({state})"

    if action_type == "hover":
        selector = action.get("selector")
        if not selector:
            raise ValueError(f"{tc_id}.actions[{action_index}]: hover 액션에 selector가 필요합니다.")
        force = action.get("force", False)
        locator = page.locator(selector).first
        try:
            locator.scroll_into_view_if_needed(timeout=3000)
        except (PlaywrightError, PlaywrightTimeoutError):
            pass
        try:
            locator.hover(timeout=3000, force=bool(force))
        except (PlaywrightError, PlaywrightTimeoutError):
            # 요소가 overflow:hidden 내부 등으로 visible 불가 시 JS 이벤트로 대체
            css_sel = selector.split(",")[0].strip()
            safe_sel = json.dumps(css_sel)
            page.evaluate(f"""() => {{
                const el = document.querySelector({safe_sel});
                if (el) {{
                    el.dispatchEvent(new MouseEvent('mouseenter', {{bubbles: true, cancelable: true}}));
                    el.dispatchEvent(new MouseEvent('mouseover', {{bubbles: true, cancelable: true}}));
                }}
            }}""")
            page.wait_for_timeout(200)
        return f"hover: {selector}"

    if action_type == "scroll_into_view":
        selector = action.get("selector")
        if not selector:
            raise ValueError(f"{tc_id}.actions[{action_index}]: scroll_into_view 액션에 selector가 필요합니다.")
        locator = page.locator(selector).first
        try:
            locator.scroll_into_view_if_needed(timeout=3000)
        except (PlaywrightError, PlaywrightTimeoutError):
            try:
                locator.evaluate("el => el.scrollIntoView({block: 'center', behavior: 'instant'})")
                page.wait_for_timeout(300)
            except (PlaywrightError, PlaywrightTimeoutError):
                css_sel = selector.split(",")[0].strip()
                safe_sel = json.dumps(css_sel)
                page.evaluate(f"""() => {{
                    const el = document.querySelector({safe_sel});
                    if (el) el.scrollIntoView({{block: 'center', behavior: 'instant'}});
                }}""")
                page.wait_for_timeout(300)
        return f"scroll_into_view: {selector}"

    if action_type == "scroll_to_element":
        selector = action.get("selector")
        if not selector:
            raise ValueError(f"{tc_id}.actions[{action_index}]: scroll_to_element 액션에 selector가 필요합니다.")
        locator = page.locator(selector).first
        try:
            locator.scroll_into_view_if_needed(timeout=3000)
            page.wait_for_timeout(300)
        except (PlaywrightError, PlaywrightTimeoutError):
            css_sel = selector.split(",")[0].strip()
            safe_sel = json.dumps(css_sel)
            page.evaluate(f"""() => {{
                const el = document.querySelector({safe_sel});
                if (el) el.scrollIntoView({{block: 'center', behavior: 'instant'}});
            }}""")
            page.wait_for_timeout(300)
        return f"scroll_to_element: {selector}"

    if action_type == "check_is_checked":
        selector = action.get("selector")
        if not selector:
            raise ValueError(f"{tc_id}.actions[{action_index}]: check_is_checked 액션에 selector가 필요합니다.")
        locator = page.locator(selector).first
        try:
            locator.wait_for(state="attached", timeout=3000)
        except PlaywrightTimeoutError:
            raise
        actual_checked = locator.is_checked()
        expected = action.get("expected")
        if expected is not None:
            expected_bool = str(expected).lower() == "true"
            if actual_checked != expected_bool:
                hint = "(체크되어야 하지만 체크되지 않음)" if expected_bool else "(체크되지 않아야 하지만 체크되어 있음)"
                raise AssertionError(
                    f"{tc_id}.actions[{action_index}]: check_is_checked mismatch "
                    f"(actual={actual_checked}, expected={expected}) {hint}"
                )
        return f"check_is_checked: {selector} checked={actual_checked}"

    if action_type == "evaluate":
        expression = action.get("expression")
        if not expression:
            raise ValueError(f"{tc_id}.actions[{action_index}]: evaluate 액션에 expression이 필요합니다.")
        result = page.evaluate(expression)
        return f"evaluate: {str(expression)[:80]}"

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


def _worker_run_batch(args):
    """Worker process: 별도 Playwright 인스턴스에서 TC 배치를 실행합니다.

    precondition_error 발생 시 즉시 중단하고 나머지 TC를 skipped 처리합니다.
    """
    tc_batch, base_url, headless, global_precondition = args
    compare_func = load_compare_function()
    compare_records = []
    results = []
    precondition_aborted = False
    abort_tc_id = None
    abort_message = None

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context(viewport={"width": 1280, "height": 800})
        page = context.new_page()

        for idx, tc in enumerate(tc_batch):
            tc_id = tc.get("tc_id", "")
            name = tc.get("name", "")
            category = tc.get("category", "basic_function")
            priority = tc.get("priority", "medium")
            expected = tc.get("expected", "")

            status, message, elapsed_ms, screenshots = execute_test_case(
                page, tc, base_url, compare_func, compare_records,
                global_precondition=global_precondition,
            )

            print(f"[{tc_id}] {name} -> {status.upper()}: {message}", flush=True)
            result_entry = {
                "tc_id": tc_id, "category": category, "name": name,
                "status": status, "message": message, "expected": expected,
                "priority": priority, "elapsed_ms": elapsed_ms,
            }
            if screenshots:
                result_entry["screenshots"] = screenshots
            results.append(result_entry)

            # precondition_error 시 즉시 중단
            if status == "failed" and message.startswith("precondition failed:"):
                precondition_aborted = True
                abort_tc_id = tc_id
                abort_message = message
                print(
                    f"\n[ABORT] precondition_error 발생 — 테스트 실행 즉시 중단\n"
                    f"  TC: {tc_id}\n"
                    f"  원인: {message}\n"
                    f"  → CSS 선택자가 실제 앱 DOM과 일치하는지 확인 후 재실행하세요.",
                    flush=True,
                )
                # 나머지 TC를 skipped 처리
                for remaining_tc in tc_batch[idx + 1:]:
                    results.append({
                        "tc_id": remaining_tc.get("tc_id", ""),
                        "category": remaining_tc.get("category", "basic_function"),
                        "name": remaining_tc.get("name", ""),
                        "status": "skipped",
                        "message": f"precondition_abort: {abort_tc_id}에서 precondition 실패로 중단됨",
                        "expected": remaining_tc.get("expected", ""),
                        "priority": remaining_tc.get("priority", "medium"),
                        "elapsed_ms": 0,
                    })
                break

        browser.close()

    return results, compare_records, precondition_aborted, abort_tc_id, abort_message


def run_all_tests(test_plan_path=DEFAULT_TEST_PLAN_PATH, base_url=None, headless=True,
                  cli_precondition=None, tc_filter=None, workers=DEFAULT_WORKERS):
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
    global_precondition = cli_precondition if cli_precondition is not None else test_plan.get("precondition")

    # compare_with_reference 액션이 있는데 스크립트가 없으면 조기 경고
    compare_func = load_compare_function()
    if compare_func is None:
        has_compare = any(
            act.get("action") == "compare_with_reference"
            for tc in test_cases
            for act in tc.get("actions", [])
        )
        if has_compare:
            print("[WARN] compare_screenshot.py를 로드할 수 없습니다. compare_with_reference 액션은 실패합니다.")
            print(f"  경로: .cursor/skills/qa-automation/scripts/compare_screenshot.py")

    # TC 필터링
    filtered_tcs = [tc for tc in test_cases if not tc_filter or tc.get("tc_id", "") in tc_filter]
    if not filtered_tcs:
        print("실행할 TC가 없습니다.")
        return None

    actual_workers = min(workers, len(filtered_tcs))

    precondition_aborted = False
    abort_tc_id = None
    abort_message = None

    if actual_workers <= 1:
        # 순차 실행
        results_data, compare_records, precondition_aborted, abort_tc_id, abort_message = (
            _worker_run_batch(
                (filtered_tcs, resolved_base_url, headless, global_precondition)
            )
        )
    else:
        # 병렬 실행: TC를 N개 배치로 분배
        batches = [[] for _ in range(actual_workers)]
        for i, tc in enumerate(filtered_tcs):
            batches[i % actual_workers].append(tc)

        batch_args = [
            (batch, resolved_base_url, headless, global_precondition)
            for batch in batches if batch
        ]

        print(f"=== 병렬 실행: {len(batch_args)} workers, {len(filtered_tcs)} TCs ===")

        results_data = []
        compare_records = []

        with ProcessPoolExecutor(max_workers=len(batch_args)) as executor:
            futures = [executor.submit(_worker_run_batch, args) for args in batch_args]
            for future in futures:
                batch_results, batch_compare, batch_aborted, batch_abort_tc, batch_abort_msg = future.result()
                results_data.extend(batch_results)
                compare_records.extend(batch_compare)
                if batch_aborted and not precondition_aborted:
                    precondition_aborted = True
                    abort_tc_id = batch_abort_tc
                    abort_message = batch_abort_msg

    # TC 원래 순서로 정렬
    tc_order = {tc.get("tc_id"): i for i, tc in enumerate(filtered_tcs)}
    results_data.sort(key=lambda r: tc_order.get(r["tc_id"], 999))

    # 결과에서 summary 집계
    summary = {"total": 0, "passed": 0, "failed": 0, "skipped": 0, "errors": 0}
    category_summary = {}
    for r in results_data:
        summary["total"] += 1
        status = r["status"]
        summary[status] = summary.get(status, 0) + 1
        cat = r.get("category", "basic_function")
        if cat not in category_summary:
            category_summary[cat] = {"total": 0, "passed": 0, "failed": 0, "skipped": 0, "errors": 0}
        category_summary[cat]["total"] += 1
        category_summary[cat][status] = category_summary[cat].get(status, 0) + 1

    test_result = {
        "test_plan_id": test_plan.get("test_plan_id", ""),
        "executed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "base_url": resolved_base_url,
        "summary": summary,
        "category_summary": category_summary,
        "results": results_data,
    }

    # precondition_abort 정보 포함
    if precondition_aborted:
        test_result["precondition_abort"] = {
            "aborted": True,
            "tc_id": abort_tc_id,
            "message": abort_message,
        }

    with open(DEFAULT_TEST_RESULT_PATH, "w", encoding="utf-8") as f:
        json.dump(test_result, f, ensure_ascii=False, indent=2)

    with open(DEFAULT_COMPARE_RESULT_PATH, "w", encoding="utf-8") as f:
        json.dump({"generated_at": datetime.now().isoformat(), "items": compare_records}, f, ensure_ascii=False, indent=2)

    if precondition_aborted:
        print(
            f"\n=== [PRECONDITION ABORT] 테스트 중단됨 ===\n"
            f"원인 TC: {abort_tc_id}\n"
            f"메시지: {abort_message}\n"
            f"결과 저장: {DEFAULT_TEST_RESULT_PATH}\n"
            f"총: {summary['total']}, 통과: {summary['passed']}, 실패: {summary['failed']}, "
            f"스킵: {summary['skipped']}, 오류: {summary['errors']}\n"
            f"\n→ 선택자가 실제 앱 DOM과 일치하는지 확인한 후 test_plan.json을 수정하고 재실행하세요."
        )
    else:
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
    parser.add_argument("--workers", type=int, default=DEFAULT_WORKERS,
                        help=f"병렬 worker 수 (기본: {DEFAULT_WORKERS}, 1이면 순차 실행)")
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

    result = run_all_tests(
        test_plan_path=args.test_plan,
        base_url=args.base_url,
        headless=not args.headed,
        cli_precondition=cli_precondition,
        tc_filter=tc_filter,
        workers=args.workers,
    )
    if result and result.get("precondition_abort", {}).get("aborted"):
        sys.exit(3)  # exit code 3 = precondition_abort


if __name__ == "__main__":
    main()
