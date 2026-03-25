---
name: extract-pptx
description: Use when extracting content from PowerPoint (PPTX) files for QA test scenario generation. Triggers on PPTX analysis, slide extraction, image/table/text extraction from presentations, or Phase 1 document analysis with PPTX input.
---

# PPTX 문서 추출

PPTX 기획서에서 텍스트, 표, 노트, 이미지를 추출하여 QA 테스트 시나리오의 원본 데이터를 생성합니다.

## 실행

```bash
# 통합 진입점 (권장 — 확장자 자동 감지)
python .cursor/skills/qa-automation/scripts/extract_document.py inputs/ --output outputs

# PPTX 직접 호출
python .cursor/skills/qa-automation/scripts/extract_pptx.py inputs/spec.pptx --reference-dir outputs/reference
```

## 의존성

```bash
pip install markitdown python-pptx
```

- `markitdown`: 텍스트·표 추출 (실패 시 python-pptx fallback 자동 적용)
- `python-pptx`: 이미지·노트·직접 텍스트 추출

## 추출 항목

| 항목 | 소스 | 비고 |
|------|------|------|
| 텍스트 | markitdown → python-pptx fallback | 마크다운 마커 자동 정리 |
| 표 | markitdown | 2차원 배열로 파싱 |
| 노트 | python-pptx notes_text_frame | 슬라이드 발표자 노트 |
| 이미지 | python-pptx (재귀 탐색) | 그룹 셰이프 내부 포함 |
| Alt text | python-pptx cNvPr.descr | 이미지 설명 |

## 출력 스키마

```json
{
  "slides": [
    {
      "page_num": 1,
      "texts": ["제목", "본문 텍스트"],
      "tables": [[ ["헤더1", "헤더2"], ["값1", "값2"] ]],
      "notes": "발표자 노트 내용",
      "images": [
        { "path": "outputs/reference/slide_1_img_0.png", "description": "alt text" }
      ]
    }
  ],
  "reference_images": [
    { "source_page": 1, "path": "outputs/reference/slide_1_img_0.png" }
  ]
}
```

`extract_document.py` 경유 시 `slides` → `pages`로 정규화되어 `outputs/extract_result.json`에 저장됩니다.

## 산출물

| 파일 | 설명 |
|------|------|
| `outputs/extract_result.json` | 공통 스키마 JSON (extract_document.py 경유 시) |
| `outputs/scenario_draft_source.md` | 마크다운 요약 + 구성 체크 리스트 |
| `outputs/reference/slide_N_img_M.png` | 참조 이미지 (화면 비교용) |

## 핵심 동작

1. **markitdown fallback**: markitdown 변환 실패 시 python-pptx `text_frame`에서 직접 텍스트 추출
2. **그룹 셰이프 재귀**: `MSO_SHAPE_TYPE.GROUP` 내부의 이미지까지 탐색
3. **이미지 중복 제거**: MD5 해시로 동일 이미지 감지, 경로 재사용
4. **슬라이드별 에러 격리**: 한 슬라이드 실패가 전체 추출을 중단하지 않음

## 후속 단계

추출 완료 후 Phase 2로 진행:
```bash
python scripts/qa_cli.py complete 1
python scripts/qa_cli.py start 2
python scripts/generate_test_skeleton.py --output-dir outputs
```

## 트러블슈팅

| 증상 | 원인 | 해결 |
|------|------|------|
| 텍스트 빈 슬라이드 | markitdown 파싱 실패 | 자동 fallback 적용됨 (로그 확인) |
| 이미지 누락 | 그룹 셰이프 내부 | v2에서 재귀 탐색으로 해결됨 |
| `markitdown` import 에러 | 미설치 | `pip install markitdown` |
| 한글 깨짐 | stdout 인코딩 | 스크립트가 UTF-8 자동 설정 |
| 동일 이미지 중복 | 여러 슬라이드에 같은 이미지 | MD5 해시로 자동 중복 제거 |
