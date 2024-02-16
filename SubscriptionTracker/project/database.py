from sqlalchemy import create_engine, Column, Integer, String, Float, select, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from project.Config import Config

engine = create_engine(Config.SQLALCHEMY_DATABASE_URI, isolation_level="READ COMMITTED")

Session = sessionmaker(bind=engine)
Session.configure(bind=engine)
session = Session()

Base = declarative_base()


class Subscription(Base):
    __tablename__ = 'subscription'
    id = Column(Integer, primary_key=True)
    email = Column(String(255))
    crypto_name = Column(String(255))
    crypto_value = Column(Float)
    rule = Column(Float)


Base.metadata.create_all(engine)


def create_subscription(email, crypto_name, crypto_value, rule):
    try:
        new_subscription = Subscription(email=email, crypto_name=crypto_name, crypto_value=crypto_value, rule=rule)
        session.add(new_subscription)
        session.commit()
        return 0
    except Exception as e:
        return -1


def delete_subscription_user(email, crypto_name, rule):
    try:
        result = session.execute(select(Subscription.id, Subscription.rule)
                                 .where(Subscription.email == email)
                                 .where(Subscription.crypto_name == crypto_name)).all()
        # rule is set --> check specific subscription
        for entry in result:
            if entry.rule == rule:
                session.query(Subscription).filter_by(id=entry.id).delete()
                session.commit()
                return 0
    except Exception:
        return -1


def retrieve_info_subscription_crypto(crypto):
    try:
        result = session.execute(select(Subscription.email, Subscription.rule, Subscription.crypto_value).
                                 where(Subscription.crypto_name == crypto)).all()

        data = []
        for entry in result:
            data.append((entry.email, entry.rule, entry.crypto_value))
        return data
    except Exception:
        return -1