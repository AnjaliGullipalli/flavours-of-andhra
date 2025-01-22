import os


class Config:
    SECRET_KEY = os.urandom(24)
    MYSQL_HOST = 'localhost'
    MYSQL_PORT = 3306
    MYSQL_USER = 'sammy'
    MYSQL_PASSWORD = 'password'
    MYSQL_DB = 'KTM'
    MYSQL_CURSORCLASS = 'DictCursor'
