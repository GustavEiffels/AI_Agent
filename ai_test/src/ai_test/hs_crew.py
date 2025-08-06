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
        # 모든 outputs 디렉토리 강제 생성
        for folder in ['salesforce_connector', 'data_analyzer', 'summary_generator', 'translator', 'report_creator']:
            os.makedirs(os.path.join(OUTPUTS_DIR, folder), exist_ok=True)

        self.current_year = datetime.now().year
        self.current_month = datetime.now().month

    @agent
    def salesforce_connector(self) -> Agent:
        return Agent(
            role="Salesforce Data Extraction Expert",
            goal="Extract Account and Opportunity data from Salesforce CRM for sales analysis",
            backstory=(
                "You are a Salesforce API specialist using simple-salesforce to query and retrieve "
                "Account and Opportunity data. You securely connect using environment variables and "
                "save results to CSV without errors."
            ),
            verbose=True,
            tools=[SalesforceExtractTool()]
        )

    @agent
    def data_analyzer(self) -> Agent:
        return Agent(
            role="Sales Data Analysis Expert",
            goal="Analyze Account and Opportunity CSV files to produce factual sales-related statistics only",
            backstory=(
                "You are a sales data analysis specialist. You only work with Account and Opportunity datasets "
                "from Salesforce. You compute statistics such as total accounts, top industries, total opportunities, "
                "revenue totals, and stage distributions for the given year. You never perform marketing or service analysis "
                "and never fabricate results."
            ),
            verbose=True
        )

    @agent
    def summary_generator(self) -> Agent:
        return Agent(
            role="AI-Based Data Summary Expert",
            goal="Convert factual sales statistics into a concise English summary paragraph",
            backstory="You use GPT only for summarization, not for generating or fabricating data.",
            verbose=True
        )

    @agent
    def translator(self) -> Agent:
        return Agent(
            role="English to Korean Translation Expert",
            goal="Translate the English sales summary into accurate Korean, preserving business terms",
            backstory="You translate summaries using GPT, ensuring consistent terminology like Opportunity=기회, Account=고객사.",
            verbose=True
        )

    @agent
    def report_creator(self) -> Agent:
        return Agent(
            role="Report and Output Generation Expert",
            goal="Compile translated summaries into text-based PDF reports",
            backstory="You generate simple PDFs with text only, no charts or graphics.",
            verbose=True
        )

    @task
    def data_extract_task(self) -> Task:
        return Task(
            description=(
                f"Connect to Salesforce and query only Account and Opportunity objects. "
                f"Extract data created in the last year (up to {self.current_year}). "
                f"For Account: SELECT Id, Name, Industry, CreatedDate FROM Account WHERE CreatedDate >= 2025-01-01T00:00:00Z "
                f"For Opportunity: SELECT Id, Name, StageName, Amount, CloseDate, AccountId FROM Opportunity WHERE CreatedDate >= 2025-01-01T00:00:00Z "
                f"Save each as separate CSV files in outputs/salesforce_connector/. "
                f"Do not include Leads or Users."
            ),
            expected_output="Two CSV files: Account_data_{current_year}.csv and Opportunity_data_{current_year}.csv",
            agent=self.salesforce_connector(),
            output_file=f"outputs/salesforce_connector/Account_data_{self.current_year}.csv"
        )

    @task
    def data_analysis_task(self) -> Task:
        return Task(
            description=(
                f"Load both CSV files: outputs/salesforce_connector/Account_data_{self.current_year}.csv "
                f"and outputs/salesforce_connector/Opportunity_data_{self.current_year}.csv using pandas. "
                f"Clean the data (handle missing values, convert dates). "
                f"Compute and output factual and verifiable sales-related statistics for {self.current_year} "
                f"in a structured JSON format with separate keys for each metric category:\n"
                f"- 'account_summary': Total number of Accounts created and Top 5 Industries by count.\n"
                f"- 'opportunity_summary': Total Opportunities closed, total & average Opportunity Amount (USD).\n"
                f"- 'stage_distribution': Count of Opportunities by StageName.\n"
                f"- 'quarterly_revenue': Total Opportunity revenue (USD) per quarter.\n"
                f"Ensure numeric formatting is consistent (commas for thousands, 2 decimal places for currency). "
                f"No clustering, keyword extraction, or speculative analysis — only values calculated directly from the CSV data."
            ),
            expected_output=(
                f"Structured JSON file for {self.current_year} containing keys: "
                f"'account_summary', 'opportunity_summary', 'stage_distribution', 'quarterly_revenue'."
            ),
            agent=self.data_analyzer(),
            output_file=f"outputs/data_analyzer/analysis_results_{self.current_year}.json"
        )

    @task
    def summary_generation_task(self) -> Task:
        return Task(
            description=(
                f"Load the plain text analysis from outputs/data_analyzer/analysis_results_{self.current_year}.txt. "
                f"Using only the computed statistics, produce a concise, professional business summary in English "
                f"as a valid JSON object with three keys: 'Analysis', 'Conclusion', and 'Strategy'.\n"
                f"- 'Analysis': Detailed factual summary of the statistics, in executive report style.\n"
                f"- 'Conclusion': Key insights and implications from the analysis.\n"
                f"- 'Strategy': Recommended actions or next steps based on the conclusion.\n"
                f"Example output:\n"
                f"{{\n"
                f'  "Analysis": "In {self.current_year}, a total of ...",\n'
                f'  "Conclusion": "The sales performance indicates ...",\n'
                f'  "Strategy": "Focus on expanding high-performing industries ..."\n'
                f"}}"
            ),
            expected_output=f"JSON object with keys 'Analysis', 'Conclusion', and 'Strategy' for {self.current_year}.",
            agent=self.summary_generator(),
            output_file=f"outputs/summary_generator/summary_{self.current_year}.json"
        )

    @task
    def translation_task(self) -> Task:
        return Task(
            description=(
                f"Load the JSON file from outputs/summary_generator/summary_{self.current_year}.json. "
                f"Translate each value into Korean, keeping the same JSON structure with keys 'analysis', 'conclusion', and 'strategy'. "
                f"Preserve all numbers and business terms accurately "
                f"(Opportunity=기회, Account=고객사, Industry=산업, revenue=수익). "
                f"The final output must be a raw, valid JSON string, without any additional text, explanations, or markdown fences like '```json'."
            ),
            expected_output=(
                f"A raw JSON string with keys 'analysis', 'conclusion', and 'strategy' for {self.current_year}, containing the translated summary. "
                f"The output must not be wrapped in markdown fences or other formatting."
            ),
            agent=self.translator(),
            output_file=f"outputs/translator/translated_summary_{self.current_year}.json"
        )


    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=[
                self.salesforce_connector(),
                self.data_analyzer(),
                self.summary_generator(),
                self.translator(),
                self.report_creator()
            ],
            tasks=[
                self.data_extract_task(),
                self.data_analysis_task(),
                self.summary_generation_task(),
                self.translation_task()
            ],
            process=Process.sequential
        )

    def run(self, inputs=None):
        try:
            # 항상 폴더 체크 및 생성
            for folder in ['salesforce_connector', 'data_analyzer', 'summary_generator', 'translator', 'report_creator']:
                os.makedirs(os.path.join(OUTPUTS_DIR, folder), exist_ok=True)

            result = self.crew().kickoff(inputs=inputs or {})
            print(f"Crew completed: {result}")
            return result
        except Exception as e:
            print(f"Error in Crew execution: {str(e)}")
            raise