import threading
from datetime import datetime
import json
from confluent_kafka import Consumer, Producer
from project.database import create_subscription, delete_subscription_user, retrieve_info_subscription_crypto
from project.Config import Config
from project.QoSMetrics import QoSMetrics


class Worker:
    def __init__(self):
        self.metrics = QoSMetrics()
        self.subscription_on_fly = []
        self.unsubscription_on_fly = []

        self.producer = Producer({'bootstrap.servers': Config.BROKER_KAFKA,
                                  'retries': 10,
                                  'max.in.flight.requests.per.connection': 1})

        self.consumer = Consumer({'bootstrap.servers': Config.BROKER_KAFKA,
                                  'group.id': 'subscription_tracker',
                                  'enable.auto.commit': 'true',
                                  'auto.offset.reset': 'earliest'})
        self.consumer.subscribe([Config.CRYPTO_UPDATE_TOPIC, Config.SUBSCRIPTION_UPDATE_TOPIC])
        # start thread
        self.kafka_thread = threading.Thread(target=self.kafka_consumer())
        self.kafka_thread.start()

    def retry_insert(self):
        for i in range(len(self.subscription_on_fly) - 1, -1, -1):
            print("Try insert old record subscription")
            # issue metrics
            self.metrics.set_operation()
            # insert subscription
            retry_result = create_subscription(self.subscription_on_fly[i]['email'],
                                               self.subscription_on_fly[i]['crypto_name'],
                                               self.subscription_on_fly[i]['crypto_value'],
                                               self.subscription_on_fly[i]['rule'])
            if retry_result == 0:
                print("Ok")
                del self.subscription_on_fly[i]
            else:
                # issue metrics
                self.metrics.set_error()
        for i in range(len(self.unsubscription_on_fly) - 1, -1, -1):
            print("Try delete old record unsubscribe")
            # issue metrics
            self.metrics.set_operation()
            # insert subscription
            retry_result = delete_subscription_user(self.unsubscription_on_fly[i]['email'],
                                                    self.unsubscription_on_fly[i]['crypto_name'],
                                                    self.unsubscription_on_fly[i]['rule'])
            if retry_result == 0:
                print("Ok")
                del self.unsubscription_on_fly[i]
            else:
                # issue metrics
                self.metrics.set_error()

    def send_message(self, email, delta_percentage, key, topic):
        data_kafka = {
            'email': email,
            'alert': "crypto update - subscription alert",
            'delta_percentage': delta_percentage,
            'timestamp': datetime.strftime(datetime.utcnow(), "%Y-%m-%d %H:%M:%S")
        }
        start_kafka_time = datetime.utcnow()
        try:
            print("Producing record: {}\t{}".format(key, data_kafka))
            self.producer.produce(topic=topic, key=key, value=json.dumps(data_kafka))
        except BufferError:
            print('%% Local producer queue is full (%d messages awaiting delivery): try again\n' % len(self.producer))
        # Wait until all messages have been delivered
        print('%% Waiting for %d deliveries\n' % len(self.producer))
        self.producer.flush()
        self.metrics.set_kafka(start_kafka_time)

    def evaluate_subscription(self, subscription, crypto_value, crypto_name):
        for element in subscription:
            # for each user
            # (email, rule, crypto_value)
            delta_percentage = ((crypto_value - element[2]) / element[2]) * 100.0
            if element[1] > 0:
                # c'è stato un aumento
                if delta_percentage >= float(element[1]):
                    self.send_message(key=crypto_name, email=element[0], delta_percentage=delta_percentage, topic=Config.ALERT_TOPIC)
            elif element[1] < 0:
                # c'è stata un decremento
                if delta_percentage <= float(element[1]):
                    self.send_message(key=crypto_name, email=element[0], delta_percentage=delta_percentage, topic=Config.ALERT_TOPIC)
            else:
                self.send_message(key=crypto_name, email=element[0], delta_percentage=delta_percentage,
                                  topic=Config.ALERT_TOPIC)

    def kafka_consumer(self):
        try:
            while True:
                self.retry_insert()
                # poll ogni 5s
                msg = self.consumer.poll(timeout=5.0)

                if msg is None:
                    # No message available within timeout.
                    # Initial message consumption may take up to
                    # `session.timeout.ms` for the consumer group to
                    # rebalance and start consuming
                    continue
                elif msg.error():
                    print('error: {}'.format(msg.error()))
                else:
                    # issue metrics
                    self.metrics.set_operation()
                    print("Consumed record with value {}".format(json.loads(msg.value())))
                    # from which topic?
                    if msg.topic() == Config.SUBSCRIPTION_UPDATE_TOPIC:
                        # only store subscribe/unsubscribe record
                        # (crypto, {action, email, rule, crypto_value})
                        key = msg.key()
                        data_kafka = json.loads(msg.value())
                        email = data_kafka['email']
                        action = data_kafka['action']
                        rule = data_kafka['rule']
                        crypto_value = data_kafka['crypto_value']

                        if action == "subscribe":
                            result = create_subscription(email, key.decode(), crypto_value, rule)
                            if result == -1:
                                self.subscription_on_fly.append({
                                    'email': email,
                                    'crypto_name': key.decode(),
                                    'crypto_value': crypto_value,
                                    'rule': rule})
                                # issue metrics
                                self.metrics.set_error()
                        else:
                            # delete record
                            result = delete_subscription_user(email, key.decode(), rule)
                            if result == -1:
                                self.unsubscription_on_fly.append({
                                    'email': email,
                                    'crypto_name': key.decode(),
                                    'rule': rule})
                                # issue metrics
                                self.metrics.set_error()
                    else:
                        # (crypto, {crypto_value})
                        # check rule for each user
                        data_kafka = json.loads(msg.value())
                        key = msg.key()
                        crypto_value = data_kafka['crypto_value']

                        # process
                        # retrive data from db who subscribed to this crypto
                        subscription_info = retrieve_info_subscription_crypto(key.decode())
                        if subscription_info == -1:
                            # issue metrics
                            self.metrics.set_error()
                        else:
                            if subscription_info is not None:
                                # add record
                                self.evaluate_subscription(subscription_info, crypto_value, key)
        except KeyboardInterrupt:
            pass
        finally:
            # Leave group and commit final offsets
            self.consumer.close()


if __name__ == '__main__':
    Worker()
