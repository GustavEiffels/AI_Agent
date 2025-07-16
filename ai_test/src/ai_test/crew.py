from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task, output_pydantic
from .tools.dart_tool import CollectFinancialDataTool, ReadAndDeleteXmlFileTool
from .tools.naver_tool import NaverSearchDataTool
from .tools.yahoo_tool import YahooFinanceDataTool, YahooFinanceNewsDataTool
from .tools.goolge_search_tool import GoogleSearchTickerTool

@CrewBase
class AiTest():
    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    @agent
    def researcher(self) -> Agent:
        return Agent(
            config=self.agents_config['researcher'],
            verbose=True,
            tools=[
                NaverSearchDataTool(),
                GoogleSearchTickerTool(),
                YahooFinanceNewsDataTool()
            ]
        )

    @agent
    def financial_analyst(self) -> Agent:
        pass
        return Agent(
            config=self.agents_config['financial_analyst'],
            verbose=True,
            tools=[
                CollectFinancialDataTool(),
                GoogleSearchTickerTool(),
                YahooFinanceDataTool()
            ]
        )

    @agent
    def document_parser(self) -> Agent:
        return Agent(
            config=self.agents_config['document_parser'],
            verbose=True,
            tools=[
                ReadAndDeleteXmlFileTool()
            ]
        )

    @agent
    def news_collector(self) -> Agent:
        pass
        return Agent(
            config=self.agents_config['news_collector'],
            verbose=True,
            tools=[
                NaverSearchDataTool(),
                YahooFinanceNewsDataTool()
            ]
        )

    @agent
    def reporting_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config['reporting_analyst'],
            verbose=True
        )

    @task
    def research_task(self) -> Task:
        return Task(
            config=self.tasks_config['research_task'],
            output_file='research_resport.md'
        )

    @task
    def financial_data_collection_task(self) -> Task:
        return Task(
            config=self.tasks_config['financial_data_collection_task'],
            agent=self.financial_analyst(),
            context=[]
        )

    @task
    def document_parsing_task(self) -> Task:
        return Task(
            config=self.tasks_config['document_parsing_task'],
            agent=self.document_parser(),
            context=[self.financial_data_collection_task()]
        )

    @task
    def financial_analysis_task(self) -> Task:
        return Task(
            config=self.tasks_config['financial_analysis_task'],
            agent=self.financial_analyst(),
            context=[self.financial_data_collection_task(), self.document_parsing_task()]
        )

    @task
    def news_collection_task(self) -> Task:
        return Task(
            config=self.tasks_config['news_collection_task'],
            output_file='news_[company_name].md'
        )

    @task
    def reporting_task(self) -> Task:
        return Task(
            config=self.tasks_config['reporting_task'],
            output_file='comprehensive_report_{topic}.json',
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=[
                self.researcher(),
                self.financial_analyst(),
                self.news_collector(),
                self.reporting_analyst(),
                self.document_parser()
            ],
            tasks=[
                self.financial_data_collection_task(),
                self.document_parsing_task(),
                self.financial_analysis_task(),
                self.research_task(),
                self.news_collection_task(),
                self.reporting_task()
            ],
            process=Process.sequential,
            verbose=True,
        )