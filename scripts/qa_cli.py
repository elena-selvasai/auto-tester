#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scripts/qa_cli.py - QA 자동화 상태 관리 CLI

YAML을 상태 DB로 사용. 에이전트의 모든 Phase 전환은 이 CLI를 통해서만 수행.
검증 게이트로 순서 위반, 필수 산출물 미존재 시 거부.
매 명령 실행 후 리마인더(다음 할 일 + 경고 + 랜덤 팁 2개) 강제 출력.

Usage:
  python scripts/qa_cli.py init
  python scripts/qa_cli.py start <phase>
  python scripts/qa_cli.py complete <phase> [--files file1 file2 ...]
  python scripts/qa_cli.py fail <phase> <"error message">
  python scripts/qa_cli.py next
  python scripts/qa_cli.py status
  python scripts/qa_cli.py resume
  python scripts/qa_cli.py set test_url <url>
  python scripts/qa_cli.py set github_repo <owner/repo>
  python scripts/qa_cli.py set skip_github <true|false>

Exit Codes:
  0 - 성공
  1 - 사용법 오류 또는 상태 파일 없음
  2 - 검증 게이트 거부 (이전 Phase 미완료, 필수 파일 없음 등)
"""

import sys
import os
import json
import random
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

# Windows 콘솔 UTF-8 출력 설정
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML이 설치되지 않았습니다.")
    print("설치: pip install pyyaml")
    sys.exit(1)

STATE_FILE = "outputs/qa_state.yaml"
SUPPORTED_INPUT_EXTENSIONS = {".pptx", ".docx", ".pdf", ".png", ".jpg", ".jpeg"}

# ============================================================
# Phase 메타데이터: 의존성, 필수 입력, 필수 산출물
# ============================================================

PHASE_META = {
    0: {
        "name": "사전 검증",
        "required_before": [],
        "required_inputs": [],
        "produces_required": [],
        "produces": [],
        "optional": False,
    },
    1: {
        "name": "문서 분석",
        "required_before": [0],
        "required_inputs": [],
        "produces_required": ["outputs/scenario_draft.md", "outputs/extract_result.json"],
        "produces": [
            "outputs/scenario_draft.md",
            "outputs/extract_result.json",
            "outputs/scenario_draft_source.md",
        ],
        "optional": False,
    },
    2: {
        "name": "테스트 설계",
        "required_before": [1],
        "required_inputs": ["outputs/extract_result.json"],
        "produces_required": ["outputs/test_plan.json"],
        "produces": [
            "outputs/test_plan_skeleton.json",
            "outputs/test_plan.json",
        ],
        "optional": False,
    },
    3: {
        "name": "테스트 실행",
        "required_before": [2],
        "required_inputs": ["outputs/test_plan.json"],
        "produces_required": ["outputs/test_result.json"],
        "produces": ["outputs/test_result.json"],
        "optional": False,
    },
    4: {
        "name": "리포트 생성",
        "required_before": [3],
        "required_inputs": ["outputs/test_result.json"],
        "produces_required": ["outputs/REPORT.md"],
        "produces": ["outputs/REPORT.md"],
        "optional": False,
    },
    5: {
        "name": "GitHub 이슈 등록",
        "required_before": [4],
        "required_inputs": ["outputs/REPORT.md"],
        "produces_required": ["outputs/issues_created.json"],
        "produces": ["outputs/issues_created.json"],
        "optional": False,
    },
    5.5: {
        "name": "실패 수정",
        "required_before": [5],
        "required_inputs": ["outputs/test_result.json"],
        "produces_required": ["outputs/fix_log.json"],
        "produces": ["outputs/fix_log.json"],
        "optional": True,
    },
    6: {
        "name": "정리",
        "required_before": [4],
        "required_inputs": ["outputs/REPORT.md"],
        "produces_required": [],
        "produces": [],
        "optional": False,
    },
}

PHASE_ORDER = [0, 1, 2, 3, 4, 5, 5.5, 6]

# ============================================================
# Phase별 팁 풀
# ============================================================

TIPS = {
    0: [
        "test_url은 http:// 또는 https:// 프로토콜을 포함한 전체 URL이어야 합니다.",
        "GitHub 이슈 등록이 불필요하면 skip_github=true로 설정하세요.",
        "gh auth status 명령으로 GitHub CLI 로그인 상태를 먼저 확인하세요.",
        "테스트할 페이지가 로그인이 필요하다면 사전 동작(precondition)을 미리 정의하세요.",
    ],
    1: [
        "PPTX 노트 슬라이드에 숨겨진 요구사항이 있을 수 있습니다.",
        "outputs/reference/ 폴더의 참조 이미지 수를 확인하세요 - Phase 3 화면 비교에 사용됩니다.",
        "scenario_draft_source.md 하단 '구성 체크 리스트'를 반드시 확인하세요.",
        "extract_document.py는 디렉터리를 주면 첫 번째 지원 파일을 자동 선택합니다.",
        "이미지 파일만 있으면 와이어프레임으로 등록되어 참조 이미지로만 활용됩니다.",
        "여러 문서가 있으면 기획서 파일명을 직접 지정하세요.",
    ],
    2: [
        "base_url은 ${base_url} 플레이스홀더로 두세요 - 실행 시 실제 URL로 대체됩니다.",
        "선택자 우선순위: data-testid > id > aria-label > class > text",
        "compare_with_reference 액션은 outputs/reference/ 이미지가 있을 때만 추가하세요.",
        "카테고리별 최소 TC 수: basic_function 8개, button_state 4개, navigation 3개",
        "python validate_json.py outputs/test_plan.json 으로 항상 검증하세요.",
        "동적 클래스(css-1a2b3c 형태)는 선택자로 사용하면 안 됩니다.",
    ],
    3: [
        "browser_snapshot 먼저! 실제 DOM 확인 없이 test_plan.json 선택자를 맹신하지 마세요.",
        "요소 클릭 전 스크롤 여부 확인 - viewport 밖 요소는 클릭이 안 될 수 있습니다.",
        "오답 테스트는 실제 오답을 선택하여 피드백을 검증해야 합니다. 정답으로 대체 금지.",
        "스크린샷은 주요 인터랙션 전/후 모두 찍으세요. 실패 증거 수집이 핵심입니다.",
        "타임아웃 오류는 wait 시간을 2배로 늘린 후 재시도하세요.",
        "compare_screenshot.py 임계값: threshold=10이 기본값, 낮을수록 엄격합니다.",
    ],
    4: [
        "REPORT.md에 '발견 사항' 섹션을 포함하세요 - 기획서 vs 실제 차이점.",
        "카테고리별 통계는 test_result.json의 category 필드로 집계합니다.",
        "스크린샷 목록도 REPORT.md에 포함하면 검토가 용이합니다.",
    ],
    5: [
        "GitHub CLI 미설치 시 skip_github=true로 설정하고 Phase 5를 skip하세요.",
        "이슈 본문 outputs/issue_body.md는 Phase 6 정리 후에도 보존됩니다.",
        "gh issue create -R owner/repo 형식으로 리포지토리를 명시하세요.",
    ],
    5.5: [
        "selector_mismatch, text_mismatch는 수정 가능. app_bug는 절대 수정하지 마세요.",
        "수정 적용은 반드시 사용자 승인 후에만 가능합니다.",
        "DOM 분석 없이 선택자를 임의로 수정하지 마세요.",
    ],
    6: [
        "debug_*.png, issue_ISS_* 파일을 반드시 삭제하세요.",
        "outputs_/, outputs__/ 등 이전 실행 폴더 삭제를 사용자에게 제안하세요.",
        "최종 산출물 9개(REPORT.md, test_plan.json, test_result.json 등)가 남아있는지 확인하세요.",
    ],
}

# ============================================================
# 헬퍼 함수
# ============================================================

def get_phase_key(phase_num):
    """Phase 번호를 YAML 키(문자열)로 변환. 5.5 포함."""
    return str(float(phase_num)) if phase_num == 5.5 else str(int(phase_num))


def phase_num_from_arg(arg):
    """CLI 인자 문자열을 Phase 번호(int 또는 float)로 변환."""
    f = float(arg)
    return f if f == 5.5 else int(f)


def is_phase_done(state, phase_num):
    """Phase가 completed 또는 skipped 상태인지 확인."""
    phase = state["phases"].get(get_phase_key(phase_num), {})
    return phase.get("status") in ("completed", "skipped")


def is_workflow_completed(state):
    """필수 Phase가 모두 완료되었는지 확인 (optional Phase는 무시)."""
    for phase_num in PHASE_ORDER:
        if PHASE_META[phase_num].get("optional", False):
            continue
        if not is_phase_done(state, phase_num):
            return False
    return True


def has_supported_input_document(input_dir="inputs"):
    """inputs/ 폴더 내 지원 문서 존재 여부 확인."""
    if not os.path.isdir(input_dir):
        return False
    for name in os.listdir(input_dir):
        ext = os.path.splitext(name)[1].lower()
        if ext in SUPPORTED_INPUT_EXTENSIONS:
            return True
    return False


def validate_github_auth():
    """gh CLI 설치/로그인 상태 검증."""
    if shutil.which("gh") is None:
        return False, "GitHub CLI(gh)가 설치되어 있지 않습니다. skip_github=true를 설정하거나 gh를 설치하세요."
    try:
        result = subprocess.run(
            ["gh", "auth", "status"],
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as exc:
        return False, f"gh 실행 실패: {exc}"

    if result.returncode != 0:
        output = (result.stderr or result.stdout or "").strip()
        return False, f"GitHub 인증 상태 확인 실패(gh auth status): {output}"
    return True, None


def validate_phase0_config(state):
    """Phase 0 완료 전 필수 설정 검증."""
    config = state.get("config", {})
    test_url = config.get("test_url") or ""
    if not (isinstance(test_url, str) and test_url.startswith(("http://", "https://"))):
        return False, "config.test_url 이 유효하지 않습니다. 예: python scripts/qa_cli.py set test_url http://localhost:3000"

    # precondition 확인: 미설정(None)이면 "선행 동작 없음"으로 간주하여 통과
    precondition = config.get("precondition")
    if precondition is not None and not isinstance(precondition, dict):
        return False, (
            "config.precondition 형식이 잘못되었습니다. JSON 객체여야 합니다:\n"
            "  python scripts/qa_cli.py set precondition '{\"description\":\"...\",\"actions\":[...],\"success_checks\":[...]}'\n"
            "선행 동작을 제거하려면:\n"
            "  python scripts/qa_cli.py set precondition none"
        )

    skip_github = bool(config.get("skip_github", False))
    github_repo = config.get("github_repo") or ""
    if not skip_github:
        if not isinstance(github_repo, str) or "/" not in github_repo:
            return False, (
                "config.github_repo 가 필요합니다(owner/repo). "
                "또는 python scripts/qa_cli.py set skip_github true 로 GitHub 단계를 건너뛰세요."
            )
        owner, repo = github_repo.split("/", 1)
        if not owner.strip() or not repo.strip():
            return False, "config.github_repo 형식이 올바르지 않습니다. owner/repo 형식으로 설정하세요."
        ok, reason = validate_github_auth()
        if not ok:
            return False, reason
    return True, None


def load_state():
    """YAML 상태 파일 로드. 없으면 None 반환."""
    if not os.path.exists(STATE_FILE):
        return None
    with open(STATE_FILE, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def save_state(state):
    """상태를 YAML 파일로 저장."""
    state["session"]["updated_at"] = datetime.now().isoformat()
    os.makedirs("outputs", exist_ok=True)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        yaml.dump(state, f, allow_unicode=True, default_flow_style=False, sort_keys=False)


def find_next_pending(state):
    """다음 pending 상태의 Phase 번호 반환. 없으면 None."""
    phases = state.get("phases", {})
    for p in PHASE_ORDER:
        key = get_phase_key(p)
        st = phases.get(key, {}).get("status", "pending")
        if st == "pending":
            return p
    return None


def get_random_tips(phase_num, count=2):
    """Phase별 팁 풀에서 랜덤 팁 선택."""
    key = 5.5 if phase_num == 5.5 else int(phase_num)
    pool = TIPS.get(key, [])
    if not pool:
        return []
    return random.sample(pool, min(count, len(pool)))


def get_next_action_text(state, current_phase=None):
    """현재 상태에서 다음 할 일 1개를 문자열로 반환."""
    phases = state.get("phases", {})

    # in_progress Phase 찾기
    for p in PHASE_ORDER:
        key = get_phase_key(p)
        if phases.get(key, {}).get("status") == "in_progress":
            return f"Phase {p} 작업을 완료한 후 실행: python scripts/qa_cli.py complete {p}"

    # 다음 pending Phase 찾기
    nxt = find_next_pending(state)
    if nxt is not None:
        return f"다음 Phase 시작: python scripts/qa_cli.py start {nxt}"

    return "모든 Phase 완료. python scripts/qa_cli.py status 로 결과를 확인하세요."


def get_warning_text(phase_num):
    """Phase별 경고 메시지 반환."""
    warnings = {
        0: "test_url은 http:// 프로토콜을 포함한 전체 URL이어야 합니다.",
        1: "inputs/ 폴더에 지원 파일(PPTX/DOCX/PDF/PNG)이 반드시 있어야 합니다.",
        2: "test_plan.json 생성 후 반드시 validate_json.py로 검증하세요.",
        3: "browser_snapshot 없이 선택자를 신뢰하지 마세요. DOM 먼저 확인.",
        4: "test_result.json의 모든 카테고리 결과가 포함되었는지 확인하세요.",
        5: "github_repo 미설정 시 skip_github=true로 설정하고 Phase를 skip하세요.",
        5.5: "모든 수정은 사용자 승인 후에만 적용. app_bug는 절대 수정 금지.",
        6: "debug_*.png, issue_ISS_* 파일 삭제 후 최종 산출물 9개를 확인하세요.",
    }
    key = 5.5 if phase_num == 5.5 else int(phase_num)
    return warnings.get(key, "이전 Phase 산출물 파일을 반드시 확인하세요.")


def print_reminder(state, phase_num):
    """리마인더 블록 출력 (다음 할 일 + 경고 + 랜덤 팁 2개)."""
    next_action = get_next_action_text(state, phase_num)
    warning = get_warning_text(phase_num)
    tips = get_random_tips(phase_num)

    print()
    print("[REMINDER] " + "─" * 44)
    print(f"다음 할 일: {next_action}")
    print(f"경고: {warning}")
    for i, tip in enumerate(tips, 1):
        print(f"팁 {i}: {tip}")
    print("─" * 55)


# ============================================================
# 검증 게이트
# ============================================================

def validate_start_gate(state, phase_num):
    """
    Phase 시작 가능 여부 검증.
    반환: (True, None) 또는 (False, "거부 사유")
    """
    meta = PHASE_META.get(phase_num)
    if meta is None:
        return False, f"알 수 없는 Phase 번호: {phase_num}"

    phases = state.get("phases", {})

    # 선행 Phase 완료 여부 확인
    for req_phase in meta.get("required_before", []):
        req_key = get_phase_key(req_phase)
        req_status = phases.get(req_key, {}).get("status", "pending")
        if req_status not in ("completed", "skipped"):
            req_name = PHASE_META[req_phase]["name"]
            return False, (
                f"Phase {req_phase} ({req_name})이(가) 완료되지 않았습니다.\n"
                f"현재 상태: {req_status}\n"
                f"해결 방법: python scripts/qa_cli.py complete {req_phase}"
            )

    # 선행 Phase의 필수 입력 파일 존재 확인
    for req_file in meta.get("required_inputs", []):
        if not os.path.exists(req_file):
            return False, (
                f"필수 입력 파일이 없습니다: {req_file}\n"
                f"이전 Phase를 먼저 완료하세요."
            )

    # Phase 1 시작 시 inputs/ 문서 존재 확인
    if phase_num == 1 and not has_supported_input_document("inputs"):
        return False, "inputs/ 폴더에 지원 문서(PPTX/DOCX/PDF/PNG/JPG)가 없습니다."

    return True, None


def validate_complete_gate(state, phase_num):
    """
    Phase 완료 가능 여부 검증 (필수 산출물 파일 존재 확인).
    반환: (True, None) 또는 (False, "거부 사유")
    """
    meta = PHASE_META.get(phase_num)
    if meta is None:
        return False, f"알 수 없는 Phase 번호: {phase_num}"

    config = state.get("config", {})
    skip_github = bool(config.get("skip_github", False))

    # Phase 0 완료 시 필수 config + gh 인증 상태 검증
    if phase_num == 0:
        ok, reason = validate_phase0_config(state)
        if not ok:
            return False, reason

    # Phase 5는 skip_github=true이면 필수 산출물 체크 생략
    if phase_num == 5 and skip_github:
        return True, None

    missing = []
    for req_file in meta.get("produces_required", []):
        if not os.path.exists(req_file):
            missing.append(req_file)

    if missing:
        return False, (
            "필수 산출물 파일이 없습니다:\n" +
            "\n".join(f"  - {f}" for f in missing) +
            "\n파일을 생성한 후 다시 시도하세요."
        )

    return True, None


# ============================================================
# 명령어 핸들러
# ============================================================

def cmd_init(args):
    """새 세션 초기화."""
    if os.path.exists(STATE_FILE):
        print(f"기존 상태 파일이 있습니다: {STATE_FILE}")
        print("기존 세션을 재사용하려면: python scripts/qa_cli.py resume")
        print(f"새로 시작하려면 {STATE_FILE} 을 삭제 후 다시 실행하세요.")
        return 1

    session_id = f"QA_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    state = {
        "session": {
            "id": session_id,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "current_phase": 0,
            "overall_status": "pending",
        },
        "config": {
            "test_url": None,
            "precondition": None,
            "github_repo": None,
            "skip_github": False,
        },
        "phases": {
            get_phase_key(p): {
                "name": PHASE_META[p]["name"],
                "status": "pending",
                "optional": PHASE_META[p].get("optional", False),
                "started_at": None,
                "completed_at": None,
                "outputs": [],
                "errors": [],
            }
            for p in PHASE_META
        },
    }
    save_state(state)

    print(f"[OK] 새 세션 초기화 완료: {session_id}")
    print(f"상태 파일: {STATE_FILE}")
    print_reminder(state, 0)
    return 0


def cmd_start(args):
    """Phase 시작 - 검증 게이트 통과 시에만 in_progress로 전환."""
    if len(args) < 1:
        print("Usage: qa_cli.py start <phase_number>")
        return 1

    try:
        phase_num = phase_num_from_arg(args[0])
    except ValueError:
        print(f"ERROR: 유효하지 않은 Phase 번호: {args[0]}")
        return 1

    state = load_state()
    if state is None:
        print("ERROR: 상태 파일이 없습니다. 먼저 실행: python scripts/qa_cli.py init")
        return 1

    phase_key = get_phase_key(phase_num)

    # 이미 완료된 Phase 경고
    current_status = state["phases"].get(phase_key, {}).get("status", "pending")
    if current_status == "completed":
        print(f"[WARN] Phase {phase_num}는 이미 완료된 상태입니다.")
        print(f"재실행하려면 상태 파일에서 해당 Phase status를 'pending'으로 수동 변경하세요.")
        return 2

    # 검증 게이트
    ok, reason = validate_start_gate(state, phase_num)
    if not ok:
        print(f"[GATE BLOCKED] Phase {phase_num} 시작 거부")
        print(f"사유: {reason}")
        print()
        print("현재 상태 확인: python scripts/qa_cli.py status")
        return 2

    # 상태 전환
    state["phases"][phase_key]["status"] = "in_progress"
    state["phases"][phase_key]["started_at"] = datetime.now().isoformat()
    state["session"]["current_phase"] = phase_num
    state["session"]["overall_status"] = "in_progress"
    save_state(state)

    phase_name = PHASE_META[phase_num]["name"]
    print(f"[START] Phase {phase_num}: {phase_name}")
    print_reminder(state, phase_num)
    return 0


def cmd_complete(args):
    """Phase 완료 - 필수 산출물 확인 후 completed로 전환."""
    if len(args) < 1:
        print("Usage: qa_cli.py complete <phase_number> [--files file1 file2 ...]")
        return 1

    try:
        phase_num = phase_num_from_arg(args[0])
    except ValueError:
        print(f"ERROR: 유효하지 않은 Phase 번호: {args[0]}")
        return 1

    state = load_state()
    if state is None:
        print("ERROR: 상태 파일이 없습니다. 먼저 실행: python scripts/qa_cli.py init")
        return 1

    # --files 파싱
    produced_files = []
    if "--files" in args:
        idx = args.index("--files")
        produced_files = args[idx + 1:]

    # 검증 게이트
    ok, reason = validate_complete_gate(state, phase_num)
    if not ok:
        print(f"[GATE BLOCKED] Phase {phase_num} 완료 거부")
        print(f"사유: {reason}")
        return 2

    # Phase 5 skip_github 처리
    skip_github = state.get("config", {}).get("skip_github", False)
    phase_key = get_phase_key(phase_num)
    if phase_num == 5 and skip_github:
        state["phases"][phase_key]["status"] = "skipped"
        state["phases"][phase_key]["completed_at"] = datetime.now().isoformat()
        print(f"[SKIPPED] Phase 5: GitHub 이슈 등록 (skip_github=true)")
    else:
        # 상태 전환
        meta = PHASE_META[phase_num]
        state["phases"][phase_key]["status"] = "completed"
        state["phases"][phase_key]["completed_at"] = datetime.now().isoformat()
        state["phases"][phase_key]["outputs"] = produced_files or meta.get("produces", [])
        print(f"[COMPLETE] Phase {phase_num}: {PHASE_META[phase_num]['name']}")

    # 필수 Phase 완료 여부 확인 → overall_status 갱신 (optional Phase는 무시)
    if is_workflow_completed(state):
        state["session"]["overall_status"] = "completed"
    else:
        state["session"]["overall_status"] = "in_progress"
    save_state(state)

    # 다음 Phase 안내
    nxt = find_next_pending(state)
    print_reminder(state, nxt if nxt is not None else phase_num)
    return 0


def cmd_fail(args):
    """Phase 실패 기록."""
    if len(args) < 2:
        print('Usage: qa_cli.py fail <phase_number> "<error message>"')
        return 1

    try:
        phase_num = phase_num_from_arg(args[0])
    except ValueError:
        print(f"ERROR: 유효하지 않은 Phase 번호: {args[0]}")
        return 1

    error_msg = " ".join(args[1:])
    state = load_state()
    if state is None:
        print("ERROR: 상태 파일이 없습니다.")
        return 1

    phase_key = get_phase_key(phase_num)
    if phase_key not in state["phases"]:
        print(f"ERROR: 알 수 없는 Phase: {phase_num}")
        return 1

    state["phases"][phase_key]["status"] = "failed"
    if "errors" not in state["phases"][phase_key]:
        state["phases"][phase_key]["errors"] = []
    state["phases"][phase_key]["errors"].append({
        "timestamp": datetime.now().isoformat(),
        "message": error_msg,
    })
    state["session"]["overall_status"] = "failed"
    save_state(state)

    print(f"[FAIL] Phase {phase_num}: {PHASE_META[phase_num]['name']}")
    print(f"오류: {error_msg}")
    print()
    print(f"재시작: python scripts/qa_cli.py start {phase_num}")
    print_reminder(state, phase_num)
    return 0


def cmd_next(args):
    """현재 상태를 읽어 다음 행동 지시."""
    state = load_state()
    if state is None:
        print("상태 파일이 없습니다.")
        print("새 세션 시작: python scripts/qa_cli.py init")
        return 1

    phases = state.get("phases", {})

    # in_progress Phase 찾기
    for p in PHASE_ORDER:
        key = get_phase_key(p)
        if phases.get(key, {}).get("status") == "in_progress":
            print(f"[현재 진행 중] Phase {p}: {PHASE_META[p]['name']}")
            print_reminder(state, p)
            return 0

    # failed Phase 찾기
    for p in PHASE_ORDER:
        key = get_phase_key(p)
        if phases.get(key, {}).get("status") == "failed":
            print(f"[실패 감지] Phase {p}: {PHASE_META[p]['name']}")
            errors = phases[key].get("errors", [])
            if errors:
                print(f"마지막 오류: {errors[-1].get('message', '')}")
            print(f"재시작: python scripts/qa_cli.py start {p}")
            print_reminder(state, p)
            return 0

    # 다음 pending Phase
    nxt = find_next_pending(state)
    if nxt is not None:
        print(f"[다음 단계] Phase {nxt}: {PHASE_META[nxt]['name']}")
        print_reminder(state, nxt)
    else:
        print("[완료] 모든 Phase가 완료되었습니다.")
        print("최종 결과 확인: python scripts/qa_cli.py status")
    return 0


def cmd_status(args):
    """전체 Phase 현황 출력."""
    state = load_state()
    if state is None:
        print("상태 파일이 없습니다: python scripts/qa_cli.py init")
        return 1

    session = state["session"]
    config = state.get("config", {})
    phases = state.get("phases", {})

    STATUS_ICON = {
        "pending": "[ ]",
        "in_progress": "[>]",
        "completed": "[v]",
        "failed": "[X]",
        "skipped": "[s]",
    }

    print(f"=== QA 자동화 상태 [{session['id']}] ===")
    print(f"전체 상태: {session['overall_status']}")
    print(f"테스트 URL: {config.get('test_url') or '미설정'}")
    precondition = config.get("precondition")
    if precondition and isinstance(precondition, dict):
        desc = precondition.get("description") or "(설명 없음)"
        n_actions = len(precondition.get("actions", []))
        n_checks = len(precondition.get("success_checks", []))
        print(f"Precondition: {desc} (actions={n_actions}, success_checks={n_checks})")
    else:
        print(f"Precondition: 없음 (선행 동작 불필요)")
    print(f"GitHub Repo: {config.get('github_repo') or '미설정'}")
    print(f"GitHub Skip: {config.get('skip_github', False)}")
    print()
    print("Phase 진행 현황:")

    for p in PHASE_ORDER:
        key = get_phase_key(p)
        ph = phases.get(key, {})
        status = ph.get("status", "pending")
        icon = STATUS_ICON.get(status, "[ ]")
        optional_mark = " (선택)" if PHASE_META[p].get("optional") else ""
        print(f"  {icon} Phase {p}: {PHASE_META[p]['name']}{optional_mark} [{status}]")

        errors = ph.get("errors", [])
        if errors:
            print(f"       오류: {errors[-1].get('message', '')[:80]}")

    print()
    return 0


def cmd_resume(args):
    """중단된 세션 재개 지점 안내."""
    state = load_state()
    if state is None:
        print("상태 파일이 없습니다.")
        print("새 세션 시작: python scripts/qa_cli.py init")
        return 1

    phases = state.get("phases", {})

    # failed Phase 먼저 확인
    for p in PHASE_ORDER:
        key = get_phase_key(p)
        if phases.get(key, {}).get("status") == "failed":
            print(f"[재개 지점] Phase {p} ({PHASE_META[p]['name']})에서 실패가 발생했습니다.")
            errors = phases[key].get("errors", [])
            if errors:
                print(f"마지막 오류: {errors[-1].get('message', '')}")
            print()
            print(f"재시작: python scripts/qa_cli.py start {p}")
            print_reminder(state, p)
            return 0

    # in_progress Phase 확인
    for p in PHASE_ORDER:
        key = get_phase_key(p)
        if phases.get(key, {}).get("status") == "in_progress":
            print(f"[재개 지점] Phase {p} ({PHASE_META[p]['name']})가 진행 중입니다.")
            print_reminder(state, p)
            return 0

    # 정상 next 흐름
    return cmd_next([])


def cmd_set(args):
    """config 값 설정."""
    if len(args) < 2:
        print("Usage: qa_cli.py set <key> <value>")
        print("  key: test_url | precondition | github_repo | skip_github")
        print()
        print("  precondition 예시 (JSON 문자열):")
        print('  python scripts/qa_cli.py set precondition \'{"description":"로그인","actions":[{"action":"click","selector":"#login"}],"success_checks":[{"action":"check","selector":".dashboard"}]}\'')
        print()
        print("  선행 동작을 제거하려면:")
        print("  python scripts/qa_cli.py set precondition none")
        return 1

    key = args[0]
    value = " ".join(args[1:])

    state = load_state()
    if state is None:
        print("ERROR: 상태 파일이 없습니다. 먼저 실행: python scripts/qa_cli.py init")
        return 1

    valid_keys = ["test_url", "github_repo", "skip_github", "precondition", "skip_precondition"]
    if key not in valid_keys:
        print(f"ERROR: 알 수 없는 키: {key}")
        print(f"유효한 키: {valid_keys}")
        return 1

    if key == "skip_precondition":
        print("[INFO] skip_precondition은 더 이상 필요하지 않습니다. precondition 미설정 시 자동으로 '선행 동작 없음'으로 처리됩니다.")
        value = value.lower() in ("true", "1", "yes")
    elif key == "skip_github":
        value = value.lower() in ("true", "1", "yes")
    elif key == "precondition":
        if value.lower() == "none":
            value = None
            state["config"][key] = value
            save_state(state)
            print(f"[SET] config.precondition = None (선행 동작 없음)")
            return 0
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError as e:
            print(f"ERROR: precondition은 유효한 JSON이어야 합니다: {e}")
            return 1
        if not isinstance(parsed, dict):
            print("ERROR: precondition은 JSON 객체여야 합니다.")
            return 1
        if not isinstance(parsed.get("actions"), list) or len(parsed["actions"]) == 0:
            print("ERROR: precondition.actions는 비어 있지 않은 배열이어야 합니다.")
            return 1
        if not isinstance(parsed.get("success_checks"), list) or len(parsed["success_checks"]) == 0:
            print("ERROR: precondition.success_checks는 비어 있지 않은 배열이어야 합니다.")
            return 1
        value = parsed

    state["config"][key] = value
    save_state(state)
    if key == "precondition":
        desc = value.get("description") or ""
        n_actions = len(value.get("actions", []))
        n_checks = len(value.get("success_checks", []))
        print(f"[SET] config.precondition = {desc!r} (actions={n_actions}, success_checks={n_checks})")
    else:
        print(f"[SET] config.{key} = {value}")
    return 0


# ============================================================
# 진입점
# ============================================================

HANDLERS = {
    "init": cmd_init,
    "start": cmd_start,
    "complete": cmd_complete,
    "fail": cmd_fail,
    "next": cmd_next,
    "status": cmd_status,
    "resume": cmd_resume,
    "set": cmd_set,
}


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    command = sys.argv[1]
    args = sys.argv[2:]

    handler = HANDLERS.get(command)
    if handler is None:
        print(f"ERROR: 알 수 없는 명령: {command}")
        print(f"유효한 명령: {list(HANDLERS.keys())}")
        sys.exit(1)

    exit_code = handler(args)
    sys.exit(exit_code or 0)


if __name__ == "__main__":
    main()
