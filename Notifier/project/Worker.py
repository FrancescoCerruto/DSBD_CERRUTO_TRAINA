import json
import threading
import smtplib
import requests
from confluent_kafka import Consumer
from .Config import Config


class Worker:

    def __init__(self, metrics):
        self.consumer = Consumer({'bootstrap.servers': Config.BROKER_KAFKA,
                                  'group.id': 'notifier',
                                  'enable.auto.commit': 'true',
                                  'auto.offset.reset': 'earliest'})
        self.consumer.subscribe([Config.ALERT_TOPIC])
        self.metrics = metrics
        self.notification_error = []
        consumer_thread = threading.Thread(target=self.receive_alert)
        consumer_thread.start()

    def receive_alert(self):
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
                    key = msg.key().decode()
                    data_kafka = json.loads(msg.value())
                    print("Consumed record with value {}".format(data_kafka))
                    # new alert
                    data_post = {
                        'email': data_kafka['email'],
                        'alert': data_kafka['alert'],
                        'crypto_name': key,
                        'delta_percentage': data_kafka['delta_percentage'],
                        'timestamp': data_kafka['timestamp']
                    }
                    try:
                        response_post = requests.post("http://localhost:5000/insert_notification_record",
                                                      data=data_post)
                        if response_post.status_code == 500:
                            self.notification_error.append(data_post)
                            self.metrics.set_error()
                    except Exception:
                        self.metrics.set_operation()
                        self.notification_error.append(data_post)

                    # send email
                    to_email = data_kafka['email']
                    subject = "update"
                    body = ""
                    if data_kafka['alert'] == "crypto update - new portfolio value":
                        body = "{}\n{} value was updated\ndelta_percentage portfolio value {}".format(
                            data_kafka['alert'], key, data_kafka['delta_percentage']
                        )
                    elif data_kafka['alert'] == "Portfolio action - new portfolio value":
                        if data_kafka['delta_percentage'] < 0:
                            body = "{}\nSell {}\ndelta_percentage portfolio value {}".format(
                                data_kafka['alert'], key, data_kafka['delta_percentage']
                            )
                        else:
                            body = "{}\nBuy {}\ndelta_percentage portfolio value {}".format(
                                data_kafka['alert'], key, data_kafka['delta_percentage']
                            )
                    else:
                        body = "{}\n{} value was updated\ndelta_percentage crypto value {}".format(
                            data_kafka['alert'], key, data_kafka['delta_percentage']
                        )

                    message = f'Subject: {subject}\n\n{body}'

                    with smtplib.SMTP(Config.SMTP_SERVER, Config.SMTP_PORT) as smtp:
                        smtp.starttls()
                        smtp.login(Config.SENDER_EMAIL, Config.APP_PASSWORD)
                        smtp.sendmail(Config.SENDER_EMAIL, to_email, message)
        except KeyboardInterrupt:
            pass
        finally:
            # Leave group and commit final offsets
            self.consumer.close()

    def retry_insert(self):
        for i in range(len(self.notification_error) - 1, -1, -1):
            print("Try to insert old record")
            try:
                response_post = requests.post("http://localhost:5000/insert_notification_record",
                                              data=self.notification_error[i])
                if response_post.status_code == 200:
                    print("Ok")
                    del self.notification_error[i]
                else:
                    self.metrics.set_error()
            except Exception:
                self.metrics.set_operation()