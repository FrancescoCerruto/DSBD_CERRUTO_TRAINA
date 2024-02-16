from flask import session
from project import db


class Alert(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255))
    timestamp = db.Column(db.DateTime)
    alert = db.Column(db.String(255))
    crypto_name = db.Column(db.String(255))
    delta_percentage = db.Column(db.Float)


def create_alert(email, crypto_name, timestamp, alert, delta_percentage):
    try:
        alert = Alert(email=email, crypto_name=crypto_name, timestamp=timestamp, alert=alert, delta_percentage=delta_percentage)
        db.session.add(alert)
        db.session.commit()
        return 0
    except Exception as e:
        return -1


def retrieve_alert_user(email):
    try:
        result = db.session.query(Alert.crypto_name, Alert.timestamp, Alert.alert, Alert.delta_percentage).filter_by(email=email).all()
        data = []
        for entry in result:
            data.append({
                'timestamp': entry.timestamp,
                'alert': entry.alert,
                'crypto': entry.crypto_name,
                'delta_percentage': entry.delta_percentage
            })
        return data
    except Exception as e:
        return -1
