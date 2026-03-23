#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""추출기 공통 유틸리티."""

import os
import sys

DEFAULT_REF_DIR = "outputs/reference"


def resolve_ref_dir(reference_dir):
    """reference_dir를 절대경로로 정규화하고 디렉터리를 생성한 뒤 반환."""
    ref_dir = reference_dir or DEFAULT_REF_DIR
    ref_dir = os.path.normpath(ref_dir)
    if not os.path.isabs(ref_dir):
        ref_dir = os.path.join(os.getcwd(), ref_dir)
    os.makedirs(ref_dir, exist_ok=True)
    return ref_dir


def to_rel_path(abs_path, fallback_rel):
    """abs_path를 cwd 기준 상대경로(슬래시)로 변환. 드라이브 불일치 등 실패 시 fallback_rel 반환."""
    try:
        return os.path.relpath(abs_path, os.getcwd()).replace("\\", "/")
    except ValueError:
        return fallback_rel.replace("\\", "/")


def setup_stdout_utf8():
    """stdout 인코딩을 UTF-8로 설정."""
    if sys.stdout.encoding != "utf-8":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass


def parse_reference_dir(argv):
    """sys.argv에서 --reference-dir 값을 파싱해 반환. 없으면 None."""
    args = argv[2:]
    for i, a in enumerate(args):
        if a == "--reference-dir" and i + 1 < len(args):
            return args[i + 1]
    return None
