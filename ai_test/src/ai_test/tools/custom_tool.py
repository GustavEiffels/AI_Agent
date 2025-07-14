from crewai.tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field
import json

class MyCustomToolInput(BaseModel):
    """Input schema for MyCustomTool."""
    argument: str = Field(..., description="Description of the argument.")

class MyCustomTool(BaseTool):
    name: str = "기업 재무정보 수집 도구"
    description: str = (
        "입력된 회사명을 기준으로 OpenDART에서 재무 정보를 조회합니다. "
        "분기별 유동자산, 부채, 매출, 순이익 등의 데이터를 제공합니다."
    )

    def _run(self, company_name: str) -> str:
        try:
            data = collect_financial_data(company_name)
            return json.dumps(data, ensure_ascii=False, indent=2)
        except Exception as e:
            return f"[오류] {company_name} 재무정보 수집 실패: {str(e)}"
