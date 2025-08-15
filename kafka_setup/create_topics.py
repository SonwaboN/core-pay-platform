import time
from kafka.admin import KafkaAdminClient, NewTopic
from kafka.errors import TopicAlreadyExistsError, NoBrokersAvailable

def create_kafka_topics():
    # Configuration
    bootstrap_servers = 'kafka:29092'
    topic_list = [
        NewTopic(name='raw_transactions', num_partitions=1, replication_factor=1),
        NewTopic(name='enriched_transaction', num_partitions=1, replication_factor=1),
        NewTopic(name='compliance_checked_transaction', num_partitions=1, replication_factor=1),
        NewTopic(name='fraud_scored_transaction', num_partitions=1, replication_factor=1),
        NewTopic(name='final_decision', num_partitions=1, replication_factor=1),
        NewTopic(name='simulation_outcome', num_partitions=1, replication_factor=1),
        NewTopic(name='divergence_alert', num_partitions=1, replication_factor=1)
    ]

    print("Waiting for Kafka to be available...")
    time.sleep(15) # Wait for Kafka to be ready

    for i in range(5):
        try:
            print(f"Attempting to connect to Kafka... (Attempt {i+1}/5)")
            admin_client = KafkaAdminClient(
                bootstrap_servers=bootstrap_servers,
                client_id='topic_creator',
                request_timeout_ms=5000
            )
            print("Successfully connected to Kafka.")
            break
        except NoBrokersAvailable:
            print(f"Could not connect to Kafka, retrying in 10 seconds...")
            time.sleep(10)
    else:
        print("Could not connect to Kafka after several attempts. Exiting.")
        return

    print("Creating topics...")
    try:
        admin_client.create_topics(new_topics=topic_list, validate_only=False)
        print("Topics created successfully (or already exist).")
    except TopicAlreadyExistsError:
        print("Topics already exist, no action taken.")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        admin_client.close()

if __name__ == '__main__':
    create_kafka_topics()
