import json
import threading
import requests
from datetime import datetime, timedelta
from confluent_kafka import Producer
from .Config import Config


class Worker:

    def __init__(self, metrics):
        self.producer = Producer({'bootstrap.servers': Config.BROKER_KAFKA,
                                  'retries': 10,
                                  'max.in.flight.requests.per.connection': 1})
        self.metrics = metrics
        self.crypto_error = []
        thread = threading.Thread(target=self.produce_crypto)
        thread.start()

    def send_message(self, value, topic, key):
        try:
            print("Producing record: {}\t{}".format(key, value))
            self.producer.produce(topic=topic, key=key, value=value)
        except BufferError:
            print('%% Local producer queue is full (%d messages awaiting delivery): try again\n' % len(self.producer))
        # Wait until all messages have been delivered
        print('%% Waiting for %d deliveries\n' % len(self.producer))
        self.producer.flush()

    def produce_crypto(self):
        last_update = datetime.utcnow() - timedelta(minutes=Config.UPDATE_TIME_MINUTE)
        while True:
            self.retry_insert()
            update = False
            update_time = datetime.utcnow()
            if ((last_update + timedelta(minutes=Config.UPDATE_TIME_MINUTE)) - update_time).total_seconds() <= 0:
                update = True
            if update is True:
                # retrieve data from api
                json_response = requests.get(
                    "https://api.coingecko.com/api/v3/coins/markets"
                    "?vs_currency=eur&ids=bitcoin%2C%20ethereum%2C%20tether%2C%20binancecoin%2C%20solana"
                    "%2C%20ripple%2C%20usd-coin%2C%20staked-ether%2C%20cardano%2C%20avalanche-2%2C"
                    "%20dogecoin&order=market_cap_desc&per_page=100&page=1&sparkline=false&"
                    "precision=3&locale=it"
                )
                if json_response.status_code == 429:
                    print("Error - Rate limit exceeded")
                else:
                    data_api = json.loads(json_response.content)
                    for crypto in data_api:
                        data_post = {'name': crypto['name'], 'value': crypto['current_price'], 'timestamp': datetime.strftime(update_time, "%Y-%m-%d %H:%M:%S")}
                        try:
                            response_post = requests.post("http://localhost:5000/insert_crypto_record", data=data_post)
                            if response_post.status_code == 500:
                                # issue crypto error
                                self.metrics.set_error()
                                self.crypto_error.append(data_post)
                        except requests.exceptions.RequestException as e:
                            # issue crypto error
                            self.metrics.set_error()
                            self.crypto_error.append(data_post)
                        finally:
                            kafka_start_time = datetime.utcnow()
                            data_kafka = {
                                'crypto_value': crypto['current_price']
                            }
                            self.send_message(key=crypto['name'], value=json.dumps(data_kafka),
                                              topic=Config.CRYPTO_UPDATE_TOPIC)
                            # issue crypto error
                            self.metrics.set_kafka(kafka_start_time)
                last_update = update_time

    def retry_insert(self):
        # try to insert old record
        for i in range(len(self.crypto_error) - 1, -1, -1):
            print("Try to insert old record")
            try:
                response_post = requests.post("http://localhost:5000/insert_crypto_record",
                                              data=self.crypto_error[i])
                if response_post.status_code == 200:
                    print("Ok")
                    del self.crypto_error[i]
                else:
                    # issue crypto error
                    self.metrics.set_error()
            except requests.exceptions.RequestException:
                # issue crypto error
                self.metrics.set_operation()