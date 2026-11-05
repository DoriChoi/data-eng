"""Read Debezium MySQL CDC events from the Kafka topic (optional lab script)."""
import json
from confluent_kafka import Consumer

consumer = Consumer({
    "bootstrap.servers": "localhost:9092",
    "group.id": "cdc-reader",
    "auto.offset.reset": "earliest",
})
consumer.subscribe(["shop.shop.orders"])
labels = {"r": "스냅숏", "c": "INSERT", "u": "UPDATE", "d": "DELETE"}

try:
    while True:
        msg = consumer.poll(1.0)
        if msg is None:
            continue
        if msg.error():
            print(f"[Kafka 오류] {msg.error()}")
            continue
        if msg.value() is None:
            key = json.loads(msg.key().decode("utf-8")) if msg.key() else {}
            print(f"[툼스톤] key={key}")
            continue
        event = json.loads(msg.value().decode("utf-8"))
        payload = event.get("payload", event)
        print(f"[{labels.get(payload.get('op'), payload.get('op'))}] before={payload.get('before')} after={payload.get('after')}")
except KeyboardInterrupt:
    pass
finally:
    consumer.close()
