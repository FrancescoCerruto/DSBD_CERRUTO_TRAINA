from datetime import datetime
from prometheus_client import start_http_server, Counter, Gauge
from .Config import Config


class QoSMetrics:
    def __init__(self):
        start_http_server(Config.PROMETHEUS_PORT)

        self.error = Counter(Config.ERROR_METRICS, 'Number of times operation fails', [Config.LABEL])
        self.operation = Counter(Config.OPERATION_METRICS, 'Number of request to microservice', [Config.LABEL])
        self.kafka = Gauge(Config.KAFKA_METRICS, "Time elapsed between publish and ack kafka message", [Config.LABEL])
        self.rate = Gauge(Config.ERROR_RATE, "Error rate", [Config.LABEL])

        self.local_error = 0.0
        self.local_operation = 0.0

    def set_error(self):
        print("Issue error")
        self.error.labels(Config.LABEL).inc()
        self.local_error = self.local_error + 1.0
        self.set_rate(self.local_error / self.local_operation)

    def set_operation(self):
        print("Issue number of request")
        self.operation.labels(Config.LABEL).inc()
        self.local_operation = self.local_operation + 1.0
        self.set_rate(self.local_error / self.local_operation)

    def set_kafka(self, start_time):
        print("Issue kafka")
        elapsed_time = datetime.utcnow() - start_time
        if elapsed_time.seconds > 0:
            self.kafka.labels(Config.LABEL).set(elapsed_time.seconds)
        else:
            # time unit seconds
            self.kafka.labels(Config.LABEL).set(elapsed_time.microseconds / 1000000)

    def set_rate(self, rate):
        print("Issue rate")
        self.rate.labels(Config.LABEL).set(rate)
