from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List

@CrewBase
class CrewAiDemo():
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

    @agent # NEW AGENT
    def news_researcher(self) -> Agent:
        return Agent(
            config=self.agents_config['news_researcher'], # type: ignore[index]
            verbose=True
        )

    @agent # NEW AGENT
    def json_formatter(self) -> Agent:
        return Agent(
            config=self.agents_config['json_formatter'], # type: ignore[index]
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

    @task
    def financial_analysis_task(self) -> Task:
        return Task(
            config=self.tasks_config['financial_analysis_task'], # type: ignore[index]
        )

    @task # NEW TASK
    def news_research_task(self) -> Task:
        return Task(
            config=self.tasks_config['news_research_task'], # type: ignore[index]
            # No direct context from other tasks needed, as it will get company_name from initial inputs.
        )

    @task
    def strategy_development_task(self) -> Task:
        return Task(
            config=self.tasks_config['strategy_development_task'],  # type: ignore[index]
            context=[
                self.research_task(),
                self.data_analysis_task(),
                self.financial_analysis_task(),
                self.news_research_task()  # ADDED CONTEXT
            ]
        )


    @task
    def reporting_task(self) -> Task:
        return Task(
            config=self.tasks_config['reporting_task'], # type: ignore[index]
            output_file='report.md', # This will still output a markdown report
            context=[
                self.research_task(),
                self.data_analysis_task(),
                self.financial_analysis_task(),
                self.news_research_task(), # ADDED CONTEXT
                self.strategy_development_task()
            ]
        )

    @task
    def translation_task(self) -> Task:
        return Task(
            config=self.tasks_config['translation_task'], # type: ignore[index]
            output_file='report_korean.md',
            context=[self.reporting_task()]
        )

    @task # NEW TASK
    def json_output_task(self) -> Task:
        return Task(
            config=self.tasks_config['json_output_task'], # type: ignore[index]
            # The agent needs to see the full English report and financial details
            context=[self.reporting_task(), self.financial_analysis_task()],
            output_file='report.json' # Output the final JSON here
        )

    @crew
    def crew(self) -> Crew:
        """Creates the CrewAiDemo comprehensive business analysis crew"""

        return Crew(
            agents=[
                self.researcher(),
                self.data_analyst(),
                self.financial_analyst(),
                self.news_researcher(),  # ADDED AGENT
                self.strategist(),
                self.reporting_analyst(),
                self.translator(),
                self.json_formatter()  # ADDED AGENT
            ],
            tasks=[
                self.research_task(),
                self.data_analysis_task(),
                self.financial_analysis_task(),
                self.news_research_task(),  # ADDED TASK
                self.strategy_development_task(),
                self.reporting_task(),
                self.translation_task(),  # Keep translation task if Korean report is also needed
                self.json_output_task()
                # ADDED TASK - make sure this is the LAST task if you want its output as final result
            ],
            process=Process.sequential,
            verbose=True,
        )