from random import choice
import string
import boto3

from models import Repository
from database import session
from config import AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, REGION_NAME, ENDPOINT_URL

db = session()

def create_url_or_api_key(length: int):
    postfix =  ''.join(choice(string.ascii_letters + string.digits) for _ in range(length))
    if postfix not in db.query(Repository.link).all():
        return postfix
    create_url_or_api_key()


session = boto3.Session(
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=REGION_NAME,
    )


s3 = session.client(
    service_name='s3',
    endpoint_url=ENDPOINT_URL
)
s3_resource = boto3.resource('s3')