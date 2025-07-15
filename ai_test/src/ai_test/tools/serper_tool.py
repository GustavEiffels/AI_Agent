from typing import Type
from dotenv import load_dotenv
from litellm.llms.custom_httpx.httpx_handler import headers
from pydantic import BaseModel, Field
load_dotenv()
import os,requests


class SearchTickerDataInput(BaseModel):
    company_name: str = Field(..., description='조회할 기업의 정확한 이름')


class SearchTickerDataTool(BaseModel):
    name: str = "Serper API for Search Ticker by Company Name"
    description: str = (
        "This tool utilizes the Serper API to search for the stock ticker symbol of companies, "
        "specifically focusing on international enterprises. It aims to find the precise ticker symbol for a given company name."
    )
    args_schema : Type[BaseModel] = SearchTickerDataInput

    def _run(self, company_name:str) -> str | None:

        serper_key = os.getenv('SERPER_KEY')

        if serper_key is None:
            raise ValueError("SERPER_KEY 환경 변수가 없습니다. .env 파일을 확인하세요.")

        query =  {
            'q':f'What is ticker of the {company_name}'
        }
        headers = {
            'X-API-KEY': f'{serper_key}',
            'Content-Type': 'application/json'
        }

        response = requests.post(
            'https://google.serper.dev/search',
            headers=headers,
            json=query
        )

        return response.json()

if __name__ == "__main__":

    surper_tool = SearchTickerDataTool()
    test_company_name = input("테스트할 해외 기업이름을 입력")

    try:
        result = surper_tool._run(company_name=test_company_name)

    except Exception as e:
        print(f'Exception : {e}')
