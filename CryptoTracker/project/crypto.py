from flask import Blueprint, request, g
from .QoSMetrics import QoSMetrics
from .models import retrieve_last_value_crypto, create_crypto
from .Worker import Worker

crypto = Blueprint('user', __name__)
metrics = QoSMetrics()
kafka = Worker(metrics)


@crypto.route('/insert_crypto_record', methods=['POST'])
def insert_crypto_record():
    # issue crypto request
    metrics.set_operation()

    name = request.form.get('name')
    value = request.form.get('value')
    timestamp = request.form.get('timestamp')

    result = create_crypto(name, value, timestamp)
    if result == -1:
        # issue crypto error
        metrics.set_error()

        return '', 500
    return '', 200


@crypto.route('/get_last_crypto_value', methods=['GET'])
def retrieve_last_value():
    # issue crypto request
    metrics.set_operation()

    crypto_name = request.args.get('crypto')
    crypto_value = retrieve_last_value_crypto(crypto_name)
    if crypto_value == -1:
        # issue crypto error
        metrics.set_error()

        return "crypto_tracker error - something went wrong", 500
    if crypto_value == -2:
        return "crypto does not exist", 400
    return {'crypto_value': crypto_value}, 200