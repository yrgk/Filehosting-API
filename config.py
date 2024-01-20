import os
from dotenv import load_dotenv

load_dotenv()

PASSWORD = os.environ.get("DB_PASS")
USER = os.environ.get("DB_USER")
HOST = os.environ.get("DB_HOST")
PORT = os.environ.get("DB_PORT")
NAME = os.environ.get("DB_NAME")
AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")
REGION_NAME = os.environ.get("REGION_NAME")
ENDPOINT_URL = os.environ.get("ENDPOINT_URL")