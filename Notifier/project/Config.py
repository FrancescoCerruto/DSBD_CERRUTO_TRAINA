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

    TOKEN_ALGORITHM = "HS256"
    TOKEN_KEY = os.getenv("TOKEN_KEY")

    # KAFKA ENVIRONMENT
    BROKER_KAFKA = os.getenv('BROKER_KAFKA')
    ALERT_TOPIC = os.getenv('ALERT_TOPIC')

    # GOOGLE ENVIRONMENT
    SMTP_SERVER = os.getenv('SMTP_SERVER')
    SMTP_PORT = 587
    SENDER_EMAIL = os.getenv('SENDER_EMAIL')
    APP_PASSWORD = os.getenv('APP_PASSWORD')

    # PROMETHEUS ENVIRONMNET
    PROMETHEUS_PORT = int(os.getenv('PROMETHEUS_PORT'))
    ERROR_METRICS = os.getenv('ERROR_METRICS')
    KAFKA_METRICS = os.getenv('KAFKA_METRICS')
    OPERATION_METRICS = os.getenv('OPERATION_METRICS')
    ERROR_RATE = os.getenv('ERROR_RATE')
    LABEL = os.getenv('LABEL')
