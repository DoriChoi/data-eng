# 6주차 — Kafka·Debezium CDC → MinIO 실시간 적재

2026-11-05 ICT 데이터 엔지니어링 6주차 실습 산출물. Windows + WSL2 Ubuntu 22.04, Docker Compose 환경.

## 1. 구성

| 서비스 | 역할 | 접근 포트 |
|---|---|---|
| kafka (Apache Kafka 3.7.0) | 이벤트 토픽 및 Connect 내부 저장소 | 외부 9092 / 내부 29092 |
| mysql (MySQL 8.0) | 원천 `shop.orders` DB, ROW binlog | 3306 |
| connect (Debezium Connect 2.7.3.Final) | MySQL Source + Confluent S3 Sink | 8083 |
| minio (cdc-minio) | S3 호환 오브젝트 저장소, `cdc-raw` 버킷 | API 9000 / 콘솔 9001 |

**데이터 흐름:** MySQL(binlog) → Debezium(`mysql-cdc`) → Kafka(`shop.shop.orders`) → S3 Sink(`minio-sink`) → MinIO(`cdc-raw`).

## 2. Kafka 토픽 (실제 목록 8개)

| 토픽 | 용도 |
|---|---|
| `orders` | 이전 6-3 Kafka 실습 |
| `shop.shop.orders` | Debezium CDC 주문 변경 이벤트 |
| `schema-changes.shop` | MySQL 스키마 변경 이력 |
| `shop` | Debezium 내부 스키마 이력 토픽 |
| `connect_configs` | Kafka Connect 커넥터 구성 |
| `connect_offsets` | Kafka Connect 소스 오프셋 |
| `connect_statuses` | Kafka Connect 작업 상태 |
| `__consumer_offsets` | Kafka 소비자 그룹 오프셋 |

## 3. 산출물

- [docker-compose.yml](./docker-compose.yml) — Kafka, MySQL, Connect, MinIO
- [register-mysql.json](./register-mysql.json) — Debezium MySQL Source 등록 템플릿
- [sink-minio.json](./sink-minio.json) — MinIO S3 Sink 등록 템플릿
- [cdc_reader.py](./cdc_reader.py) — CDC 이벤트 간단 출력 코드 (실행 미검증)
- [.env.example](./.env.example) — 로컬 환경 변수 예시
- [requirements.txt](./requirements.txt) — Python Consumer 의존성

**보안:** 공개 저장소의 JSON 파일은 비밀번호를 `REPLACE_...`로 대체한 **템플릿**입니다. 제출용 구조를 보존하지만 그대로는 인증되지 않습니다. 로컬 실습에서 사용한 `rootpw`, `dbz`, `minioadmin` 등 고정 비밀번호는 실서비스에서 사용하지 마세요. S3 Sink JSON의 자격증명은 실제 실행 환경에 맞게 로컬에서 교체해야 합니다. 비밀번호가 들어간 수정 파일을 Git에 커밋하지 마세요.

## 4. 실제 검증 결과

- MySQL: `log_bin=ON`, `binlog_format=ROW` 확인.
- `mysql-cdc` Connector 및 Task `RUNNING` 확인.
- CDC 이벤트 `r/c/u/d` 확인: 스냅숏, INSERT, `CREATED → PAID` UPDATE, DELETE 뒤 툼스톤(`null`).
- S3 Sink 플러그인 12.1.15 다운로드 및 JAR 파일 145개 확인.
- `cdc-raw` 버킷 생성 성공; `minio-sink` Connector/Task `RUNNING` 확인.
- `flush.size=5` 조건에서 `ROTATION TRIGGERED` 및 `FILES COMMITTED` (5 records/file) 로그 확인.
- MinIO의 `topics/shop.shop.orders/partition=0/` 아래 JSON 파일 3개 생성 및 실제 `op`/`after` 데이터 확인.
- 추가 INSERT 5건(`u1`~`u5`)이 Kafka Consumer에 실시간 도착하는 것 확인.
- 최종 점검 시 `CURRENT-OFFSET=21`, `LOG-END-OFFSET=22`, `LAG=1`. **끝의 1건이 MinIO 파일까지 저장됐는지는 추가 확인 필요**.
- `cdc_reader.py`는 작성했으나 `.venv` 및 `python` 명령 부재로 **실행 성공은 확인되지 않음**.

## 5. 재현 순서 (로컬 실습 전용)

1. `.env.example`을 복사해 `.env` 작성 후 개인 비밀번호 설정 (`.env`는 Git 제외).
2. `plugins/confluentinc-kafka-connect-s3/` 경로에 Confluent S3 Sink 12.1.15 플러그인을 압축 해제.
3. `docker compose up -d` 실행 및 `curl http://localhost:8083/connector-plugins`로 플러그인 확인.
4. MySQL의 `shop.orders` 테이블, CDC 계정 및 binlog/권한 설정 (강의 실습 단계 참조).
5. 로컬에서 두 JSON의 `REPLACE_...` 항목을 실제 인증값으로 교체한 후 `POST /connectors` 등록. **교체한 파일을 Git에 업로드하지 않기.**
6. `cdc-raw` 버킷을 먼저 만든 뒤 `minio-sink` 등록, Connector와 Task 둘 다 `RUNNING` 확인.
7. INSERT/UPDATE/DELETE 후 Kafka 메시지, Consumer 오프셋, MinIO 저장 파일과 내용을 순서대로 검증.

이 저장소는 **수업 산출물과 구조를 기록하는 템플릿**입니다. 완전 자동 초기화 스크립트가 아니며 새 환경에서 그대로 원클릭 재현된다고 주장하지 않습니다.

## 6. 남은 개선점

1. 메시지가 적을 때도 파일이 생성되도록 `rotate.interval.ms` 등 시간 기준 회전 검토.
2. Kafka Consumer LAG, Connect Task FAILED, MinIO 적재 오류 모니터링 및 알림.
3. 재처리·중복 이벤트·삭제 이벤트를 키와 변경 순서 기준으로 멱등 적재 (향후 Spark/Iceberg).
4. Python `.venv` 및 `confluent-kafka` 설치 후 `cdc_reader.py` 실행 검증.
5. 공개 저장소/운영 환경에서는 자격증명 관리, 접근 제어, 데이터 보존 기간을 강화.

## 7. 확인에 사용한 명령

```bash
docker compose ps
curl -s localhost:8083/connectors/mysql-cdc/status | python3 -m json.tool
curl -s localhost:8083/connectors/minio-sink/status | python3 -m json.tool
docker exec kafka /opt/kafka/bin/kafka-topics.sh --bootstrap-server localhost:9092 --list
docker exec kafka /opt/kafka/bin/kafka-consumer-groups.sh --bootstrap-server localhost:9092 --describe --group connect-minio-sink
docker compose logs connect | tail -n 30
```

> 실습 후 다음 수업을 위해 컨테이너 보존이 필요하면 `docker compose stop`을 사용하고, 데이터를 잃을 수 있는 무분별한 `down -v`는 피하세요.
