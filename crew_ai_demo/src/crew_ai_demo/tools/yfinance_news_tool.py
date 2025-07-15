# src/tools/yfinance_news_tool.py

import yfinance as yf
from crewai.tools import BaseTool
from typing import List, Dict, Any
from datetime import datetime

class YFinanceNewsTool(BaseTool):
    name: str = "Yahoo Finance News Tool"
    description: str = "Fetches the three most recent news articles for a publicly traded company using its stock ticker from Yahoo Finance. Input should be the company's stock ticker (e.g., 'TSLA', 'NVDA')."

    def _run(self, ticker_symbol: str) -> List[Dict[str, str]]:
        try:
            ticker = yf.Ticker(ticker_symbol)
            all_news_items = ticker.news


            extracted_news = []
            if all_news_items:
                for i, item in enumerate(all_news_items):
                    if i >= 3:
                        break

                    content = item.get('content', {}) 

                    title = content.get('title', 'N/A')
                    pub_date_raw = content.get('pubDate') 
                    publish_date = "N/A"
                    if pub_date_raw:
                        try:

                            publish_date = datetime.fromisoformat(pub_date_raw.replace('Z', '+00:00')).strftime('%Y-%m-%d')
                        except ValueError:
                            publish_date = "Invalid Date Format"
                    
                    source = content.get('provider', {}).get('displayName', 'N/A')
                    
                    summary = content.get('summary', 'N/A')

                    url = content.get('canonicalUrl', {}).get('url', 'N/A')
                    if url == 'N/A': 
                        url = content.get('clickThroughUrl', {}).get('url', 'N/A')
                    
                    if not url or url.startswith("N/A"):
                        url = f"https://finance.yahoo.com/quote/{ticker_symbol}/news" 
                        
                    extracted_news.append({
                        "date": publish_date,
                        "source": source,
                        "headline": title,
                        "summary": summary,
                        "url": url
                    })
            return extracted_news
        except Exception as e:
            return [{
                "date": datetime.now().strftime('%Y-%m-%d'),
                "source": "System Error",
                "headline": "News Fetch Failed",
                "summary": f"Failed to fetch news for {ticker_symbol} using yfinance: {e}. Ensure ticker is correct and publicly traded.",
                "url": "N/A"
            }]