import jwt
import json
import requests
from datetime import datetime, timedelta
from flask import request
from werkzeug.security import generate_password_hash, check_password_hash
from project.KafkaProducer import send_message
from project.TokenVerifier import token_required
from project.models import (retrieve_purchase_user,
                            retrieve_money_portfolio_user,
                            retrieve_quantity_purchase_crypto, delete_subscription_user,
                            retrieve_subscription_user,
                            check_purchase_crypto,
                            create_portfolio_action,
                            create_subscription_user, check_subscription_user, retrieve_portfolio_user)
from project.Config import Config
from project.QoSMetrics import QoSMetrics
from project.models import retrieve_user, create_user_data
from project import create_app

app = create_app()
metrics = QoSMetrics()


@app.route('/login', methods=['POST'])
def login():
    metrics.set_operation()
    email = request.json.get('email')
    password = request.json.get('password')

    if None in [email, password]:
        return {'error': "required (email, password)"}, 400

    # retrieve user object
    record = retrieve_user(email)
    if record == -1:
        metrics.set_error()
        return {'error': "something went wrong"}, 500
    if not record or not check_password_hash(record.password, password):
        return {'error': "user not registered"}, 400
    # expiration time after 30 minutes
    token = jwt.encode(
        payload={
            "user_id": record.id,
            "user_email": record.email,
            "exp": datetime.utcnow() + timedelta(minutes=Config.EXPIRATION_TIME_MINUTE)
        },
        key=Config.TOKEN_KEY,
        algorithm=Config.TOKEN_ALGORITHM
    )
    return {'access_token': token}, 200


@app.route('/register', methods=['POST'])
def register():
    metrics.set_operation()
    email = request.json.get('email')
    password = request.json.get('password')

    if None in [email, password]:
        return {'error': "required (email, password)"}, 400

    # retrieve user object
    record = retrieve_user(email)
    if record == -1:
        metrics.set_error()

        return {'error': "something went wrong"}, 500
    if record:
        return {'error': "user already exists"}, 400

    # create user
    result = create_user_data(email, generate_password_hash(password, method=Config.HASH_ALGORITHM))
    if result == -1:
        metrics.set_error()

        return {'error': "something went wrong"}, 500
    return "User registered successfully", 200


@app.route('/subscription_user', methods=['GET', 'POST'])
@token_required
def subscription(user_id, email):
    metrics.set_operation()
    if request.method == 'GET':
        data = retrieve_subscription_user(user_id)
        if data == -1:
            metrics.set_error()

            return {'error': "something went wrong"}, 500

        return data, 200

    # retrieve data from request
    action = request.json.get('action')
    crypto = request.json.get('crypto')
    rule = request.json.get('rule')

    # empty data
    if None in [action, crypto, rule]:

        return "required (action, crypto, rule)", 400

    # validity
    if action not in ["subscribe", "unsubscribe"]:

        return "action not recognized (subscribe, unsubscribe)", 400
    if rule > 100.0 or rule < -100.0:

        return "rule in [-100.0; 100.0]", 400

    # check if crypto is handled by system
    try:

        response = requests.get("http://cryptotracker:5000/get_last_crypto_value?crypto=" + crypto)

        if response.status_code == 200:
            # crypto found
            crypto_value = json.loads(response.content)['crypto_value']

            subscription_id = check_subscription_user(user_id, crypto, rule)
            if subscription_id == -1:
                metrics.set_error()

                return "something went wrong", 500
            # store record
            if action == "subscribe":
                # if record already exists error 400
                if subscription_id >= 1:
                    return "subscription already done", 400
                result = create_subscription_user(user_id, datetime.utcnow(), crypto, crypto_value, rule)
                if result == 0:
                    # kafka send
                    # kafka metrics
                    kafka_start_time = datetime.utcnow()
                    data_kafka = {'action': "subscribe",
                                  'email': email,
                                  'rule': rule,
                                  'crypto_value': crypto_value}
                    send_message(key=crypto, value=json.dumps(data_kafka), topic=Config.SUBSCRIPTION_UPDATE_TOPIC)
                    # issue metrics
                    metrics.set_kafka(kafka_start_time)

                    return "Subscription stored successfully", 200
                else:
                    # issue metrics
                    metrics.set_error()
                    return "something went wrong", 500
            # delete record
            # if record it's not found error 400
            if subscription_id == 0:

                return "subscription not found", 400

            result = delete_subscription_user(subscription_id)

            if result == 0:
                # kafka send
                kafka_start_time = datetime.utcnow()
                data_kafka = {'action': "unsubscribe",
                              'email': email,
                              'rule': rule,
                              'crypto_value': "not required"}
                send_message(key=crypto, value=json.dumps(data_kafka), topic=Config.SUBSCRIPTION_UPDATE_TOPIC)
                # issue metrics
                metrics.set_kafka(kafka_start_time)

                return "Subscription deleted successfully", 200
            else:
                # issue metrics
                metrics.set_error()
                return "something went wrong", 500
        elif response.status_code == 400:
            return response.content, 400
        else:
            return response.content, 500
    except Exception:
        # issue metrics
        metrics.set_error()
        return "server not found", 404


