"""
QA UI Test Runner

사용법:
    python run_test.py --url "http://..." --pre-action ".selector"
    
또는 스크립트 내 변수를 직접 수정하여 실행
"""
import json
import argparse
from datetime import datetime
from pathlib import Path
from playwright.sync_api import sync_playwright

# Default Configuration (modify these or use command line args)
DEFAULT_URL = ""
DEFAULT_PRE_ACTION = ""

def run_test(test_url: str, pre_action: str = None):
    """Run UI tests on the specified URL"""
    results = []
    
    print("=" * 50)
    print("QA UI Test Started")
    print(f"URL: {test_url}")
    if pre_action:
        print(f"Pre-action: {pre_action}")
    print("=" * 50)
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        # Test 1: Page Load
        print("\n[TC_001] Page Load Test")
        try:
            page.goto(test_url, timeout=30000)
            page.wait_for_load_state("networkidle", timeout=10000)
            results.append({
                "tc_id": "TC_001", 
                "name": "Page Load", 
                "status": "PASS", 
                "message": "Page loaded successfully"
            })
            print("  -> PASS: Page loaded")
        except Exception as e:
            results.append({
                "tc_id": "TC_001", 
                "name": "Page Load", 
                "status": "FAIL", 
                "message": str(e)
            })
            print(f"  -> FAIL: {e}")
            browser.close()
            return results
        
        # Test 2: Pre-action (if specified)
        if pre_action:
            print(f"\n[TC_002] Pre-action: Click '{pre_action}'")
            try:
                page.wait_for_selector(pre_action, timeout=10000)
                page.click(pre_action)
                page.wait_for_timeout(1000)
                results.append({
                    "tc_id": "TC_002", 
                    "name": "Pre-action Click", 
                    "status": "PASS", 
                    "message": f"Clicked {pre_action}"
                })
                print(f"  -> PASS: Clicked {pre_action}")
            except Exception as e:
                results.append({
                    "tc_id": "TC_002", 
                    "name": "Pre-action Click", 
                    "status": "FAIL", 
                    "message": str(e)
                })
                print(f"  -> FAIL: {e}")
        
        # Test 3: UI Elements Check
        print("\n[TC_003] UI Elements Check")
        try:
            buttons = page.query_selector_all("button:visible")
            links = page.query_selector_all("a:visible")
            inputs = page.query_selector_all("input:visible")
            
            message = f"Found {len(buttons)} buttons, {len(links)} links, {len(inputs)} inputs"
            results.append({
                "tc_id": "TC_003", 
                "name": "UI Elements", 
                "status": "PASS", 
                "message": message
            })
            print(f"  -> PASS: {message}")
        except Exception as e:
            results.append({
                "tc_id": "TC_003", 
                "name": "UI Elements", 
                "status": "FAIL", 
                "message": str(e)
            })
            print(f"  -> FAIL: {e}")
        
        # Test 4: Screenshot
        print("\n[TC_004] Screenshot Capture")
        try:
            logs_dir = Path("outputs")
            logs_dir.mkdir(parents=True, exist_ok=True)
            screenshot_path = logs_dir / f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            page.screenshot(path=str(screenshot_path))
            results.append({
                "tc_id": "TC_004", 
                "name": "Screenshot", 
                "status": "PASS", 
                "message": f"Saved to {screenshot_path}"
            })
            print(f"  -> PASS: Screenshot saved")
        except Exception as e:
            results.append({
                "tc_id": "TC_004", 
                "name": "Screenshot", 
                "status": "FAIL", 
                "message": str(e)
            })
            print(f"  -> FAIL: {e}")
        
        browser.close()
    
    return results

def generate_report(results: list, test_url: str) -> str:
    """Generate markdown report"""
    today = datetime.now().strftime("%Y-%m-%d %H:%M")
    passed = sum(1 for r in results if r["status"] == "PASS")
    failed = sum(1 for r in results if r["status"] == "FAIL")
    total = len(results)
    
    report = f"""# QA UI Test Report

**Date**: {today}  
**URL**: {test_url}

## Summary

| Item | Count |
|------|-------|
| Total | {total} |
| Passed | {passed} |
| Failed | {failed} |
| Pass Rate | {passed/total*100:.0f}% |

## Results

| TC ID | Name | Status | Message |
|-------|------|--------|---------|
"""
    
    for r in results:
        status = "PASS" if r["status"] == "PASS" else "FAIL"
        message = r["message"][:50] + "..." if len(r["message"]) > 50 else r["message"]
        report += f"| {r['tc_id']} | {r['name']} | {status} | {message} |\n"
    
    return report

def main():
    parser = argparse.ArgumentParser(description="QA UI Test Runner")
    parser.add_argument("--url", type=str, default=DEFAULT_URL, help="Test URL")
    parser.add_argument("--pre-action", type=str, default=DEFAULT_PRE_ACTION, help="Pre-action selector")
    args = parser.parse_args()
    
    if not args.url:
        print("Error: URL is required. Use --url or modify DEFAULT_URL in script.")
        return
    
    results = run_test(args.url, args.pre_action if args.pre_action else None)
    
    print("\n" + "=" * 50)
    print("Test Summary")
    print("=" * 50)
    
    passed = sum(1 for r in results if r["status"] == "PASS")
    failed = sum(1 for r in results if r["status"] == "FAIL")
    print(f"Passed: {passed}, Failed: {failed}")
    
    # Save report
    output_dir = Path("outputs")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    report = generate_report(results, args.url)
    report_path = output_dir / "REPORT.md"
    report_path.write_text(report, encoding="utf-8")
    print(f"\nReport saved: {report_path}")
    
    # Save JSON results
    json_path = output_dir / "test_result.json"
    json_path.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")

if __name__ == "__main__":
    main()
