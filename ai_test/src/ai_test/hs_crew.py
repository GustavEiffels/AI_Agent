from crewai import Agent, Crew, Process, Task
from typing import List
from crewai.project import CrewBase, agent, crew, task
import os
from dotenv import load_dotenv
from datetime import datetime
from .tools.salesforce_connection_tool import SalesforceExtractTool
from crewai.agents.agent_builder.base_agent import BaseAgent

load_dotenv()

OUTPUTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), 'outputs'))


@CrewBase
class SalesforceCrewai():
    agents: List[BaseAgent]
    tasks: List[Task]

    agents_config: dict = {}
    tasks_config: dict = {}


    def __init__(self):
        # 모든 outputs 디렉토리 미리 생성 (절대 경로)
        os.makedirs(os.path.join(OUTPUTS_DIR, 'salesforce_connector'), exist_ok=True)
        os.makedirs(os.path.join(OUTPUTS_DIR, 'data_analyzer'), exist_ok=True)
        os.makedirs(os.path.join(OUTPUTS_DIR, 'summary_generator'), exist_ok=True)
        os.makedirs(os.path.join(OUTPUTS_DIR, 'translator'), exist_ok=True)
        os.makedirs(os.path.join(OUTPUTS_DIR, 'report_creator'), exist_ok=True)

        self.current_year = datetime.now().year
        self.current_month = datetime.now().month

    @agent
    def salesforce_connector(self) -> Agent:
        return Agent(
            role="Salesforce Data Extraction Expert",
            goal="Securely and efficiently extract required data from Salesforce CRM",
            backstory="You are a Salesforce API specialist, using simple-salesforce to query and retrieve data. You handle connections with security tokens and instance URLs, converting results to pandas DataFrames without errors.",
            verbose = True,
            tools=[SalesforceExtractTool()]
        )

    @agent
    def data_analyzer(self) -> Agent:
        return Agent(
            role="Data Analysis and Categorization Expert",
            goal="Analyze extracted data and classify into sales, marketing, and customer service categories",
            backstory="You are an expert in pandas and scikit-learn, but primarily use GPT-4.1-mini-2025-04-14 AI to perform analysis, clustering, and keyword extraction intelligently, minimizing manual coding.",
            verbose = True
        )

    @agent
    def summary_generator(self) -> Agent:
        return Agent(
            role="AI-Based Data Summary Expert",
            goal="Transform analyzed data into concise and useful summaries",
            backstory="You rely on GPT-4.1-mini-2025-04-14 AI for all summarization, using its NLP capabilities to generate insights without requiring user-coded logic.",
            verbose = True
        )

    @agent
    def translator(self) -> Agent:
        return Agent(
            role="English to Korean Translation Expert",
            goal="Accurately translate English summaries and reports into natural Korean",
            backstory="You use GPT-4.1-mini-2025-04-14 AI exclusively for translations, ensuring context-aware and professional results without any manual code implementation.",
            verbose = True
        )

    @agent
    def report_creator(self) -> Agent:
        return Agent(
            role="Report and Output Generation Expert",
            goal="Compile summaries into PDF reports integrable with Salesforce",
            backstory="You generate reports with reportlab, but embed GPT-4.1-mini-2025-04-14 AI outputs directly for content, focusing on visualization.",
            verbose = True
        )

    @task
    def data_extract_task(self) -> Task:
        return Task(
            description=(
                f"Connect to Salesforce and query Account, Lead, Opportunity, and User. "
                f"Use SOQL to extract data created in the last year (up to {self.current_year}). "
                f"Additionally, extract the **exact count of Accounts, Leads, and Opportunities created in the current month ({self.current_year}-{self.current_month:02d})**. "  # 이번 달 생성 건수 추출 지시 추가
                f"Utilize environment variables for connection. Store all results as pandas DataFrames. "
                f"Example SOQL for last year: SELECT Id, Name, Email, Status FROM Lead WHERE CreatedDate > LAST_YEAR. "
                f"Example SOQL for current month count: SELECT COUNT(Id) FROM Account WHERE CreatedDate = THIS_MONTH."
            ),
            expected_output="Data summary (head(10), shape), category counts.",
            agent=self.salesforce_connector(),
            output_file="outputs/salesforce_connector/extracted_data_{current_year}.csv"
        )

    @task
    def data_analysis_task(self) -> Task:
        return Task(
            description="Load the CSV file from outputs/salesforce_connector/extracted_data_{current_year}.csv using pandas. Clean the data with pandas (handle missing values, convert dates). Do NOT re-query Salesforce; analyze only the loaded CSV data. Use GPT-4.1-mini-2025-04-14 AI to perform clustering, categorization (sales/marketing/service), and trend analysis for {current_year}. Let the AI handle keyword extraction and stats computation intelligently via natural language prompts, without manual coding. Focus on {current_year} trends, such as quarterly growth in the current year.",
            expected_output="Categorized lists (5 samples/category), 10 bullet points of AI-generated stats for {current_year}, clustering summary.",
            agent=self.data_analyzer(),
            output_file="outputs/data_analyzer/analysis_results_{current_year}.json"
        )

    @task
    def summary_generation_task(self) -> Task:
        return Task(
            description="Load the analysis JSON from outputs/data_analyzer/analysis_results_{current_year}.json. Use GPT-4.1-mini-2025-04-14 AI to summarize data by category, "
                        "generating natural language insights for {current_year} trends. Focus on business decisions; AI handles entity recognition and content creation fully, "
                        "labeling all insights as {current_year} data. expected_output: >",
            expected_output="AI-generated bullet points (10 total) for {current_year}, one paragraph summarizing {current_year} insights.",
            agent=self.summary_generator(),
            output_file="outputs/summary_generator/summary_{current_year}.md"
        )

    @task
    def translation_task(self) -> Task:
        return Task(
            description=(
                f"Load the analysis JSON from {os.path.join(OUTPUTS_DIR, 'data_analyzer', f'analysis_results_{self.current_year}.json')}. "
                f"Use GPT-4.1-mini-2025-04-14 AI to summarize data by category, generating natural language insights for {self.current_year} trends. "
                f"Focus on business decisions; AI handles entity recognition and content creation fully, labeling all insights as {self.current_year} data. "
                f"**The summary MUST be a JSON formatted string, representing a Python list of concise insights/paragraphs. "
                f"Each element in the list should be a string. Example: '[\"Insight 1.\", \"Insight 2.\", \"Paragraph insight goes here.\"]'**" # JSON 형식으로 출력 명시
            ),
            expected_output=(
                f"A JSON formatted string representing a list of concise AI-generated insights for {self.current_year}, "
                f"like: '[\"Insight 1.\", \"Insight 2.\", \"Paragraph insight goes here.\"]'" # JSON 형식 예시
            ),
            agent=self.translator(),
            output_file=None
        )


    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=[self.salesforce_connector(), self.data_analyzer(), self.summary_generator(), self.translator(),
                    self.report_creator()],
            tasks=[self.data_extract_task(), self.data_analysis_task(), self.summary_generation_task(),
                   self.translation_task()],
            process=Process.sequential
        )

    def run(self, inputs=None):
        try:
            result = self.crew().kickoff(inputs=inputs or {})
            print(f"Crew completed: {result}")
            return result
        except Exception as e:
            print(f"Error in Crew execution: {str(e)}")
            raise