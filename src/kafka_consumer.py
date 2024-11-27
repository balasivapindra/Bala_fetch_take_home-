import logging
from confluent_kafka import Consumer, Producer, KafkaError
from confluent_kafka.admin import AdminClient, NewTopic
import json
import time
from collections import defaultdict

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


class KafkaMessageProcessor:
    def __init__(self, broker, group, input_topics, output_topic, aggregation_interval=60):
        self.broker = broker
        self.group = group
        self.input_topics = input_topics
        self.output_topic = output_topic
        self.aggregation_interval = aggregation_interval
        self.consumer = None
        self.producer = None
        self.device_counts = defaultdict(int)
        self.valid_records = 0
        self.skipped_records = 0
        self.aggregation_start_time = time.time()
        self.required_fields = ["app_version", "ip", "locale"]

    def create_topic_if_not_exists(self, topic_name, num_partitions=1, replication_factor=1):
        """
        Ensures the Kafka topic exists, creating it if necessary.
        """
        admin_client = AdminClient({'bootstrap.servers': self.broker})
        try:
            topic_metadata = admin_client.list_topics(timeout=10)

            if topic_name not in topic_metadata.topics:
                logging.info(f"Topic '{topic_name}' does not exist. Creating it...")
                new_topic = NewTopic(topic=topic_name,
                                     num_partitions=num_partitions,
                                     replication_factor=replication_factor)
                futures = admin_client.create_topics([new_topic])

                for topic, future in futures.items():
                    try:
                        future.result()  # Wait for topic creation
                        logging.info(f"Topic '{topic}' created successfully.")
                    except Exception as e:
                        logging.error(f"Failed to create topic '{topic}': {e}")
            else:
                logging.info(f"Topic '{topic_name}' already exists.")
        except Exception as e:
            logging.error(f"Failed to create topic '{topic_name}': {e}")

    def ensure_schema_consistency(self, message_value):
        """
        Ensures all required fields are present in the message with default values if missing.
        """
        for field in self.required_fields:
            if field not in message_value:
                message_value[field] = ""  # Set missing fields to an empty string
        return message_value

    def consume_and_process_messages(self):
        """
        Consumes data from Kafka, processes it, aggregates metrics, and publishes to another topic.
        """
        # Create the output topic if it does not exist
        self.create_topic_if_not_exists(self.output_topic)

        # Consumer configuration
        consumer_conf = {
            'bootstrap.servers': self.broker,
            'group.id': self.group,
            'auto.offset.reset': 'earliest',
            "enable.auto.commit": "false"
        }

        # Producer configuration
        producer_conf = {
            'bootstrap.servers': self.broker,
        }

        self.consumer = Consumer(consumer_conf)
        self.producer = Producer(producer_conf)

        # Subscribe to input topics
        self.consumer.subscribe(self.input_topics)

        try:
            logging.info("Starting message consumption...")
            while True:
                msg = self.consumer.poll(timeout=0.1)
                if msg is None:
                    continue
                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        logging.info(f"%% {msg.topic()} [{msg.partition()}] reached end at offset {msg.offset()}")
                    else:
                        logging.error(f"Error: {msg.error()}")
                    continue

                try:
                    # Decode message
                    message_value = json.loads(msg.value().decode('utf-8'))

                    # Validate required fields
                    if 'user_id' not in message_value or 'device_id' not in message_value or 'timestamp' not in message_value:
                        logging.warning(f"Skipping invalid message: {msg.value()}")
                        self.skipped_records += 1
                        continue

                    if 'device_type' not in message_value:
                        logging.info(f"device_type is missing: {msg.value()}")
                        message_value['device_type'] = 'unknown'

                    # Aggregation: Count device types
                    device_type = message_value.get('device_type', 'unknown').lower()
                    self.device_counts[device_type] += 1

                    # Ensure schema consistency
                    message_value = self.ensure_schema_consistency(message_value)

                    # Transform and send processed message
                    message_value['processed_at'] = int(time.time())
                    message_value['user_id'] = message_value['user_id'].upper()

                    # Send processed message to Kafka topic
                    self.producer.produce(self.output_topic, json.dumps(message_value).encode('utf-8'))
                    self.consumer.commit(asynchronous=True)
                    self.valid_records += 1

                except Exception as e:
                    logging.error(f"Error processing message: {e}")
                    self.skipped_records += 1
                    continue

                # Check if the aggregation window has expired
                if time.time() - self.aggregation_start_time >= self.aggregation_interval:
                    # Print aggregated metrics
                    aggregated_data = {
                        'timestamp': int(time.time()),
                        'aggregated_counts': dict(self.device_counts),
                        'valid_records': self.valid_records,
                        'skipped_records': self.skipped_records
                    }
                    logging.info(f"Aggregated Data: {json.dumps(aggregated_data, indent=2)}")

                    # Reset state for the next window
                    self.device_counts.clear()
                    self.valid_records = 0
                    self.skipped_records = 0
                    self.aggregation_start_time = time.time()

        except KeyboardInterrupt:
            logging.info("Shutting down...")
        finally:
            self.consumer.close()


if __name__ == "__main__":
    broker = 'localhost:29092'
    group = 'advanced-consumer-group'
    input_topics = ['user-login']
    output_topic = 'processed-user-events'

    processor = KafkaMessageProcessor(broker, group, input_topics, output_topic, aggregation_interval=60)
    processor.consume_and_process_messages()
