---
name: compare-screenshot
description: Use when comparing reference images with actual screenshots for visual regression testing. Triggers on screen comparison, image diff, visual mismatch detection, or Phase 3 compare_with_reference actions.
---

# 스크린샷 비교

참조 이미지(기획서)와 실제 스크린샷의 유사도를 perceptual hash로 비교합니다.

## 실행

```bash
# CLI
python .cursor/skills/qa-automation/scripts/compare_screenshot.py <참조> <실제> [--threshold N] [--diff-out PATH]

# 예시
python .cursor/skills/qa-automation/scripts/compare_screenshot.py \
  outputs/reference/slide_6.png outputs/screenshot_01.png --threshold 10 --diff-out outputs/diff.png
```

## 의존성

```bash
pip install Pillow imagehash
```

## 옵션

| 옵션 | 기본값 | 설명 |
|------|--------|------|
| `--threshold` | 10 | 해밍 거리 임계값 (낮을수록 엄격) |
| `--diff-out` | 없음 | 차이 맵 이미지 저장 경로 |

## 반환값 (Python API)

```python
from compare_screenshot import compare_screenshot

result = compare_screenshot("ref.png", "actual.png", threshold=10, diff_out_path="diff.png")
# {
#   "match": True/False,     # 임계값 이하면 True
#   "score": 3,              # 해밍 거리 (0=동일)
#   "threshold": 10,
#   "diff_path": "diff.png"  # 차이 맵 경로 (없으면 None)
# }
```

## 동작 방식

1. 두 이미지를 RGB로 로드
2. 해상도 불일치 시 실제 이미지를 참조 크기로 리사이즈
3. **perceptual hash** (pHash) 비교 → 해밍 거리 계산
4. `score ≤ threshold`이면 일치
5. `--diff-out` 지정 시 픽셀 차이 맵(그레이스케일) 저장

## run_all_tests.py 연동

`test_plan.json`에 `compare_with_reference` 액션이 있으면 `run_all_tests.py`가 자동 호출합니다. 수동 비교가 필요할 때만 직접 실행하세요.

## 임계값 가이드

| threshold | 용도 |
|-----------|------|
| 0~5 | 거의 동일한 이미지 확인 (엄격) |
| 5~10 | 일반적인 UI 비교 (권장) |
| 10~20 | 레이아웃 유사성 확인 (관대) |
| 20+ | 구조적 유사성만 확인 |
