# ICT 데이터 엔지니어링 160H

수도권 ICT 이노베이션스퀘어 데이터 엔지니어링 실습 기록입니다. 주차별 코드, 실습 결과 및 아키텍처를 정리합니다.

| 주차 | 주요 학습 내용 | 자료 |
|---|---|---|
| 3주차 | Pandas, DuckDB, 데이터 정제·품질 검증 | [week3](./week3/) |
| 4주차 | MinIO, Apache Iceberg, REST Catalog, Spark, Trino 레이크하우스 | [week4](./week4/) |
| 5주차 | Spark Standalone, 파티셔닝·셔플, Iceberg 데이터 마트 | [week5](./week5/) |
| 6주차 | Kafka, Debezium CDC, S3 Sink, MinIO 실시간 적재 | [week6](./week6/) |

## 4주차 주요 산출물

- [레이크하우스 아키텍처와 실습 검증](./week4/lakehouse_architecture.md) — Mermaid 다이어그램 포함
- [Trino SQL 스크립트](./week4/scripts/lakehouse_queries.sql) — 테이블 조회, 고객·채널별 집계, 스냅샷 검사

> 기존 3주차 저장소는 별도로 보존했습니다. `orders_clean.parquet`와 독립 PNG 다이어그램은 통합 저장소에 아직 복사되지 않았습니다.

## 5주차 주요 산출물

- [PySpark 배치 코드](./week5/mart.py) — 환경변수로 MinIO 접속 정보 설정
- [실습 README·실측 결과](./week5/README.md) — AQE, 셔플, 스큐, 파일 수, 멱등성
- [배치 검증 요약](./week5/execution-summary.txt) — 성공/실패/복원 결과

## 6주차 주요 산출물

- [CDC → Kafka → MinIO 실습 README](./week6/README.md) — 전체 흐름, 실제 검증 결과, 남은 개선점
- [Docker Compose 구성](./week6/docker-compose.yml) — Kafka·MySQL·Debezium·MinIO
- [Debezium Source 커넥터](./week6/register-mysql.json) / [S3 Sink 커넥터](./week6/sink-minio.json) — 공개용 인증정보 대체 템플릿
