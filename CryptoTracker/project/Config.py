import os


class Config(object):
    # FLASK ENVIRONMNET
    SECRET_KEY = os.urandom(12)

    # URI SQL
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:{}@{}/{}'.format(
        os.getenv('MYSQL_ROOT_PASSWORD'),
        os.getenv('MYSQL_HOST'),
        os.getenv('MYSQL_DATABASE')
    )

    # UPDATE TIME CRYPTO VALUE
    UPDATE_TIME_MINUTE = int(os.getenv('UPDATE_TIME_MINUTE'))

    # KAFKA - work in progress
    BROKER_KAFKA = os.getenv('BROKER_KAFKA')
    CRYPTO_UPDATE_TOPIC = os.getenv('CRYPTO_UPDATE_TOPIC')

    # PROMETHEUS ENVIRONMNET
    PROMETHEUS_PORT = int(os.getenv('PROMETHEUS_PORT'))
    ERROR_METRICS = os.getenv('ERROR_METRICS')
    KAFKA_METRICS = os.getenv('KAFKA_METRICS')
    OPERATION_METRICS = os.getenv('OPERATION_METRICS')
    ERROR_RATE = os.getenv('ERROR_RATE')
    LABEL = os.getenv('LABEL')
