# crew.py
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task # project 모듈에서 필요한 것들을 임포트
from crewai.agents.agent_builder.base_agent import BaseAgent
from .tools.dart_tool import CollectFinancialDataTool 
from typing import List

@CrewBase
class AiTest():
    """AiTest crew"""

    @agent 
    def researcher(self) -> Agent:
        return Agent(
            config=self.agents_config['researcher'], 
            verbose=True
        )

    @agent
    def financial_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config['financial_analyst'], 
            verbose=True,
            tools=[
                CollectFinancialDataTool()
            ]            
        )

    @agent
    def reporting_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config['reporting_analyst'], # type: ignore[index]
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
            output_file='reporting_task.md'
        ) 

    @crew
    def crew(self) -> Crew:
        """Creates the CrewAiDemo comprehensive business analysis crew"""

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