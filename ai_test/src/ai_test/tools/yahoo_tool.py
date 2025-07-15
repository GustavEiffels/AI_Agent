import json
from datetime import datetime
from typing import Type, Any, List, Dict

from crewai.tools import BaseTool
from pydantic import BaseModel, Field
import yfinance as yf
import pandas as pd

class YahooFinanceDataInput(BaseModel):
    ticker_symbol:str = Field(..., description='조회할 해외 기업의 ticker')

class YahooFinanceDataTool(BaseTool):
    name: str = "Collect Financial Datad"
    description: str =(
        "Retrieve a company's financial data using its ticker symbol"
    )
    args_schema: Type[BaseModel] = YahooFinanceDataInput

    def _run(self, ticker_symbol: str) -> dict[str, str | dict[Any, Any]] | str:
        print(f'ticker_symbol : {ticker_symbol}')
        company = yf.Ticker(ticker_symbol)

        quarterly_income_statement = company.quarterly_financials
        quarterly_balance_sheet = company.quarterly_balance_sheet

        if quarterly_income_statement.empty or quarterly_balance_sheet.empty:
            return {
                "company_name": ticker_symbol,
                "financial_data_by_quarter": {},
                "error": "Financial data (income statement or balance sheet) not available for this ticker."
            }

        quarterly_income_statement = quarterly_income_statement.sort_index(axis=1, ascending=False)
        quarterly_balance_sheet = quarterly_balance_sheet.sort_index(axis=1, ascending=False)

        financial_data_by_quarter = {}
        quarter_dates = quarterly_income_statement.columns.tolist()


        for date_col in quarter_dates:
            year = date_col.year
            month = date_col.month

            if 1 <= month <= 3:
                quarter_str = f"{year}_Q1"
            elif 4 <= month <= 6:
                quarter_str = f"{year}_Q2"
            elif 7 <= month <= 9:
                quarter_str = f"{year}_Q3"
            elif 10 <= month <= 12:
                quarter_str = f"{year}_Q4"
            else:
                quarter_str = f"{year}_UnknownQ"

            quarter_data = {}

            # 손익계산서 항목 추출
            quarter_data["revenue"] = quarterly_income_statement.loc[
                "Total Revenue", date_col] if "Total Revenue" in quarterly_income_statement.index else None
            quarter_data["operating_income"] = quarterly_income_statement.loc[
                "Operating Income", date_col] if "Operating Income" in quarterly_income_statement.index else None
            quarter_data["net_income"] = quarterly_income_statement.loc[
                "Net Income", date_col] if "Net Income" in quarterly_income_statement.index else None

            # 대차대조표 항목 추출
            quarter_data["asset_moveable"] = quarterly_balance_sheet.loc[
                "Current Assets", date_col] if "Current Assets" in quarterly_balance_sheet.index else None
            quarter_data["asset_unmoveable"] = quarterly_balance_sheet.loc[
                "Non Current Assets", date_col] if "Non Current Assets" in quarterly_balance_sheet.index else None
            quarter_data["amount_asset"] = quarterly_balance_sheet.loc[
                "Total Assets", date_col] if "Total Assets" in quarterly_balance_sheet.index else None

            # 부채 항목
            quarter_data["bet_moveable"] = quarterly_balance_sheet.loc[
                "Current Liabilities", date_col] if "Current Liabilities" in quarterly_balance_sheet.index else None
            quarter_data["bet_unmoveable"] = quarterly_balance_sheet.loc[
                "Non Current Liabilities", date_col] if "Non Current Liabilities" in quarterly_balance_sheet.index else None
            quarter_data["amount_bet"] = quarterly_balance_sheet.loc[
                "Total Liabilities", date_col] if "Total Liabilities" in quarterly_balance_sheet.index else None

            quarter_data["amount_asset_equity"] = quarterly_balance_sheet.loc[
                "Total Stockholder Equity", date_col] if "Total Stockholder Equity" in quarterly_balance_sheet.index else None

            for key, value in quarter_data.items():
                if pd.isna(value):
                    quarter_data[key] = 0

            financial_data_by_quarter[quarter_str] = quarter_data

        result = {
            "company_name": company.info.get('longName', ticker_symbol),
            "financial_data_by_quarter": financial_data_by_quarter
        }

        print(f'result : {result}')

        return json.dumps(result, ensure_ascii=False)

