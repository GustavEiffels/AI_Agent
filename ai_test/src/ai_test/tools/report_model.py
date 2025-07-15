from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class FinancialDataByQuarterEntry(BaseModel):
    revenue: Optional[float] = None
    operating_income: Optional[float] = None
    net_income: Optional[float] = None
    asset_moveable: Optional[float] = None
    asset_unmoveable: Optional[float] = None
    amount_asset: Optional[float] = None
    bet_moveable: Optional[float] = None
    bet_unmoveable: Optional[float] = None
    amount_bet: Optional[float] = None
    amount_asset_equity: Optional[float] = None


class FinancialKeyTrends(BaseModel):
    revenue_trend: Optional[str] = None
    operating_income_trend: Optional[str] = None
    net_income_trend: Optional[str] = None
    asset_liability_structure_trend: Optional[str] = None
    cash_flow_outlook_trend: Optional[str] = None


class FinancialAnalysisOutput(BaseModel):
    company_name: str
    financial_data_by_quarter: Optional[Dict[str, FinancialDataByQuarterEntry]] = None
    key_trends: Optional[FinancialKeyTrends] = None
    financial_outlook: Optional[str] = None
    risks_and_opportunities: Optional[List[str]] = None

class FinancialAnalysisNotApplicable(BaseModel):
    company_name: str
    status: str
    reason: str

class RisksAndOpportunities(BaseModel):
    risks: str = Field(description="주요 위험 요인에 대한 설명")
    opportunities: str = Field(description="주요 기회 요인에 대한 설명")

class ComprehensiveReportOutput(BaseModel):
    company_overview: str = Field(description="기업 개요에 대한 요약")
    latest_trends_and_strategy: str = Field(description="최신 주요 동향 및 전략에 대한 설명")
    business_direction: str = Field(description="비즈니스 방향성에 대한 설명")

    detailed_financial_analysis: Optional[Dict[str, Any]] = Field(
        None, description="이전 financial_task에서 생성된 원본 상세 재무 분석 JSON 결과"
    )

    financial_performance_and_analysis: str = Field(description="재무 성과 및 분석에 대한 종합적인 설명")
    revenue_and_profitability_trends: str = Field(description="매출 및 수익성 동향에 대한 분석")
    asset_and_liability_structure: str = Field(description="자산 및 부채 구조에 대한 분석")
    financial_outlook_and_cash_flow: str = Field(description="재무 전망 및 현금 흐름에 대한 분석")
    risks_and_opportunities: RisksAndOpportunities = Field(description="주요 위험 요인 및 기회 요인")
    social_responsibility_and_contribution: str = Field(description="사회적 책임 및 사회 공헌 활동에 대한 설명")
    conclusion: str = Field(description="보고서의 결론")

    status: Optional[str] = Field(None, description="전체 보고서의 상태 (예: 'complete', 'not_applicable')")
    reason: Optional[str] = Field(None, description="보고서가 불완전하거나 적용되지 않는 경우의 사유")
