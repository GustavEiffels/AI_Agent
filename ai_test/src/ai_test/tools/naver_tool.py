import requests, os
from dotenv import load_dotenv
from email.utils import parsedate_to_datetime
load_dotenv()
from typing import Type, Any
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

class NaverSearchDataInput(BaseModel):
    company_name:str = Field(..., description='조회할 기업의 정확한 이름')

class NaverSearchDataTool(BaseTool):
    name: str = "Naver Data"
    description: str = (
        "기업 이름을 기반 으로 Naver API 에서 데이터를 조회"
    )
    args_schema: Type[BaseModel] = NaverSearchDataInput

    def _run(self,company_name:str) -> list[Any] | None:

        naver_id = os.getenv("NAVER_ID")
        naver_secret = os.getenv("NAVER_SECRET")

        if naver_id is None:
            raise  ValueError("NAVER_ID 환경 변수가 없습니다. .env 파일을 확인하세요.")

        if naver_secret is None:
            raise  ValueError("NAVER_SECRET 환경 변수가 없습니다. .env 파일을 확인하세요.")

        query = company_name
        display : int = 3
        page : int = 1
        sort_type: str = 'sim'
        url = f'https://openapi.naver.com/v1/search/news.json?query={query}&display={display}&start={page}&sort={sort_type}'

        headers = {
            'X-Naver-Client-Id':f'{naver_id}',
            'X-Naver-Client-Secret':f'{naver_secret}'
        }

        data = []

        try:
            response = requests.get(url, headers=headers)
            items = response.json()['items']
            if len(items) > 0:

                for item in items:
                    datetime_object = parsedate_to_datetime(item['pubDate'])
                    data.append({
                        'title':item['title'].replace('<b>','').replace('</b>',''),
                        'link':item['originallink'],
                        'description':item['description'].replace('<b>','').replace('</b>',''),
                        'date':datetime_object.strftime("%Y-%m-%d"),
                        'time':datetime_object.strftime("%H:%M")
                    })

            print(f'data : {data}')

            return data
        except requests.exceptions.Timeout:
            print("요청 시간 초과")

