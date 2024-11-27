import unittest
from unittest.mock import patch, MagicMock
import json
from src.kafka_consumer import KafkaMessageProcessor


class TestKafkaMessageProcessor(unittest.TestCase):
    def setUp(self):
        self.broker = 'localhost:29092'
        self.group = 'test-group'
        self.input_topics = ['test-topic']
        self.output_topic = 'output-topic'
        self.processor = KafkaMessageProcessor(
            self.broker, self.group, self.input_topics, self.output_topic, aggregation_interval=10
        )

    @patch('confluent_kafka.admin.AdminClient.list_topics')
    def test_create_topic_if_not_exists_topic_exists(self, mock_list_topics):
        processor = KafkaMessageProcessor(broker='localhost:29092', group='test-group', input_topics=['test-topic'],
                                          output_topic='output-topic')

        # Mocking the topic to be present
        mock_list_topics.return_value.topics = {'test-topic': None}

        with self.assertLogs(level='INFO') as log:
            processor.create_topic_if_not_exists('test-topic')

        self.assertIn("Topic 'test-topic' already exists.", log.output[0])



    # Test ensure_schema_consistency method

    def test_ensure_schema_consistency_all_fields_present(self):
        processor = KafkaMessageProcessor(broker='localhost:29092', group='test-group', input_topics=['test-topic'],
                                          output_topic='output-topic')

        message = {"app_version": "1.0", "ip": "127.0.0.1", "locale": "en_US"}
        result = processor.ensure_schema_consistency(message)

        self.assertEqual(result, message)

    def test_ensure_schema_consistency_missing_field(self):
        processor = KafkaMessageProcessor(broker='localhost:29092', group='test-group', input_topics=['test-topic'],
                                          output_topic='output-topic')

        message = {"app_version": "1.0", "ip": "127.0.0.1"}
        result = processor.ensure_schema_consistency(message)

        self.assertEqual(result["locale"], "")
        self.assertEqual(result["app_version"], "1.0")
        self.assertEqual(result["ip"], "127.0.0.1")

    def test_ensure_schema_consistency_empty_message(self):
        processor = KafkaMessageProcessor(broker='localhost:29092', group='test-group', input_topics=['test-topic'],
                                          output_topic='output-topic')

        message = {}
        result = processor.ensure_schema_consistency(message)

        self.assertEqual(result["app_version"], "")
        self.assertEqual(result["ip"], "")
        self.assertEqual(result["locale"], "")

    # Test consume_and_process_messages method



    @patch('src.kafka_consumer.Consumer')
    @patch('src.kafka_consumer.Producer')
    def test_consume_and_process_messages(self, MockProducer, MockConsumer):
        # Mock Consumer
        consumer_instance = MockConsumer.return_value
        mock_message = MagicMock()
        mock_message.error.return_value = None
        mock_message.value.return_value = json.dumps({
            "user_id": "test_user",
            "device_id": "device123",
            "timestamp": "2024-11-26T12:00:00Z",
            "device_type": "mobile"
        }).encode('utf-8')
        consumer_instance.poll.side_effect = [mock_message,
                                              None]  # Mock one message and then None to simulate no new messages

        # Mock Producer
        producer_instance = MockProducer.return_value

        # Run the method
        with patch('time.time', side_effect=[0, 5, 15]):  # Simulate time progression for aggregation
            try:
                self.processor.consume_and_process_messages()
            except StopIteration:
                pass  # Allow test to break the infinite loop manually

        # Assert Consumer subscribed to topics
        consumer_instance.subscribe.assert_called_once_with(self.input_topics)

        # Assert Producer produced the transformed message
        producer_instance.produce.assert_called_once()
        produced_message = producer_instance.produce.call_args[0][1]
        produced_data = json.loads(produced_message.decode('utf-8'))
        self.assertEqual(produced_data['user_id'], 'TEST_USER')
        self.assertEqual(produced_data['device_type'], 'mobile')
        self.assertIn('processed_at', produced_data)

        # Verify aggregation logic
        expected_aggregated_data = {
            'aggregated_counts': {'mobile': 1},
            'valid_records': 1,
            'skipped_records': 0
        }
        self.assertEqual(self.processor.device_counts['mobile'], 1)
        self.assertEqual(self.processor.valid_records, 1)
        self.assertEqual(self.processor.skipped_records, 0)

    @patch('src.kafka_consumer.Consumer')
    def test_handle_invalid_message(self, MockConsumer):
        # Mock Consumer with an invalid message
        consumer_instance = MockConsumer.return_value
        mock_message = MagicMock()
        mock_message.error.return_value = None
        mock_message.value.return_value = json.dumps({"invalid_field": "data"}).encode('utf-8')
        consumer_instance.poll.side_effect = [mock_message, None]

        # Run the method
        with patch('time.time', side_effect=[0, 5, 15]):
            try:
                self.processor.consume_and_process_messages()
            except StopIteration:
                pass  # Stop infinite loop manually

        # Assert invalid messages are skipped
        self.assertEqual(self.processor.skipped_records, 1)
        self.assertEqual(self.processor.valid_records, 0)



if __name__ == '__main__':
    unittest.main()
