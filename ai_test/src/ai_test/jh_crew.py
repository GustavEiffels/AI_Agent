import datetime
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List
now_str = datetime.datetime.now().strftime('%y%m%d_%H%M%S')


from crewai.knowledge.source.crew_docling_source import CrewDoclingSource

content_source = CrewDoclingSource(
    file_paths=[
        "Knowledge.pdf"
    ]
)

@CrewBase
class SbtProject():
    """SbtProject crew"""

    agents: List[BaseAgent]
    tasks: List[Task]

    agents_config: dict = {}
    tasks_config: dict = {}

    @agent
    def researcher(self) -> Agent:
        return Agent(
            role="A collector who gathers information about {company}",
            goal="Based on available knowledge, gather the most up-to-date and important information about {company}, which is the target of my sales efforts.",
            backstory="You are an expert in efficiently collecting the latest and most useful information.",
            verbose=True,
            knowledge_sources=[content_source]
        )

    @agent
    def analyst(self) -> Agent:
        return Agent(
            role="An analyst who analyzes sales activities",
            goal="Based on available knowledge, refer to the {sales_activity} data and analyze the sales activities represented by {sales_activity}.",
            backstory="You analyze sales activities. You sequentially review and analyze the history of sales engagements.",
            verbose=True,
            knowledge_sources=[content_source]
        )

    @agent
    def consultant(self) -> Agent:
        return Agent(
            role="A consultant who proposes strategies for success",
            goal="Based on available knowledge, propose sales strategies by considering both customer characteristics and past sales activities.",
            backstory="""You are a consultant specialized in sales strategy.
            Your mission is to propose effective sales strategies by referring to the sales activity summaries provided by the analyst and the information gathered by the researcher.
            Recommending the most appropriate next sales action is your top priority.""",
            verbose=True,
            knowledge_sources=[content_source]
        )

    @agent
    def summarizer(self) -> Agent:
        return Agent(
            role="A sales activity analyst",
            goal="Based on available knowledge, analyze {sales_activity} data, summarize it on a weekly basis, and provide strategic insights.",
            backstory="""You are an expert with extensive experience in B2B sales strategy and data analysis.
            You excel at interpreting CRM logs, customer interactions, and bidding records to extract key issues, opportunities, and risk factors.
            Your summaries are trusted resources for executive-level strategic decision-making.""",
            verbose=True,
            knowledge_sources=[content_source]
        )



    @task
    def research_task(self) -> Task:
        return Task(
            description="Gather the most up-to-date and relevant information about the {company}.",
            expected_output="A concise and structured summary of key facts about {company}, including recent news, business focus, leadership, market status, and competitive positioning.",
            agent=self.researcher()
        )

    @task
    def analyze_task(self) -> Task:
        return Task(
            description="""Analyze and summarize the sales activities based on {sales_activity}.
            And analyze the sales activities by date.
            Finally, translate the output into Korean and convert it into JSON format.""",
            expected_output="A sequential breakdown of past {sales_activity}, highlighting customer responses, deal progress, objections, and outcomes.",
            agent=self.analyst(),
            output_file=None, # Changed to None so output is passed to context
            depends_on=['research_task']
        )

    @task
    def consulting_task(self) -> Task:
        return Task(
            description="""Based on the analyst's and researcher's outputs, develop a tailored sales strategy.
            Your output **must be a JSON object** with the following **fixed English keys** and **Korean values**:
            1.  `recommended_strategy_overview`: A concise summary of the overall strategy.
            2.  `next_best_action`: A detailed plan for the immediate next steps.
            3.  `messaging_focus`: Key messages and value propositions to emphasize.
            4.  `potential_engagement_plan`: A broader plan for future interactions.
            """,
            expected_output="""A JSON object with fixed English keys (`recommended_strategy_overview`, `next_best_action`, `messaging_focus`, `potential_engagement_plan`) and all values in Korean.
            """,
            agent=self.consultant(),
            context=[self.research_task(), self.analyze_task()],
            output_file=None, # Ensure this is None
        )
    @task
    def summarize_task(self) -> Task:
        return Task(
            description="""Based on the provided {sales_activity} data, analyze and summarize the latest sales activity data on a weekly basis.
            Your output **must be a JSON object** with the following **fixed English keys** and **Korean values**:
            1.  `weekly_sales_activity_summary`: An array of weekly summaries. Each item in this array must **only** contain:
                * `week` (English key, Korean date range value)
                * `key_milestones` (English key, Korean list of milestones)
            2.  `summary_of_recurring_risks_and_delays` (English key, Korean list of summaries)
            3.  `recommendations_and_strategic_next_actions` (English key, Korean list of recommendations)

            Ensure the summary is clear, concise, and suitable for executive-level review.
            """,
            expected_output="""A JSON object with fixed English keys (`weekly_sales_activity_summary`, `summary_of_recurring_risks_and_delays`, `recommendations_and_strategic_next_actions`) and all values in Korean.
            The `weekly_sales_activity_summary` array items must strictly contain only `week` and `key_milestones` fields.""",
            agent=self.summarizer(),
            context=[self.research_task(), self.analyze_task()],
            output_file=None,  # Set to None to return data directly instead of writing to a file
        )


    @task
    def aggregate_results_task(self) -> Task:
        return Task(
            # STRICT INSTRUCTION FOR JSON OUTPUT ONLY
            description="""Combine the outputs from the consulting task and the sales activity summary task into a single JSON object.
            The final output **MUST BE ONLY** the JSON object, with no additional text or formatting.
            The JSON object should have two top-level keys: `sales_strategy` (containing the JSON output from the consulting task) and `sales_summary` (containing the JSON output from the sales activity summary task).
            Ensure all keys are in English and all values are in Korean.
            """,
            expected_output="""A single JSON object containing two top-level keys: `sales_strategy` (the JSON output from the consulting task) and `sales_summary` (the JSON output from the summarize task).
            **IMPORTANT**: The output must be valid JSON and contain no other text.""",
            agent=self.consultant(),
            context=[self.consulting_task(), self.summarize_task()],
            output_file=None,
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=[
                self.research_task(),
                self.analyze_task(),
                self.consulting_task(),
                self.summarize_task(),
                self.aggregate_results_task()
            ],
            process=Process.sequential,
            verbose=True,
            knowledge_sources=[content_source],
        )