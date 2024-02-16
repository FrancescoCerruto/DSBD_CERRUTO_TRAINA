from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from project.Config import Config


# init SQLAlchemy so we can use it later in our models
db = SQLAlchemy()


def create_app():
    app = Flask(__name__)

    app.config.from_object(Config)

    db.init_app(app)

    """blueprint --> set di operazioni registrate su di una applicazione
    servono per rendere modulare l'applicazione
    tramite un application factory si modifica a runtime l'applicazione sviluppata

    ad ogni operazione viene associata una view function
    ogni view function ha un url specifico (se ne occupa flask dell'indirizzamento)
    """
    # blueprint for auth routes in our app
    from project.crypto import crypto as crypto_blueprint
    app.register_blueprint(crypto_blueprint)

    with app.app_context():
        db.create_all()

    return app
