#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
참조 이미지(기획서)와 실제 스크린샷 유사도 비교. 테스트 단계에서 화면 비교/구성 체크에 사용.
Usage: python compare_screenshot.py <reference_image> <actual_screenshot> [--threshold N] [--diff-out PATH]
"""

import os
import sys


def compare_screenshot(reference_path, actual_path, threshold=10, diff_out_path=None):
    """
    참조 이미지와 실제 스크린샷을 비교.
    Returns: dict with match (bool), score (int, 해밍 거리), diff_path (str or None)
    """
    try:
        from PIL import Image, ImageChops
        import imagehash
    except ImportError as e:
        print("Error: Pillow, imagehash 라이브러리가 필요합니다.")
        print("설치: pip install Pillow imagehash")
        return None

    if not os.path.exists(reference_path):
        print(f"Error: 참조 이미지를 찾을 수 없습니다 - {reference_path}")
        return None
    if not os.path.exists(actual_path):
        print(f"Error: 실제 스크린샷을 찾을 수 없습니다 - {actual_path}")
        return None

    try:
        ref_img = Image.open(reference_path).convert("RGB")
        act_img = Image.open(actual_path).convert("RGB")
    except Exception as e:
        print(f"Error: 이미지 로드 실패 - {e}")
        return None

    # 해상도 맞춤: 실제 스크린샷을 참조와 같은 크기로 리사이즈 후 비교
    if ref_img.size != act_img.size:
        act_img = act_img.resize(ref_img.size, Image.Resampling.LANCZOS)

    hash_ref = imagehash.phash(ref_img)
    hash_act = imagehash.phash(act_img)
    score = hash_ref - hash_act
    match = score <= threshold

    diff_path = None
    if diff_out_path:
        try:
            diff = ImageChops.difference(ref_img, act_img)
            diff = diff.convert("L")
            diff.save(diff_out_path)
            diff_path = diff_out_path
        except Exception:
            pass

    return {"match": bool(match), "score": int(score), "threshold": threshold, "diff_path": diff_path}


def main():
    if len(sys.argv) < 3:
        print("Usage: python compare_screenshot.py <reference_image> <actual_screenshot> [--threshold N] [--diff-out PATH]")
        print("Example: python compare_screenshot.py outputs/reference/slide_6.png outputs/screenshot_01_initial.png --threshold 10")
        sys.exit(1)

    reference_path = sys.argv[1]
    actual_path = sys.argv[2]
    threshold = 10
    diff_out_path = None
    i = 3
    while i < len(sys.argv):
        if sys.argv[i] == "--threshold" and i + 1 < len(sys.argv):
            threshold = int(sys.argv[i + 1])
            i += 2
            continue
        if sys.argv[i] == "--diff-out" and i + 1 < len(sys.argv):
            diff_out_path = sys.argv[i + 1]
            i += 2
            continue
        i += 1

    result = compare_screenshot(reference_path, actual_path, threshold=threshold, diff_out_path=diff_out_path)
    if result is None:
        sys.exit(1)

    print(f"비교 결과: {'일치' if result['match'] else '불일치'} (해밍 거리={result['score']}, 임계값={result['threshold']})")
    if result.get("diff_path"):
        print(f"차이 맵: {result['diff_path']}")
    sys.exit(0 if result["match"] else 1)


if __name__ == "__main__":
    main()
