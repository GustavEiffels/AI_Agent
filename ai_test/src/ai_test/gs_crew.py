import os

from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List

os.environ["HF_HUB_DISABLE_SYMLINKS"] = "1"
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

from .tools.sf_create_template import SalesforceEmailTemplateTool
from crewai.knowledge.source.crew_docling_source import CrewDoclingSource

content_source = CrewDoclingSource(
    file_paths=[
        "Knowledge.pdf"
    ]
)

@CrewBase
class AbmAi():

    agents: List[BaseAgent]
    tasks: List[Task]

    agents_config: dict = {}
    tasks_config: dict = {}


    @agent
    def gs_company_researcher(self) -> Agent:
        return Agent(
            role="Research Analyst for {AccountName}",
            goal="Use Google to find recent, accurate, and relevant business information about {AccountName}.",
            backstory="""You specialize in researching real-world companies using online tools.
            Your task is to discover detailed facts, services, and news about {AccountName} in the {Industry} industry.""",
            verbose=True
        )

    @agent
    def gs_insight_extractor(self) -> Agent:
        return Agent(
            role="Strategic Insight Analyst",
            goal="Extract useful marketing insights from company research",
            backstory="""You analyze raw company data to identify potential entry points and angles for strategic outreach.
            You focus on buyer personas, market positioning, product mix, and recent business activity of companies like {AccountName}.""",
            verbose=True
        )

    @agent
    def gs_strategy_designer(self) -> Agent:
        return Agent(
            role="ABM Strategy Specialist",
            goal="Build a marketing strategy specific to {AccountName}'s needs and structure",
            backstory="""You specialize in crafting personalized account-based marketing strategies using real company insights.
            Your goal is to provide highly relevant and targeted recommendations that resonate with decision makers at {AccountName}.
            You **must use information from the internal knowledge base** about SBTGlobal’s Salesforce services and experience to craft a relevant, targeted ABM message.""",
            verbose=True,
            knowledge_sources=[content_source]
        )

    @agent
    def gs_content_creator(self) -> Agent:
        return Agent(
            role="B2B Marketing Copywriter",
            goal="Write outreach content aligned with the ABM strategy",
            backstory="""You turn marketing plans into persuasive content such as emails, pitch blurbs, or proposals to appeal to companies like {AccountName}.
            You **must use information from the internal knowledge base** about SBTGlobal’s Salesforce services and experience to craft a relevant, targeted ABM message.""",
            verbose=True,
            knowledge_sources=[content_source]
        )

    @agent
    def gs_translator(self) -> Agent:
        return Agent(
            role="Translator",
            goal="Translate English text to Korean accurately and naturally, excluding any hyperlinks (such as website URLs, LinkedIn, blog links, etc.).",
            backstory="""You are a professional translator fluent in both English and Korean, with expertise in technical and business texts.""",
            verbose=True
        )

    @agent
    def gs_email_template_saver(self) -> Agent:
        tool = SalesforceEmailTemplateTool()
        return Agent(
            role="Salesforce Email Template Creator",
            goal="Save ABM report content as a Salesforce Classic Email Template.",
            backstory="""You're a Salesforce-savvy assistant specialized in saving ABM campaign content
            directly into Salesforce as Classic Email Templates for use in future outreach.""",
            verbose=True,
            tools=[tool]
        )

    @task
    def gs_research_company(self) -> Task:
        return Task(
            description="""You are researching the company {AccountName} in the {Industry} industry.
            Use the following real-time search results as your primary data source:
            {Search_Data}

            Extract concrete business activities, products, technologies, or any partnerships from the result.
            Summarize findings in bullet points.""",
            expected_output="A bullet list of 5-10 key facts about {AccountName} based on real search results.",
            agent=self.gs_company_researcher() # <-- Agent 메서드를 직접 호출하여 Agent 객체를 전달
        )

    @task
    def gs_extract_insights(self) -> Task:
        return Task(
            description="""From the information gathered about {AccountName}, extract useful marketing insights.
            Consider what their pain points or priorities might be based on their size, industry, or business context.""",
            expected_output="A list of 3-5 potential insights or entry points for a marketing team looking to engage with {AccountName}.",
            agent=self.gs_insight_extractor(), # <-- Agent 메서드를 직접 호출
            depends_on=['gs_research_company']
        )

    @task
    def gs_design_strategy(self) -> Task:
        return Task(
            description="""Based on the insights from {AccountName}, create a tailored account-based marketing strategy.
            Recommend messaging type, tone, delivery channels, and suggested campaign ideas.""",
            expected_output="A short strategic plan (in 3+ bullets or paragraphs) including audience targeting, messaging direction, and tactics.",
            agent=self.gs_strategy_designer(), # <-- Agent 메서드를 직접 호출
            depends_on=['gs_extract_insights']
        )

    @task
    def gs_write_content(self) -> Task:
        return Task(
            description="""Write a sample outreach email or brief proposal that could be sent to {AccountName}.
            Use the strategy as context to ensure alignment with their needs and tone.""",
            expected_output="A marketing email draft (or equivalent outreach content) addressed to {AccountName}, including a subject and body.",
            agent=self.gs_content_creator(), # <-- Agent 메서드를 직접 호출
            depends_on=['gs_design_strategy']
        )

    @task
    def gs_finalize_report(self) -> Task:
        return Task(
            description="""Compile all outputs—analysis, strategy, and content—into a report for {AccountName}.
            Prepare the result to be either shared with the sales team or uploaded to Salesforce.""",
            expected_output="A markdown-formatted report for {AccountName} that includes: industry insights, strategy recommendations, and finalized email content, clearly separated by section.",
            agent=self.gs_content_creator(), # <-- Agent 메서드를 직접 호출
            output_file='report.md'
        )

    @task
    def gs_translate_task(self) -> Task:
        return Task(
            description="""Translate only the final marketing content (email body and subject) into Korean.
            Do not include strategy, report, or bullet-point insights.""",
            expected_output="A clean, Korean-language version of only the email outreach content, formatted in HTML, suitable for use as a Salesforce Classic Email Template.",
            agent=self.gs_translator(), # <-- Agent 메서드를 직접 호출
            output_key='abm_html_report',
            depends_on=['gs_finalize_report']
        )

    @task
    def gs_save_abm_template(self) -> Task:
        return Task(
            description="""Save the **translated outreach content** into Salesforce as a Classic Email Template
                under the 'Public Templates' folder.

                Use the following template values:
                - Template Name: ABM_Template_{{inputs.AccountName | slugify}} # <--- 중요한 변경 부분
                - Subject: {AccountName} ABM Strategy Report
                - HTML Body: {{ abm_html_report }}

                Important: Only use the outreach email (subject and body) as the HTML content.
                Do not include analysis, insights, or strategy.""",
            expected_output="Confirmation message and template ID after saving to Salesforce.",
            agent=self.gs_email_template_saver(),
            depends_on=['gs_translate_task']
        )
    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
            knowledge_sources=[content_source],
        )