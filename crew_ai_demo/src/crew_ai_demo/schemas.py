from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

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


# --- 단순화된 일반 섹션 DTO (title 필드 추가!) ---
class GeneralSectionContent(BaseModel):
    """일반적인 보고서 섹션의 내용을 담는 DTO. 큰 제목과 내용을 포함."""
    title: str = Field(..., description="섹션의 제목 (예: '서론', '엔비디아 개요')") # <-- 여기에 title 추가
    content: str = Field(..., description="해당 섹션의 전체 내용 문자열")

# --- Recent News DTOs (유지) ---
class NewsItem(BaseModel):
    date: str = Field(..., description="뉴스 날짜 (YYYY-MM-DD)")
    source: str = Field(..., description="뉴스 출처")
    headline: str = Field(..., description="뉴스 헤드라인")
    summary: str = Field(..., description="뉴스 요약")
    url: str = Field(..., description="뉴스 기사 URL")


# --- Full Report DTO (메인 구조 유지) ---
class FullAnalysisReport(BaseModel):
    """종합 보고서 구조 (재무 외 섹션은 단순화)."""
    executive_summary: str = Field(..., description="경영진 요약")
    introduction: GeneralSectionContent = Field(..., description="서론")
    company_overview: GeneralSectionContent = Field(..., description="엔비디아 개요")
    products_and_technology_analysis: GeneralSectionContent = Field(..., description="제품 및 기술 분석")
    market_status_and_competition: GeneralSectionContent = Field(..., description="시장 현황 및 경쟁 환경")
    financial_analysis: FinancialAnalysisSection # 복잡한 재무 구조 유지
    key_risk_factors: GeneralSectionContent = Field(..., description="주요 위험 요소")
    recent_news: List[NewsItem] = Field(..., description="최신 뉴스 목록")
    conclusion_and_recommendations: GeneralSectionContent = Field(..., description="결론 및 추천 사항")

    sources: List[str] = Field(..., description="보고서 작성에 사용된 출처 목록")
    report_status: str = Field("Complete", description="보고서 생성 상태")
    action_command: Optional[str] = Field(None, description="실행되어야 할 특정 명령 (예: send_alert_to_admin).")