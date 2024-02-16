from flask import Blueprint, request
from .Worker import Worker
from .QoSMetrics import QoSMetrics
from .TokenVerifier import token_required
from .models import create_alert, retrieve_alert_user

notification = Blueprint('user', __name__)
metrics = QoSMetrics()
kafka = Worker(metrics)


@notification.route('/insert_notification_record', methods=['POST'])
def insert_crypto_record():
    # issue request
    metrics.set_operation()

    email = request.form.get('email')
    timestamp = request.form.get('timestamp')
    alert = request.form.get('alert')
    crypto_name = request.form.get('crypto_name')
    delta_percentage = request.form.get('delta_percentage')

    result = create_alert(email, crypto_name, timestamp, alert, delta_percentage)
    if result == -1:
        # issue error
        metrics.set_error()
        return {'error: something went wrong'}, 500
    return '', 200


@notification.route('/get_alert_user', methods=['GET'])
@token_required
def get_alert(email):
    # issue request
    metrics.set_operation()
    result = retrieve_alert_user(email)
    if result == -1:
        # issue error
        metrics.set_error()
        return {'error': "something went wrong"}, 500
    return result, 200
