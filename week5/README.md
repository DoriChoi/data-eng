# 5주차 산출물 — Spark 기반 일별 매출 데이터 마트

## 1. 개요
Spark 3.5.3 Standalone(마스터 1, 워커 2 × 2코어)과 MinIO(S3A), Apache Iceberg 1.5.2(Hadoop Catalog)를 사용해 주문·상품 데이터의 일별 매출 마트를 생성했습니다. 원천 데이터는 실습을 위해 `mart.py`에서 직접 생성하는 샘플입니다.

### 처리 흐름
1. 주문 5행·상품 3행 생성
2. `product_id` JOIN, `qty × price`로 `amount` 계산
3. `order_date`별 `daily_amount`와 `order_cnt` 집계
4. `coalesce(1)` 후 `lake.db.daily_sales_mart`에 `createOrReplace()`
5. SparkSQL로 결과 조회

## 2. 실행
WSL Ubuntu, `~/data-eng/week5`에서 Docker Compose 클러스터를 실행합니다. **GitHub 버전은 공개 저장소 안전을 위해 비밀번호를 코드에서 제거했고**, 실행 시 환경변수를 전달합니다.

```bash
docker compose up -d
docker compose cp mart.py spark-master:/tmp/mart.py

# 로컬 셸에서 실제 값을 별도로 설정하고 GitHub에 올리지 마세요.
# export MINIO_ACCESS_KEY='...'
# export MINIO_SECRET_KEY='...'

docker compose exec -e MINIO_ACCESS_KEY -e MINIO_SECRET_KEY spark-master \
  /opt/spark/bin/spark-submit \
  --master spark://spark-master:7077 \
  --conf spark.jars.ivy=/tmp/.ivy2 \
  --packages org.apache.hadoop:hadoop-aws:3.3.4,org.apache.iceberg:iceberg-spark-runtime-3.5_2.12:1.5.2 \
  /tmp/mart.py > mart.log 2>&1
status=$?
echo "종료 코드: $status"
grep '\[mart\]' mart.log
```

특정 날짜는 `/tmp/mart.py 2026-08-25`처럼 전달합니다. **날짜를 지정하면 전체 테이블이 해당 날짜만으로 교체됩니다.** 이는 실습용이며 운영 환경의 증분 저장 방식은 아닙니다.

## 3. 최종 결과 (실제 확인)

| order_date | daily_amount | order_cnt |
|---|---:|---:|
| 2026-08-24 | 113,000 | 2 |
| 2026-08-25 | 1,155,000 | 2 |
| 2026-08-26 | 46,000 | 1 |
| **합계** | **1,314,000** | **5** |

### 정상·오류·복원 검증
| 테스트 | 실제 실행 결과 |
|---|---|
| 동일 입력 2회 실행 | 두 번 모두 동일한 3행·매출액 |
| 2026-08-25 | 종료 코드 0, 원천 2행, 마트 1행, 완료 |
| 2099-01-01 | 종료 코드 1, 원천 0행, 의도한 중단 |
| 날짜 미지정으로 복원 | 종료 코드 0, 원천 5행, 마트 3행, 완료 |

`createOrReplace()`로 논리적 결과의 멱등성을 확인했습니다. 과거 Iceberg 스냅샷의 물리 파일은 남을 수 있습니다.

## 4. 파티셔닝·셔플 성능 실측 (2026-10-29)

Spark 3.5.3 / Worker 2 × 2코어 / 1,000만 행.

| 측정 항목 | 사용자 실제 측정값 |
|---|---:|
| 기본 파티션 수 | 4 |
| `repartition(8)` | 8 |
| `coalesce(2)` | 2 |
| `repartition(4)` 행 분포 | 2,500,000 × 4 |
| `coalesce(2)` 행 분포 | 5,000,000 × 2 |
| 3개 → `coalesce(2)` | 6,666,667 / 3,333,333 |
| AQE 켬 · 셔플 파티션 200 | 0.21초 |
| AQE 켬 · 셔플 파티션 8 | 0.22초 |
| AQE 끔 · 셔플 파티션 200 | 1.06초 |
| AQE 끔 · 셔플 파티션 8 | 0.19초 |
| 비교적 고른 분포 처리 | 0.72초 |
| 스큐 분포 처리 | 0.94초 |
| 스큐 Task Max / Median | 측정 기록 없음 |
| `test-narrow` Parquet 수 | 4개 |
| `test-one` Parquet 수 | 1개 |

AQE 비활성화 시 200 → 8로 셔플 파티션을 줄이자 실행 시간이 1.06 → 0.19초로 감소했습니다(해당 실행의 실측). 스큐 처리 시간은 비교 분포보다 약 31% 길었습니다. 단일 실행 측정이므로 일반적인 성능 개선율로 해석하지 않습니다.

### 실행 계획 확인
- `filter()`의 물리 계획에서 `Exchange` 없음
- `groupBy().count()`의 물리 계획에는 `Exchange hashpartitioning(..., 200)` 표시
- `coalesce(1)` 적용 후 MinIO의 파일 수 4 → 1 확인

## 5. 오류와 해결
- PySpark `>>>`에 `docker run`을 입력해 SyntaxError 발생 → WSL Ubuntu `$`에서 실행
- 기존 PySpark 셸이 Spark 코어를 점유하면 새 배치가 대기할 수 있음 → `exit()` 후 제출
- 로그가 긴 경우 `> mart.log 2>&1`로 저장하고 `grep '[mart]'`로 요약
- 원천 데이터가 0행이면 종료 코드 1로 의도한 실패를 알림

## 6. 산출물 및 회고
- `mart.py` — 실행 가능한 배치 소스(공개용 환경변수 버전)
- `README.md` — 실행법·실제 결과·성능 실측
- `execution-summary.txt` — 원본 전체 로그 대신 검증된 출력의 요약본
- `lake.db.daily_sales_mart` — 로컬 MinIO/Iceberg 저장 테이블(저장소에 직접 업로드하지 않음)

5주차에는 Spark 분산 처리(5-1), Standalone 클러스터(5-2), S3A/Iceberg 연결(5-3), DataFrame·SQL 가공(5-4), 파티셔닝·셔플·배치 데이터 마트(5-5)를 실습했습니다.

**결론:** 병렬 처리는 파티션을 늘리는 것만으로 최적화되지 않습니다. 실행 계획, 셔플, 데이터 분포, 실제 수행 시간을 함께 확인해야 합니다.
