from datetime import datetime
from sqlalchemy import func
from project import db


class Crypto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))
    value = db.Column(db.Float)
    timestamp = db.Column(db.DateTime)


def create_crypto(name, value, timestamp):
    try:
        crypto = Crypto(name=name, value=value, timestamp=timestamp)
        db.session.add(crypto)
        db.session.commit()
        return 0
    except Exception as e:
        return -1


def retrieve_last_value_crypto(crypto):
    try:
        last_value = (db.session.query(Crypto.value, Crypto.timestamp).filter_by(name=crypto).
                      order_by(Crypto.timestamp.desc()).first())
        if not last_value:
            return -2
        return last_value.value
    except Exception as e:
        return -1