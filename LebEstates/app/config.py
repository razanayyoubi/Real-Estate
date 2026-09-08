import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '../.env'))

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'hard-to-guess-string')
    # MySQL Connection configuration
    # Format: mysql+pymysql://<username>:<password>@<host>:<port>/<database_name>
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'mysql+pymysql://root:1234@localhost:3306/lebestates')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Mailjet Credentials & Sender Info
    MAILJET_API_KEY = os.getenv('MAILJET_API_KEY')
    MAILJET_SECRET_KEY = os.getenv('MAILJET_SECRET_KEY')
    MAILJET_SENDER_EMAIL = os.getenv('MAILJET_SENDER_EMAIL', 'mohamadayoubi050@gmail.com')
    MAILJET_SENDER_NAME = os.getenv('MAILJET_SENDER_NAME', 'LebEstates')
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

