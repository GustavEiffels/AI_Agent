import os
import logging
from simple_salesforce import Salesforce
from dotenv import load_dotenv
# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
class SalesforceConnection:
    def __init__(self):
        env_path = '../../../.env'
        load_dotenv(env_path)
        self.username = os.getenv('GS_SF_USERNAME')
        self.password = os.getenv('GS_SF_PASSWORD')
        self.security_token = os.getenv('GS_SF_TOKEN')
        self.instance_url = os.getenv('GS_SF_INSTANCE_URL')
        self.sf = None
    def connect(self):
        try:
            if not all([self.username, self.password, self.security_token, self.instance_url]):
                raise ValueError("Missing one or more Salesforce credentials in .env file")
            logger.info("Attempting to connect to Salesforce...")
            # Coonect
            self.sf = Salesforce(
                username=self.username,
                password=self.password,
                security_token=self.security_token,
                instance_url=self.instance_url
            )
            logger.info("Connected to Salesforce successfully")
            return self.sf
        except Exception as e:
            logger.error(f"Failed to connect to Salesforce: {str(e)}")
            raise
    # Connect Test
    def test_query(self):
        try:
            result = self.sf.query("SELECT Id, Name FROM Account LIMIT 5")
            logger.info(f"Query successful. Retrieved {len(result['records'])} accounts")
            return result['records']
        except Exception as e:
            logger.error(f"Query failed: {str(e)}")
            raise
if __name__ == "__main__":
    # Test the connection
    try:
        sf_conn = SalesforceConnection()
        sf_conn.connect()
        accounts = sf_conn.test_query()
        for account in accounts:
            print(f"Account: {account['Name']}")
    except Exception as e:
        print(f"Error: {str(e)}")