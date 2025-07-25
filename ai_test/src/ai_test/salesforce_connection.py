from simple_salesforce import Salesforce
import os
from dotenv import load_dotenv
load_dotenv()

class SfConnection():

    def __init__(self):
        SF_CUSTOMER_KY = os.getenv('SF_CUSTOMER_KY')
        SF_CUSTOMER_SECRET = os.getenv('SF_CUSTOMER_KY')
        SF_USERNAME = os.getenv('SF_USERNAME')
        SF_PASSWORD = os.getenv('SF_PASSWORD')
        SF_SECURITY_TOKEN = os.getenv('SF_SECURITY_TOKEN')
        self.sf_info = Salesforce(
            username=SF_USERNAME,
            password=f'{SF_PASSWORD}{SF_SECURITY_TOKEN}',
            consumer_key=SF_CUSTOMER_KY,
            consumer_secret=SF_CUSTOMER_SECRET
        )
