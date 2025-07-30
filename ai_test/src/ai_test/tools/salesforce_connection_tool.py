from crewai.tools import BaseTool
from simple_salesforce import Salesforce
import os
import pandas as pd

class SalesforceExtractTool(BaseTool):
    name: str = "Salesforce Extract Tool"
    description: str = "Extracts and processes data from Salesforce CRM."

    def _run(self, query: str) -> str:
        try:
            sf = Salesforce(username=os.getenv('HS_SF_USERNAME'), password=os.getenv('HS_SF_PASSWORD'), security_token=os.getenv('HS_SF_TOKEN'))
            result = sf.query_all(query)  # 전체 데이터 쿼리
            df = pd.DataFrame(result['records'])
            df.drop(['attributes'], axis=1, inplace=True)  # 정리
            summary = df.to_json(orient='records')  # JSON으로 반환
            return summary
        except Exception as e:
            return f"Error: {str(e)}"