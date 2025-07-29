from crewai.tools import BaseTool
from ai_test.gs_sf_connect import SalesforceConnection
import datetime

now = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
class SalesforceEmailTemplateTool(BaseTool):
    name: str = "SalesforceEmailTemplateTool"
    description: str = "Saves a report as a Salesforce Classic Email Template using name, subject, HTML body, and folder ID."

    def _run(self, name: str, subject: str, html_body: str, folder_name: str = "Public Templates") -> str:
        try:
            sf = SalesforceConnection().connect()

            # 🟡 Folder ID 조회
            query = f"SELECT Id FROM Folder WHERE Name = '{folder_name}' AND Type = 'Email' LIMIT 1"
            result = sf.query(query)
            records = result.get("records", [])
            if not records:
                return f"❌ Folder '{folder_name}' not found."

            folder_id = records[0]["Id"]
            developer_name = f"{name.replace(' ', '_')}_{now}"
            # ✅ 템플릿 생성
            email_template = sf.EmailTemplate.create({
                'Name': name+'_' + now + '',
                'DeveloperName': developer_name,
                'Subject': subject,
                'HtmlValue': html_body,
                'FolderId': folder_id,
                'TemplateType': 'custom'
            })

            return f"✅ EmailTemplate created: ID = {email_template.get('id')}"
        except Exception as e:
            return f"❌ Failed to create EmailTemplate: {str(e)}"