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
    # Agent YAML 설정은 별도의 agents.yaml 파일에 정의되어야 합니다.
    # 예: config=self.agents_config['researcher']

    @agent
    def researcher(self) -> Agent:
        return Agent(
            config=self.agents_config['researcher'], # type: ignore[index]
            # tools=[SerperDevTool()], # 필요한 도구를 여기에 직접 할당하거나 YAML에서 관리
            verbose=True
        )

    @agent
    def data_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config['data_analyst'], # type: ignore[index]
            # tools=[CodeInterpreterTool()], # 데이터 분석을 위한 도구
            verbose=True
        )
    
    @agent
    def strategist(self) -> Agent:
        return Agent(
            config=self.agents_config['strategist'], # type: ignore[index]
            # tools=[SerperDevTool()], # 전략 수립을 위한 추가 검색 도구
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
    # Task YAML 설정은 별도의 tasks.yaml 파일에 정의되어야 합니다.
    # 예: config=self.tasks_config['research_task']

    @task
    def research_task(self) -> Task:
        return Task(
            config=self.tasks_config['research_task'], # type: ignore[index]
        )

    @task
    def data_analysis_task(self) -> Task:
        return Task(
            config=self.tasks_config['data_analysis_task'], # type: ignore[index]
            context=[self.research_task()] # 연구 결과를 분석 태스크의 컨텍스트로 전달
        )

    @task
    def strategy_development_task(self) -> Task:
        return Task(
            config=self.tasks_config['strategy_development_task'], # type: ignore[index]
            context=[
                self.research_task(),      # 연구 결과
                self.data_analysis_task()  # 데이터 분석 결과
            ] # 연구 및 분석 결과를 전략 개발 태스크의 컨텍스트로 전달
        )

    @task
    def reporting_task(self) -> Task:
        return Task(
            config=self.tasks_config['reporting_task'], # type: ignore[index]
            output_file='report.md',
            context=[
                self.research_task(),         # 연구 결과
                self.data_analysis_task(),    # 데이터 분석 결과
                self.strategy_development_task() # 전략 개발 결과
            ] 
        )
    
    @task
    def translation_task(self) -> Task:
        return Task(
            config=self.tasks_config['translation_task'], # type: ignore[index]
            output_file='report_korean.md',
            context=[self.reporting_task()] # reporting_task의 최종 영문 보고서를 번역 태스크의 컨텍스트로 전달
        )

    @crew
    def crew(self) -> Crew:
        """Creates the CrewAiDemo comprehensive business analysis crew"""

        return Crew(
            agents=[
                self.researcher(),
                self.data_analyst(),
                self.strategist(),
                self.reporting_analyst(),
                self.translator()
            ],
            tasks=[
                self.research_task(),
                self.data_analysis_task(),
                self.strategy_development_task(),
                self.reporting_task(),
                self.translation_task()
            ],
            process=Process.sequential, # 태스크들을 순차적으로 실행
            verbose=True,

        )