from flask import Flask
from flask_mongoengine import MongoEngine
from project.Config import Config

# init SQLAlchemy so we can use it later in our models
db = MongoEngine()


def create_app():
    app = Flask(__name__)

    app.config.from_object(Config)

    db.init_app(app)

    return app