@app.route('/portfolio_action_user', methods=['GET', 'POST'])
@token_required
def portfolio_action(user_id, email):
    metrics.set_operation()
    if request.method == 'GET':
        data = retrieve_purchase_user(user_id)
        if data == -1:
            # issue metrics
            metrics.set_error()

            return {'error': "something went wrong"}, 500

        return data, 200

    # retrieve data from request
    action = request.json.get('action')
    crypto = request.json.get('crypto')
    quantity = request.json.get('quantity')

    # empty data
    if None in [action, crypto, quantity]:

        return "required (action, crypto, quantity)", 400

    # validity
    if action not in ["buy", "sell"]:

        return "action not recognized (buy, sell)", 400
    if quantity <= 0:

        return "quantity not allowed", 400

    # check if crypto is handled by system
    try:
        # crypto metrics
        response = requests.get("http://cryptotracker:5000/get_last_crypto_value?crypto=" + crypto)

        if response.status_code == 200:
            # crypto found
            crypto_value = json.loads(response.content)['crypto_value']

            # process
            # retrieve user money
            money = retrieve_money_portfolio_user(user_id)
            if money == -1:
                metrics.set_error()

                return "something went wrong", 500

            # filter data to check purchase and subscription existence
            filter_data = {'user_id': user_id, 'crypto_name': crypto}
            filter_data = {key: value for (key, value) in filter_data.items() if value}

            # buy crypto
            if action == "buy":
                if money - float(quantity) * crypto_value < 0:

                    return "invalid quantity buy crypto - Max allowed {}".format(int(money / crypto_value)), 400

                # prepare data update
                update_data_portfolio = dict(money=money - float(quantity) * crypto_value)

                result = create_portfolio_action(user_id, datetime.now(), crypto, crypto_value, quantity,
                                                 update_data_portfolio)
                if result == 0:
                    # kafka send
                    kafka_start_time = datetime.utcnow()
                    # kafka send
                    data_kafka = {'email': email,
                                  'quantity': quantity,
                                  'crypto_value': crypto_value
                                  }
                    send_message(key=crypto, value=json.dumps(data_kafka), topic=Config.PURCHASE_UPDATE_TOPIC)
                    # issue metrics
                    metrics.set_kafka(kafka_start_time)

                    return "Purchase stored successfully", 200
                else:
                    # issue metrics
                    metrics.set_error()
                    return "something went wrong", 500
            if action == "sell":
                # sell crypto
                record = check_purchase_crypto(**filter_data)
                if record == -1:
                    # issue metrics
                    metrics.set_error()
                    return "something went wrong", 500
                if record is None:
                    return "user never bought this crypto", 400

                quantity_available = retrieve_quantity_purchase_crypto(**filter_data)
                if quantity_available == -1:
                    # issue metrics
                    metrics.set_error()
                    return "something went wrong", 500
                if quantity_available - quantity < 0:
                    return "invalid quantity sell crypto - Max allowed {}".format(quantity_available), 400

                update_data_portfolio = dict(money=money + float(quantity) * crypto_value)
                result = create_portfolio_action(user_id, datetime.now(), crypto, crypto_value, 0 - quantity,
                                                 update_data_portfolio)

                if result == 0:
                    # kafka send
                    kafka_start_time = datetime.utcnow()
                    # kafka send
                    data_kafka = {'email': email,
                                  'quantity': 0 - quantity,
                                  'crypto_value': crypto_value
                                  }
                    send_message(key=crypto, value=json.dumps(data_kafka), topic=Config.PURCHASE_UPDATE_TOPIC)
                    # issue metrics
                    metrics.set_kafka(kafka_start_time)

                    return "Sell stored successfully", 200
                else:
                    metrics.set_error()
                    return "something went wrong", 500
        elif response.status_code == 400:

            return response.content, 400
        else:
            return response.content, 500
    except Exception as e:
        # issue metrics
        metrics.set_error()
        return "server not found", 404


@app.route('/overview_portfolio_user', methods=['GET'])
@token_required
def overview_portfolio(user_id, email):
    metrics.set_operation()

    data = retrieve_portfolio_user(user_id)
    if data == -1:
        # issue metrics
        metrics.set_error()

        return {'error': "something went wrong"}, 500

    return data, 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
