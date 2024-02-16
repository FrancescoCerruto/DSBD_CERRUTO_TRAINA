import json

import requests
from project import db
from sqlalchemy import select, func

last_id_user = 0


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(255))


class Portfolio(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, unique=True)
    money = db.Column(db.Float)


class PortfolioAction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    timestamp = db.Column(db.DateTime)
    crypto_name = db.Column(db.String(255))
    crypto_value = db.Column(db.Float)
    quantity = db.Column(db.Integer)


class Subscription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    timestamp = db.Column(db.DateTime)
    crypto_name = db.Column(db.String(255))
    crypto_value = db.Column(db.Float)
    rule = db.Column(db.Float)


# retrieve user from email
def retrieve_user(email):
    try:
        return db.session.query(User).filter_by(email=email).first()
    except Exception:
        return -1


# create user and portfolio
def create_user_data(email, password):
    try:
        global last_id_user
        user = User(id=(last_id_user + 1), email=email, password=password)
        db.session.add(user)
        portfolio = Portfolio(user_id=last_id_user + 1, money=50000.0)
        db.session.add(portfolio)
        db.session.commit()
        last_id_user = last_id_user + 1
        return 0
    except Exception:
        return -1


# retrieve subscription list
def retrieve_subscription_user(user_id):
    try:
        result = db.session.execute(select(Subscription.timestamp, Subscription.crypto_name, Subscription.crypto_value,
                                           Subscription.rule)
                                    .where(Subscription.user_id == user_id)).all()
        data = []
        for sub_inst in result:
            data.append(
                {
                    'timestamp': sub_inst.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                    'crypto_name': sub_inst.crypto_name,
                    'crypto_value': sub_inst.crypto_value,
                    'rule': sub_inst.rule,
                }
            )
        return data
    except Exception:
        return -1


# check if user subscribe to crypto with specific rule
def check_subscription_user(user_id, crypto_name, rule):
    try:
        result = db.session.execute(select(Subscription.id, Subscription.rule)
                                    .where(Subscription.user_id == user_id)
                                    .where(Subscription.crypto_name == crypto_name)).all()
        # rule is set --> check specific subscription
        for entry in result:
            if entry.rule == rule:
                return entry.id
        return 0
    except Exception:
        return -1


# delete subscription
# {user_id, crypto_name, rule}
def create_subscription_user(user_id, timestamp, crypto_name, crypto_value, rule):
    try:
        new_subscription = Subscription(user_id=user_id, timestamp=timestamp,
                                        crypto_name=crypto_name, crypto_value=crypto_value,
                                        rule=rule)
        db.session.add(new_subscription)
        db.session.commit()
        return 0
    except Exception:
        return -1


# delete subscription
def delete_subscription_user(subscription_id):
    try:
        db.session.query(Subscription).filter_by(id=subscription_id).delete()
        db.session.commit()
        return 0
    except Exception:
        return -1


# retrieve purchase list
def retrieve_purchase_user(user_id):
    try:
        result = db.session.execute(select(PortfolioAction.timestamp, PortfolioAction.crypto_name,
                                           PortfolioAction.crypto_value, PortfolioAction.quantity)
                                    .where(PortfolioAction.user_id == user_id)).all()
        data = []
        for pur_inst in result:
            data.append(
                {
                    'timestamp': pur_inst.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                    'crypto_name': pur_inst.crypto_name,
                    'crypto_value': pur_inst.crypto_value,
                    'quantity': pur_inst.quantity,
                }
            )
        return data
    except Exception:
        return -1


# retrieve list of crypto bought
def retrieve_crypto_purchase_user(user_id):
    try:
        result = (db.session.query(PortfolioAction.crypto_name).filter_by(user_id=user_id)
                  .group_by(PortfolioAction.crypto_name).all())
        data = []
        for pur_inst in result:
            data.append(
                {
                    'crypto_name': pur_inst.crypto_name
                }
            )
        return data
    except Exception:
        return -1


# overview of portfolio: (money, purchase_value, actual_value (if no error during communication)
# aggregation story purchase on crypto_name)
def retrieve_portfolio_user(user_id):
    try:
        # retrive money
        money = retrieve_money_portfolio_user(user_id)
        # retrieve list crypto purchase
        crypto_list = retrieve_crypto_purchase_user(user_id)
        # retrieve all purchase list
        data_purchase = retrieve_purchase_user(user_id)
        if money == -1:
            return -1
        if crypto_list == -1:
            return -1
        if data_purchase == -1:
            return -1

        # calculate purchase and portfolio value
        data_portfolio = []
        purchase_value = 0.0
        portfolio_value = 0.0
        error_communication = False
        for entry in crypto_list:
            # retrieve actual value crypto
            response = requests.get(
                "http://crypto_tracker:5000/get_last_crypto_value?crypto=" + entry['crypto_name'])
            crypto_value = 0.0
            if response.status_code == 200:
                crypto_value = json.loads(response.content)['crypto_value']
            else:
                error_communication = True
            # for each crypto bought
            filter_data = {'user_id': user_id, 'crypto_name': entry['crypto_name']}
            filter_data = {key: value for (key, value) in filter_data.items() if value}
            # retrieve total quantity
            quantity = retrieve_quantity_purchase_crypto(**filter_data)
            if quantity == -1:
                return -1
            if quantity > 0:
                for purchase in data_purchase:
                    if purchase['crypto_name'] == entry['crypto_name']:
                        if error_communication is False:
                            portfolio_value = portfolio_value + crypto_value * float(purchase['quantity'])
                        purchase_value = purchase_value + purchase['crypto_value'] * float(purchase['quantity'])
                data_portfolio.append(
                    {
                        'crypto_name': entry['crypto_name'],
                        'total_quantity': quantity
                    }
                )
        if error_communication is False:
            data = {'money': money,
                    'purchase_value': purchase_value,
                    'portfolio_value': portfolio_value,
                    'purchase': data_portfolio
                    }
            return data
        else:
            data = {'money': money,
                    'purchase_value': purchase_value,
                    'portfolio_value': "Unknown",
                    'purchase': data_portfolio
                    }
            return data
    except Exception:
        return -1


# retrieve quantity crypto purchase
# {user_id, crypto_name}
def retrieve_quantity_purchase_crypto(**filter_data):
    try:
        result = (db.session.query(func.sum(PortfolioAction.quantity).label("quantity_available"))
                  .filter_by(**filter_data).first())
        return result.quantity_available
    except Exception:
        return -1


# check if user bought crypto
# {user_id, crypto_name}
def check_purchase_crypto(**filter_data):
    try:
        return db.session.query(PortfolioAction).filter_by(**filter_data).first()
    except Exception:
        return -1


# create purchase
def create_portfolio_action(user_id, timestamp, crypto_name, crypto_value, quantity, update_data_portfolio):
    try:
        new_purchase = PortfolioAction(user_id=user_id, timestamp=timestamp, crypto_name=crypto_name,
                                       crypto_value=crypto_value, quantity=quantity)
        db.session.add(new_purchase)
        update_portfolio(user_id, update_data_portfolio)
        db.session.commit()
        return 0
    except Exception:
        return -1


# money portfolio
def retrieve_money_portfolio_user(user_id):
    try:
        result = db.session.execute(select(Portfolio.money)
                                    .where(Portfolio.user_id == user_id)).first()
        return result.money
    except Exception:
        return -1


# update portfolio
# {money}
def update_portfolio(user_id, update_data):
    db.session.query(Portfolio).filter_by(user_id=user_id).update(update_data, synchronize_session='fetch')
