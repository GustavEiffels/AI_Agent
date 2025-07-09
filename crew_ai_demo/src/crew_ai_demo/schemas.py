from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any # Any 추가 (유연성을 위해)

# --- Financial Analysis DTOs (기존 유지) ---
class FinancialMetricDetails(BaseModel):
    current_assets_USD: float = Field(..., description="유동자산 (USD)")
    non_current_assets_USD: float = Field(..., description="비유동자산 (USD)")
    current_liabilities_USD: float = Field(..., description="유동부채 (USD)")
    non_current_liabilities_USD: float = Field(..., description="비유동부채 (USD)")
    operating_profit_USD: float = Field(..., description="영업이익 (USD)")
    net_income_USD: float = Field(..., description="당기순이익 (USD)")
    current_ratio: float
    debt_to_equity_ratio: float
    quick_ratio_estimated: float

class FinancialChanges(BaseModel):
    QoQ_percent_changes: Dict[str, float] = Field(..., description="직전 분기 대비 변화율")
    YoY_percent_changes: Dict[str, float] = Field(..., description="전년 동기 대비 변화율")

class FinancialAnalysisSection(BaseModel):
    key_financial_metrics: Dict[str, FinancialMetricDetails] = Field(..., description="각 분기별 주요 재무 지표 (예: 'Q1_2025')")
    changes: FinancialChanges
    financial_insights: List[str] = Field(..., description="재무 상태 및 성과에 대한 분석 인사이트")

# --- Recent News DTOs (NewsItem.summary에 Optional 적용) ---
class NewsItem(BaseModel):
    date: str = Field(..., description="뉴스 날짜 (YYYY-MM-DD)")
    source: str = Field(..., description="뉴스 출처")
    headline: str = Field(..., description="뉴스 헤드라인")
    summary: Optional[str] = Field(None, description="뉴스 요약") # <-- Optional[str]로 변경, 기본값 None
    url: str = Field(..., description="뉴스 기사 URL")

# --- Strategic Recommendations DTOs (기존 유지) ---
class StrategicRecommendation(BaseModel):
    """단일 전략적 권고안을 나타냅니다."""
    title: str = Field(..., description="전략적 권고안의 제목")
    contents: List[str] = Field(..., description="권고안의 상세 내용 (정당화, 영향, 실행 단계, SMART 목표 포함)") # <-- actions -> contents 변경


# --- Full Report DTO (메인 구조 유지) ---
class FullAnalysisReport(BaseModel):
    executive_summary: str = Field(..., description="경영진 요약")
    introduction: str = Field(..., description="서론의 전체 내용")
    company_overview: str = Field(..., description="엔비디아 개요의 전체 내용")
    products_and_technology_analysis: str = Field(..., description="제품 및 기술 분석의 전체 내용")
    market_status_and_competition: str = Field(..., description="시장 현황 및 경쟁 환경의 전체 내용")
    financial_analysis: FinancialAnalysisSection # 복잡한 재무 구조 유지
    key_risk_factors: str = Field(..., description="주요 위험 요소의 전체 내용")
    recent_news: List[NewsItem] = Field(..., description="최신 뉴스 목록")
    strategic_recommendations: List[StrategicRecommendation] = Field(..., description="전략적 권고안 목록")
    conclusion_and_recommendations: str = Field(..., description="결론 및 추천 사항의 전체 내용")

    sources: List[str] = Field(..., description="보고서 작성에 사용된 출처 목록")
    report_status: str = Field("Complete", description="보고서 생성 상태")
    action_command: Optional[str] = Field(None, description="실행되어야 할 특정 명령 (예: send_alert_to_admin).")