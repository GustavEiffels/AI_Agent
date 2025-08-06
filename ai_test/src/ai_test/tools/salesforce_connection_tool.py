from crewai.tools import BaseTool
from simple_salesforce import Salesforce
import os
import pandas as pd
from datetime import datetime

class SalesforceExtractTool(BaseTool):
    name: str = "Salesforce Extract Tool"
    description: str = "Extracts Account and Opportunity data from Salesforce CRM."

    def _run(self, query: str = None) -> dict:
        try:
            sf = Salesforce(
                username=os.getenv('MAIN_SF_USERNAME'),
                password=os.getenv('MAIN_SF_PASSWORD'),
                security_token=os.getenv('MAIN_SF_TOKEN')
            )

            current_year = datetime.now().year
            os.makedirs("outputs/salesforce_connector", exist_ok=True)

            # Account 데이터
            account_query = """
                SELECT Id, Name, Industry, CreatedDate
                FROM Account
                WHERE CreatedDate >= 2025-01-01T00:00:00Z
                ORDER BY CreatedDate ASC
            """
            accounts = sf.query_all(account_query)
            df_accounts = pd.DataFrame(accounts['records']).drop(['attributes'], axis=1)
            account_file = f"outputs/salesforce_connector/Account_data_{current_year}.csv"
            df_accounts.to_csv(account_file, index=False)

            # Opportunity 데이터 (834건 전부 가져오기)
            opportunity_query = """
                SELECT Id, Name, StageName, Amount, CloseDate, AccountId, CreatedDate
                FROM Opportunity
                WHERE CreatedDate >= 2025-01-01T00:00:00Z
                ORDER BY CreatedDate ASC
            """
            opportunities = sf.query_all(opportunity_query)
            df_opps = pd.DataFrame(opportunities['records']).drop(['attributes'], axis=1)

            # 날짜 포맷 변환 (원하는 경우)
            if 'CreatedDate' in df_opps.columns:
                df_opps['CreatedDate'] = pd.to_datetime(df_opps['CreatedDate']).dt.strftime('%Y-%m-%d %H:%M:%S')

            opp_file = f"outputs/salesforce_connector/Opportunity_data_{current_year}.csv"
            df_opps.to_csv(opp_file, index=False)

            return {
                "status": "success",
                "files": {
                    "account": account_file,
                    "opportunity": opp_file
                },
                "account_shape": df_accounts.shape,
                "opportunity_shape": df_opps.shape
            }

        except Exception as e:
            return {"status": "error", "message": str(e)}