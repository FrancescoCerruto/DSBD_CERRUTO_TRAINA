from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy

from project.Config import Config


# init SQLAlchemy so we can use it later in our models
db = SQLAlchemy()


def create_app():
    app = Flask(__name__)

    app.config.from_object(Config)

    db.init_app(app)

    with app.app_context():
        db.create_all()

    return app
