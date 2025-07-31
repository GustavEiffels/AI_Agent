import os
from simple_salesforce import Salesforce
from ai_test.main import StandardResponse

def send_to_sfdc(data:StandardResponse):
    try:
        sf = Salesforce(
            username=os.getenv('MAIN_SF_USERNAME'),
            password=os.getenv('MAIN_SF_PASSWORD'),
            security_token=os.getenv('MAIN_SF_TOKEN'),
            instance_url=os.getenv('MAIN_SF_INSTANCE_URL')
        )
        print(type(data))
        response = sf.apexecute('crew-result','POST',data=data.dict())
        print(f'response from sfdc  : {response}')

    except Exception as e:
        print(f'SFDC ERROR : {e}')