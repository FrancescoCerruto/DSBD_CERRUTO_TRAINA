import os


class Config(object):
    # FLASK ENVIRONMNET
    SECRET_KEY = os.urandom(12)

    # SECURITY ENVIRONMENT
    EXPIRATION_TIME_MINUTE = 10
    HASH_ALGORITHM = "sha256"
    TOKEN_ALGORITHM = "HS256"
    TOKEN_KEY = os.getenv("TOKEN_KEY")

    # URI SQL
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:{}@{}/{}'.format(
        os.getenv('MYSQL_ROOT_PASSWORD'),
        os.getenv('MYSQL_HOST'),
        os.getenv('MYSQL_DATABASE')
    )

    # KAFKA ENVIRONMENT
    BROKER_KAFKA = os.getenv('BROKER_KAFKA')
    PURCHASE_UPDATE_TOPIC = os.getenv('PURCHASE_UPDATE_TOPIC')
    SUBSCRIPTION_UPDATE_TOPIC = os.getenv('SUBSCRIPTION_UPDATE_TOPIC')

    # PROMETHEUS ENVIRONMNET
    PROMETHEUS_PORT = int(os.getenv('PROMETHEUS_PORT'))
    ERROR_METRICS = os.getenv('ERROR_METRICS')
    KAFKA_METRICS = os.getenv('KAFKA_METRICS')
    OPERATION_METRICS = os.getenv('OPERATION_METRICS')
    ERROR_RATE = os.getenv('ERROR_RATE')
    LABEL = os.getenv('LABEL')

