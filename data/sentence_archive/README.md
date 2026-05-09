# 문장 데이터 보관 (레거시 참고용)

이 폴더의 JSON은 **제품 리포트(PDF)·`analyze_full()` 응답·API 노출 문장으로 사용하지 않습니다.**  
보관·도구·테스트·문서 생성용으로만 둡니다.

| 파일 | 참고 |
|------|------|
| `sentences_v2.json` | `engine/sentences_v2_engine.py`의 `build_v2_sentences` / `attach_v2_sentences`는 스크립트·로컬 테스트 등에서만 호출합니다. 제품 파이프라인에서는 부착하지 않습니다. |
| `sentence_db.json` | `scripts/test_sentence_structure.py` 등 구조 검증용. |

- 경로를 바꿀 때는 위 스크립트·엔진의 경로 상수를 함께 수정하세요.
- `data/sentences_v2_reader.md`는 `scripts/export_sentences_v2_to_markdown.py`로 이 JSON에서 만든 동반 문서입니다(`data/`에 둠).
