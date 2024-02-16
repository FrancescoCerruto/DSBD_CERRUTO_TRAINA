from confluent_kafka import Producer
from . import Config

# Create Producer instance
p = Producer({'bootstrap.servers': Config.BROKER_KAFKA,
              'retries': 10,
              'max.in.flight.requests.per.connection': 1}
             )


def send_message(value, topic, key):
    try:
        print("Producing record: {}\t{}".format(key, value))
        p.produce(topic=topic, key=key, value=value)
    except BufferError:
        print('%% Local producer queue is full (%d messages awaiting delivery): try again\n' % len(p))
    # Wait until all messages have been delivered
    print('%% Waiting for %d deliveries\n' % len(p))
    p.flush()
