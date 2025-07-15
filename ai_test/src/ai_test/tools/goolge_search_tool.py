from typing import Type
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from dotenv import load_dotenv
import os
import json
from googleapiclient.discovery import build

load_dotenv()

class GoogleSearchTickerInput(BaseModel):
    company_name: str = Field(..., description="The Company Name")

class GoogleSearchTickerTool(BaseTool):
    name: str = "Getting Ticker By Google Search Engine"
    description: str = (
        "Searches for the stock ticker symbol using the Google Custom Search API with the given international company name. "
        "Extracts and returns the most probable ticker symbol from the search results in JSON format."
    )
    args_schema: Type[BaseModel] = GoogleSearchTickerInput

    def _run(self, company_name: str) -> str:
        api_key = os.getenv("GOOGLE_KEY")
        search_engine = os.getenv("GOOGLE_CSE")

        if not api_key or not search_engine:
            return json.dumps({"error": "GOOGLE_API_KEY or GOOGLE_CSE_ID environment variable is not set."})

        try:
            # Build the Google Custom Search service
            service = build("customsearch", "v1", developerKey=api_key)
            res = service.cse().list(
                q=f'{company_name} stock ticker',
                cx=search_engine,
                num=5
            ).execute()
            return res['items']

        except Exception as e:
            return json.dumps({"error": f"Google API error: {str(e)}"})

if __name__ == '__main__':
    company = input("Enter the international company name (e.g., APPLE, TESLA, NVIDIA): ")
    result = GoogleSearchTickerTool()._run(company_name=company)
    print(result)