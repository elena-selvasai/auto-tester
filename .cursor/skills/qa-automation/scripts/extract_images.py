#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
이미지 파일(와이어프레임/목업)을 참조 이미지로 등록. 1파일=1페이지 또는 폴더 내 이미지=페이지별 참조.
Usage: python extract_images.py <path> [--reference-dir DIR]
  path: 단일 이미지 파일 또는 이미지가 들어 있는 디렉터리
"""

import os
import shutil
import sys

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp"}


def extract_images(path, output_path=None, reference_dir=None):
    """이미지 경로를 공통 스키마로 반환. 복사는 하지 않고 경로만 참조하거나 reference_dir로 복사."""
    if not os.path.exists(path):
        print(f"Error: 파일을 찾을 수 없습니다 - {path}")
        return None

    ref_dir = reference_dir or "outputs/reference"
    ref_dir = os.path.normpath(ref_dir)
    if not os.path.isabs(ref_dir):
        ref_dir = os.path.join(os.getcwd(), ref_dir)
    os.makedirs(ref_dir, exist_ok=True)

    files = []
    if os.path.isfile(path):
        ext = os.path.splitext(path)[1].lower()
        if ext in IMAGE_EXTENSIONS:
            files.append((1, path))
    elif os.path.isdir(path):
        for i, name in enumerate(sorted(os.listdir(path)), 1):
            ext = os.path.splitext(name)[1].lower()
            if ext in IMAGE_EXTENSIONS:
                files.append((i, os.path.join(path, name)))

    if not files:
        print("Error: 이미지 파일이 없습니다.")
        return None

    pages_out = []
    reference_images = []
    for page_num, abs_src in files:
        name = os.path.basename(abs_src)
        rel_dest = os.path.join(ref_dir, f"ref_page_{page_num}_{name}")
        try:
            shutil.copy2(abs_src, rel_dest)
        except Exception as e:
            print(f"Warning: 복사 실패 {abs_src} - {e}")
            rel_dest = abs_src
        try:
            rel_path = os.path.relpath(rel_dest, os.getcwd()).replace("\\", "/")
        except ValueError:
            rel_path = os.path.join("outputs", "reference", f"ref_page_{page_num}_{name}").replace("\\", "/")
        pages_out.append({
            "page_num": page_num,
            "texts": [],
            "tables": [],
            "notes": "",
            "images": [{"path": rel_path, "description": name}],
        })
        reference_images.append({"source_page": page_num, "path": rel_path})

    result = {"pages": pages_out, "reference_images": reference_images}

    print(f"=== 이미지 참조 등록 ===\n")
    for p in pages_out:
        print(f"--- 페이지 {p['page_num']} ---")
        for im in p["images"]:
            print(f"  {im['path']}")
    print()

    return result


def main():
    if len(sys.argv) < 2:
        print("Usage: python extract_images.py <path> [--reference-dir DIR]")
        sys.exit(1)
    path = sys.argv[1]
    ref_dir = None
    for i, a in enumerate(sys.argv[2:], 2):
        if a == "--reference-dir" and i < len(sys.argv) - 1:
            ref_dir = sys.argv[i]
            break
    if sys.stdout.encoding != "utf-8":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass
    r = extract_images(path, reference_dir=ref_dir)
    sys.exit(0 if r is not None else 1)


if __name__ == "__main__":
    main()
