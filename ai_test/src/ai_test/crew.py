from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task, output_pydantic
from .tools.dart_tool import CollectFinancialDataTool
from .tools.naver_tool import NaverSearchDataTool
from .tools.yahoo_tool import YahooFinanceDataTool
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
                NaverSearchDataTool()
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
    def financial_task(self) -> Task:
        return Task(
            config=self.tasks_config['financial_task'],
            output_file='financial_task.md'
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
                self.reporting_analyst()
            ],
            tasks=[
                self.research_task(),
                self.financial_task(),
                self.reporting_task()
            ],
            process=Process.sequential,
            verbose=True,
        )