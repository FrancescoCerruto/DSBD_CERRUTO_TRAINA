from sqlalchemy import create_engine, Column, Integer, String, Float, select, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from project.Config import Config

engine = create_engine(Config.SQLALCHEMY_DATABASE_URI, isolation_level="READ COMMITTED")

Session = sessionmaker(bind=engine)
Session.configure(bind=engine)
session = Session()

Base = declarative_base()


class PortfolioAction(Base):
    __tablename__ = 'portfolio_action'
    id = Column(Integer, primary_key=True)
    email = Column(String(255))
    crypto_name = Column(String(255))
    crypto_value = Column(Float)
    quantity = Column(Integer)


Base.metadata.create_all(engine)


# insert action
def create_portfolio_action(email, crypto_name, crypto_value, quantity):
    try:
        new_purchase = PortfolioAction(email=email, crypto_name=crypto_name,
                                       crypto_value=crypto_value, quantity=quantity)
        session.add(new_purchase)
        session.commit()
        return 0
    except Exception as e:
        return -1


# retrieve purchase list user
def retrieve_purchase_list(email):
    try:
        # retrieve all purchase
        result = session.execute(select(PortfolioAction.crypto_name,
                                        PortfolioAction.crypto_value, PortfolioAction.quantity)
                                 .where(PortfolioAction.email == email)).all()
        data = []
        for pur_inst in result:
            data.append({
                'crypto_name': pur_inst.crypto_name,
                'crypto_value': pur_inst.crypto_value,
                'quantity': pur_inst.quantity,
            })
        return data
    except Exception as e:
        return -1


# retrieve all user that bought crypto
def retrieve_all_user(crypto_name):
    try:
        result = session.query(PortfolioAction.email).filter_by(crypto_name=crypto_name).group_by(PortfolioAction.email).all()
        data = []
        for instance in result:
            data.append(instance.email)
        return data
    except Exception:
        return -1