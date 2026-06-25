import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = 'hard-to-guess-string'
    # MySQL Connection configuration
    # Format: mysql+pymysql://<username>:<password>@<host>:<port>/<database_name>
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:project567@localhost:3306/lebestates'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
