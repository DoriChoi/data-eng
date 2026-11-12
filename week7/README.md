# 7주차 · RAG / Hybrid Search

MinIO 원본 문서를 청킹하고 OpenAI 임베딩으로 변환하여 Qdrant에 적재한 뒤, BM25 키워드 검색과 벡터 검색을 RRF로 결합하는 수업입니다.

## 제출 산출물

- [vector-schema.yaml](./vector-schema.yaml): `lecture_kb`, `text-embedding-3-small`, 1536차원, Cosine, 메타데이터 및 안정적인 ID 규칙
- [build_kb.py](./build_kb.py): MinIO 텍스트 → 청킹 → 임베딩 → Qdrant, 문서별 재적재와 동일 ID로 중복 방지
- [check_schema.py](./check_schema.py): 정의서와 실제 Qdrant/임베딩 차원 대조

## 실습에서 검증한 결과 (2026-11-12)

- Qdrant `lecture_kb`: 10개 조각 (guide 1, long_notes 6, notes 3)
- `python check_schema.py`: `정의서와 실제 일치 — 1536 Cosine`
- `python build_kb.py` 연속 두 번: 모두 `적재 10 조각 · 총 10`
- 청킹 크기 200 / 별도 컬렉션 테스트: 14개
- `rank-bm25==0.2.2` 사용, BM25/벡터 비교 및 RRF 검증
- RAG 질문 실험: Airflow 답변과 지식베이스 밖 질문에서 '모릅니다.' 확인, ERR-4021 출처 표시

## 재현

```bash
cd ~/data-eng/week7
source .venv/bin/activate
docker start qdrant rag-minio
python check_schema.py
python build_kb.py
python build_kb.py
```

**중요:** `build_kb.py`는 현재 컬렉션의 문서별 기존 조각을 삭제한 뒤 다시 적재합니다. 정상 환경에서만 실행하세요. `rag_env.py`, `minio_env.py`, `.env`는 로컬 환경에 이미 있어야 하며, 인증정보가 담길 수 있으므로 이 공개 저장소에는 포함하지 않았습니다.

제출할 때는 실행 캡처를 별도로 첨부합니다. GitHub에 비밀키, `.env`, `.venv`, 데이터베이스 파일을 올리지 않습니다.
