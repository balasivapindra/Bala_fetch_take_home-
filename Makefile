# Run the Kafka consumer script (depends on Docker Compose being up)
.PHONY: kafka-consumer
kafka-consumer: docker
	poetry run python3 src/kafka_consumer.py

# Run Docker Compose
.PHONY: docker
docker:
	docker-compose up -d