class YahooFinanceNewsDataTool(BaseTool):
    name: str = "Collect FinanceNews" # 툴 이름 (Task description에서 사용)
    description: str =(
        "Getting Financial News by Company Name using Yahoo Finance API. "
        "It fetches recent news articles for a given ticker symbol and provides their date, source, headline, summary, and URL. "
        "Outputs a list of up to 5 news items."
    )
    args_schema: Type[BaseModel] = YahooFinanceDataInput # 티커 심볼을 입력으로 받음

    def _run(self, ticker_symbol: str) -> List[Dict[str, str]]:  # 반환 타입 명확히
        try:
            ticker = yf.Ticker(ticker_symbol)
            all_news_items = ticker.news

            extracted_news = []
            if all_news_items:
                for i, item in enumerate(all_news_items):
                    if i >= 3:  # 최신순으로 3개 뉴스만 추출
                        break

                    content_data = item.get('content', {})

                    title = content_data.get('title', item.get('title', 'N/A'))

                    link = content_data.get('canonicalUrl', {}).get('url')
                    if not link:  # canonicalUrl이 없으면 clickThroughUrl 시도
                        link = content_data.get('clickThroughUrl', {}).get('url', item.get('link', 'N/A'))

                    description = content_data.get('summary', item.get('summary', 'N/A'))

                    # date, time: item['content']['pubDate'] (ISO 8601 string) 또는 item['providerPublishTime'] (Unix timestamp)
                    pub_date_iso = content_data.get('pubDate')  # ISO 8601 string (예: "2025-07-14T16:46:18Z")
                    pub_time_unix = item.get('providerPublishTime')  # Unix timestamp (yfinance 직접 접근 시)

                    publish_date_obj = None
                    if pub_date_iso:
                        try:
                            # ISO 8601 문자열 파싱
                            publish_date_obj = datetime.fromisoformat(pub_date_iso.replace('Z', '+00:00'))
                        except ValueError:
                            pass
                    elif pub_time_unix:
                        try:
                            # Unix timestamp 파싱
                            publish_date_obj = datetime.fromtimestamp(pub_time_unix)
                        except (TypeError, ValueError):
                            pass

                    date_str = publish_date_obj.strftime('%Y-%m-%d') if publish_date_obj else "N/A"
                    time_str = publish_date_obj.strftime('%H:%M') if publish_date_obj else "N/A"

                    # source: item['content']['provider']['displayName']
                    source = content_data.get('provider', {}).get('displayName', 'N/A')
                    if source == 'N/A':  # provider 정보가 content 안에 없을 경우, 최상위 item에서 publisher 정보 확인
                        source = item.get('publisher', 'N/A')



                    extracted_news.append({
                        "title": title,
                        "link": link,
                        "description": description,
                        "date": date_str,
                        "time": time_str,
                        "source": source  # 'source' 필드 추가
                    })

                    print(f'extracted_news : {extracted_news}')
            return extracted_news
        except Exception as e:
            # 오류 발생 시 요청된 형식으로 오류 메시지 반환
            return [{
                "title": "News Fetch Failed",
                "link": "N/A",
                "description": f"Failed to fetch news for {ticker_symbol} using yfinance: {e}. Ensure ticker is correct and publicly traded.",
                "date": datetime.now().strftime('%Y-%m-%d'),
                "time": datetime.now().strftime('%H:%M'),
                "source": "System Error"  # 'source' 필드 추가
            }]


if __name__ == '__main__':

    # yahoo_tool = YahooFinanceDataTool()
    yahoo_tool = YahooFinanceNewsDataTool()

    ticker_name = input("테스트할 기업의 ticker 를 입력해라 : ")
    yahoo_tool_result = yahoo_tool._run(ticker_symbol=ticker_name)


