from flask import Flask
from flask_mysqldb import MySQL
from .route import main


def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')

    mysql = MySQL(app)
    app.mysql = mysql
    app.register_blueprint(main)

    return app, mysql
