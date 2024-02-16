import threading
from datetime import datetime
import json
from confluent_kafka import Consumer, Producer
from project.database import create_portfolio_action, retrieve_purchase_list, \
    retrieve_all_user
from project.Config import Config
from project.QoSMetrics import QoSMetrics


class Worker:
    def __init__(self):
        self.metrics = QoSMetrics()
        self.purchase_on_fly = []

        self.producer = Producer({'bootstrap.servers': Config.BROKER_KAFKA,
                                  'retries': 10,
                                  'max.in.flight.requests.per.connection': 1})

        self.consumer = Consumer({'bootstrap.servers': Config.BROKER_KAFKA,
                                  'group.id': 'portfolio_tracker',
                                  'enable.auto.commit': 'true',
                                  'auto.offset.reset': 'earliest'})
        self.consumer.subscribe([Config.CRYPTO_UPDATE_TOPIC, Config.PURCHASE_UPDATE_TOPIC])
        # start thread
        self.kafka_thread = threading.Thread(target=self.kafka_consumer())
        self.kafka_thread.start()

    def send_message(self, value, topic, key):
        try:
            print("Producing record: {}\t{}".format(key, value))
            self.producer.produce(topic=topic, key=key, value=value)
        except BufferError:
            print('%% Local producer queue is full (%d messages awaiting delivery): try again\n' % len(self.producer))
        # Wait until all messages have been delivered
        print('%% Waiting for %d deliveries\n' % len(self.producer))
        self.producer.flush()

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
                    print("Consumed record with value {}".format(json.loads(msg.value())))
                    # issue metrics
                    self.metrics.set_operation()

                    # from which topic?
                    if msg.topic() == Config.PURCHASE_UPDATE_TOPIC:
                        # only send buy/sell alert
                        # (crypto, {email, quantity, crypto_value})
                        key = msg.key()
                        data_kafka = json.loads(msg.value())
                        email = data_kafka['email']
                        quantity = data_kafka['quantity']
                        crypto_value = data_kafka['crypto_value']

                        # calculate old_value portfolio
                        purchase_list = retrieve_purchase_list(email)

                        if purchase_list == -1:
                            # end of work - consider only purchase not stored decrease portfolio_value
                            # issue metrics
                            self.metrics.set_error()()
                            # if database is not reachable insert of record fail
                            self.purchase_on_fly.append({
                                'email': email,
                                'crypto_name': key.decode(),
                                'crypto_value': crypto_value,
                                'quantity': quantity})
                        else:
                            old_value = 0.0
                            for instance in purchase_list:
                                old_value = old_value + instance['crypto_value'] * float(instance['quantity'])
                            new_value = old_value + float(quantity) * crypto_value
                            delta_percentage = 0.0
                            if old_value == 0.0:
                                delta_percentage = 100.0
                            else:
                                delta_percentage = ((float(new_value) - float(old_value)) / float(old_value)) * 100.0
                            # send alert
                            data_kafka = {
                                'email': email,
                                'alert': "Portfolio action - new portfolio value",
                                'delta_percentage': delta_percentage,
                                'timestamp': datetime.strftime(datetime.utcnow(), "%Y-%m-%d %H:%M:%S")
                            }
                            start_kafka_time = datetime.utcnow()
                            self.send_message(key=key, value=json.dumps(data_kafka), topic=Config.ALERT_TOPIC)
                            self.metrics.set_kafka(start_kafka_time)

                            # insert portfolio action
                            result = create_portfolio_action(email, key.decode(), crypto_value, quantity)
                            if result == -1:
                                self.purchase_on_fly.append({
                                    'email': email,
                                    'crypto_name': key.decode(),
                                    'crypto_value': crypto_value,
                                    'quantity': quantity})
                                # issue metrics
                                self.metrics.set_error()
                    else:
                        # (crypto_name, {crypto_value})
                        # calculate new value portfolio for each user
                        data_kafka = json.loads(msg.value())
                        crypto_name = msg.key()
                        crypto_value = data_kafka['crypto_value']

                        # process
                        # retrive user who bought this crypto
                        all_user = retrieve_all_user(crypto_name.decode())

                        if all_user == -1:
                            # end of work - consider only purchase not stored decrease portfolio_value
                            # issue metrics
                            self.metrics.set_error()
                        else:
                            for email in all_user:
                                # for each user
                                # calculate old_value and new_value portfolio
                                purchase_list = retrieve_purchase_list(email)

                                if purchase_list == -1:
                                    # issue metrics
                                    self.metrics.set_error()
                                else:
                                    old_value = 0.0  # quantity * crypto_price in db
                                    new_value = 0.0  # quantity * crypto_price in db if crypto_name isn't ket of message
                                    for instance in purchase_list:
                                        if instance['crypto_name'] == crypto_name.decode():
                                            new_value = new_value + crypto_value * float(instance['quantity'])
                                        else:
                                            new_value = new_value + instance['crypto_value'] * float(
                                                instance['quantity'])
                                        old_value = old_value + instance['crypto_value'] * instance['quantity']

                                    # kafka send
                                    data_kafka = {
                                        'email': email,
                                        'alert': "crypto update - new portfolio value",
                                        'delta_percentage': ((float(new_value) - float(old_value)) / float(
                                            old_value)) * 100.0,
                                        'timestamp': datetime.strftime(datetime.utcnow(), "%Y-%m-%d %H:%M:%S")
                                    }
                                    start_kafka_time = datetime.utcnow()
                                    self.send_message(key=crypto_name, value=json.dumps(data_kafka),
                                                      topic=Config.ALERT_TOPIC)
                                    # issue metrics
                                    self.metrics.set_kafka(start_kafka_time)
        except KeyboardInterrupt:
            pass
        finally:
            # Leave group and commit final offsets
            self.consumer.close()

    def retry_insert(self):
        for i in range(len(self.purchase_on_fly) - 1, -1, -1):
            print("Try insert old record")
            # issue metrics
            self.metrics.set_operation()
            # insert portfolio action
            retry_result = create_portfolio_action(self.purchase_on_fly[i]['email'],
                                                   self.purchase_on_fly[i]['crypto_name'],
                                                   self.purchase_on_fly[i]['crypto_value'],
                                                   self.purchase_on_fly[i]['quantity'])
            if retry_result == 0:
                print("Ok")
                del self.purchase_on_fly[i]
            else:
                # issue metrics
                self.metrics.set_error()


if __name__ == '__main__':
    Worker()
