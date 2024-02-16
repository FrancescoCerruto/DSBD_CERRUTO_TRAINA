import os


class Config(object):
    # FLASK ENVIRONMNET
    SECRET_KEY = os.urandom(12)

    # MONGO ENVIRONMENT
    MONGODB_SETTINGS = {
        'db': os.getenv("MONGO_DB"),
        'host': os.getenv("MONGO_HOST")
    }

    # PROMETHEUS ENVIRONMNET
    PROMETHEUS_SERVER = os.getenv('PROMETHEUS_SERVER')
    KAFKA_METRICS = os.getenv('KAFKA_METRICS')
    ERROR_RATE = os.getenv('ERROR_RATE')
    CRYPTO_LABEL = os.getenv('CRYPTO_LABEL')
    NOTIFIER_LABEL = os.getenv('NOTIFIER_LABEL')
    PORTFOLIO_LABEL = os.getenv('PORTFOLIO_LABEL')
    SUBSCRIPTION_LABEL = os.getenv('SUBSCRIPTION_LABEL')
    USER_LABEL = os.getenv('USER_LABEL')

    METRICS_ALLOWED = [
        {
            'metrics': KAFKA_METRICS,
            'label': CRYPTO_LABEL
        },
        {
            'metrics': KAFKA_METRICS,
            'label': PORTFOLIO_LABEL
        },
        {
            'metrics': KAFKA_METRICS,
            'label': SUBSCRIPTION_LABEL
        },
        {
            'metrics': KAFKA_METRICS,
            'label': USER_LABEL
        },
        {
            'metrics': ERROR_RATE,
            'label': CRYPTO_LABEL
        },
        {
            'metrics': ERROR_RATE,
            'label': NOTIFIER_LABEL
        },
        {
            'metrics': ERROR_RATE,
            'label': PORTFOLIO_LABEL
        },
        {
            'metrics': ERROR_RATE,
            'label': SUBSCRIPTION_LABEL
        },
        {
            'metrics': ERROR_RATE,
            'label': USER_LABEL
        }
    ]
