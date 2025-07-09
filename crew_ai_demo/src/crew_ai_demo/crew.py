from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List

# 필요한 경우 여기에 CrewAI Tools를 import합니다.
# from crewai_tools import SerperDevTool, CodeInterpreterTool # 예시

@CrewBase
class CrewAiDemo():
    """CrewAiDemo crew for comprehensive business analysis"""

    agents: List[BaseAgent]
    tasks: List[Task]

    # --- Agent Definitions ---
    @agent
    def researcher(self) -> Agent:
        return Agent(
            config=self.agents_config['researcher'], # type: ignore[index]
            verbose=True
        )

    @agent
    def data_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config['data_analyst'], # type: ignore[index]
            verbose=True
        )

    @agent # NEW AGENT
    def financial_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config['financial_analyst'], # type: ignore[index]
            # tools=[YourFinancialToolHere()], # Consider adding a tool for fetching financial data
            verbose=True
        )

    @agent
    def strategist(self) -> Agent:
        return Agent(
            config=self.agents_config['strategist'], # type: ignore[index]
            # tools=[SerperDevTool()],
            verbose=True
        )

    @agent
    def reporting_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config['reporting_analyst'], # type: ignore[index]
            verbose=True
        )

    @agent
    def translator(self) -> Agent:
        return Agent(
            config=self.agents_config['translator'], # type: ignore[index]
            verbose=True
        )

    # --- Task Definitions ---
    @task
    def research_task(self) -> Task:
        return Task(
            config=self.tasks_config['research_task'], # type: ignore[index]
        )

    @task
    def data_analysis_task(self) -> Task:
        return Task(
            config=self.tasks_config['data_analysis_task'], # type: ignore[index]
            context=[self.research_task()]
        )

    @task # NEW TASK
    def financial_analysis_task(self) -> Task:
        return Task(
            config=self.tasks_config['financial_analysis_task'], # type: ignore[index]
            # Context for this task will likely come from direct input,
            # not from other CrewAI tasks in this specific setup.
        )

    @task
    def strategy_development_task(self) -> Task:
        return Task(
            config=self.tasks_config['strategy_development_task'], # type: ignore[index]
            context=[
                self.research_task(),
                self.data_analysis_task(),
                self.financial_analysis_task() # UPDATED CONTEXT
            ]
        )

    @task
    def reporting_task(self) -> Task:
        return Task(
            config=self.tasks_config['reporting_task'], # type: ignore[index]
            output_file='report.md',
            context=[
                self.research_task(),
                self.data_analysis_task(),
                self.financial_analysis_task(), # UPDATED CONTEXT
                self.strategy_development_task()
            ]
        )

    @task
    def translation_task(self) -> Task:
        return Task(
            config=self.tasks_config['translation_task'],
            output_file='report_korean.md',
            context=[self.reporting_task()]
        )

    @crew
    def crew(self) -> Crew:
        """Creates the CrewAiDemo comprehensive business analysis crew"""
        return Crew(
            agents=[
                self.researcher(),
                self.data_analyst(),
                self.financial_analyst(),
                self.strategist(),
                self.reporting_analyst(),
                self.translator()
            ],
            tasks=[
                self.research_task(),
                self.data_analysis_task(),
                self.financial_analysis_task(),
                self.strategy_development_task(),
                self.reporting_task(),
                self.translation_task()
            ],
            process=Process.sequential,
            verbose=True,
        )