---
name: extract-docx
description: Use when extracting content from Word (DOCX) files for QA test scenario generation. Triggers on DOCX analysis, document text/table/image extraction, or Phase 1 document analysis with DOCX input.
---

# DOCX 문서 추출

Word 기획서에서 텍스트, 표, 이미지를 추출하여 QA 테스트 시나리오의 원본 데이터를 생성합니다.

## 실행

```bash
# 통합 진입점 (권장)
python .cursor/skills/qa-automation/scripts/extract_document.py inputs/ --output outputs

# DOCX 직접 호출
python .cursor/skills/qa-automation/scripts/extract_docx.py inputs/spec.docx --reference-dir outputs/reference
```

## 의존성

```bash
pip install python-docx
```

## 추출 항목

| 항목 | 방식 | 비고 |
|------|------|------|
| 텍스트 | `python-docx` paragraphs | 단락별 추출 |
| 표 | `python-docx` tables | 2차원 배열로 파싱 |
| 이미지 | `zipfile`로 media/ 추출 | embedded 이미지 |

## 출력 스키마

```json
{
  "pages": [
    {
      "page_num": 1,
      "texts": ["단락 텍스트"],
      "tables": [[ ["헤더1", "헤더2"], ["값1", "값2"] ]],
      "notes": "",
      "images": [{ "path": "outputs/reference/docx_img_0.png", "description": "" }]
    }
  ],
  "reference_images": [
    { "source_page": 1, "path": "outputs/reference/docx_img_0.png" }
  ]
}
```

DOCX는 페이지 구분이 없어 전체 문서를 단일 페이지(`page_num: 1`)로 처리합니다.

## 트러블슈팅

| 증상 | 해결 |
|------|------|
| `python-docx` import 에러 | `pip install python-docx` |
| 이미지 누락 | 외부 링크 이미지는 추출 불가, embedded만 지원 |
| 표 셀 병합 깨짐 | python-docx 제한 — 수동 확인 필요 |
