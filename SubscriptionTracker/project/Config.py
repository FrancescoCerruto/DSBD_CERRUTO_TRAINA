import os


class Config(object):
    # URI SQL
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:{}@{}/{}'.format(
        os.getenv('MYSQL_ROOT_PASSWORD'),
        os.getenv('MYSQL_HOST'),
        os.getenv('MYSQL_DATABASE')
    )

    # KAFKA ENVIRONMENT
    # AS CONSUMER
    CRYPTO_UPDATE_TOPIC = os.getenv('CRYPTO_UPDATE_TOPIC')
    SUBSCRIPTION_UPDATE_TOPIC = os.getenv('SUBSCRIPTION_UPDATE_TOPIC')
    # AS PRODUCER
    ALERT_TOPIC = os.getenv('ALERT_TOPIC')
    BROKER_KAFKA = os.getenv('BROKER_KAFKA')

    # PROMETHEUS ENVIRONMNET
    PROMETHEUS_PORT = int(os.getenv('PROMETHEUS_PORT'))
    ERROR_METRICS = os.getenv('ERROR_METRICS')
    KAFKA_METRICS = os.getenv('KAFKA_METRICS')
    OPERATION_METRICS = os.getenv('OPERATION_METRICS')
    ERROR_RATE = os.getenv('ERROR_RATE')
    LABEL = os.getenv('LABEL')
