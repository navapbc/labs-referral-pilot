import json
import logging
from pprint import pformat

import hayhooks
from hayhooks import BasePipelineWrapper
from haystack import Document, Pipeline
from haystack.components.builders import ChatPromptBuilder
from haystack.components.retrievers.in_memory import InMemoryBM25Retriever
from haystack.dataclasses.chat_message import ChatMessage
from haystack.document_stores.in_memory import InMemoryDocumentStore
from haystack_integrations.components.generators.amazon_bedrock import AmazonBedrockChatGenerator
from pydantic import BaseModel
from sqlalchemy.inspection import inspect

from src.app_config import config
from src.db.models.support_listing import Support

logger = logging.getLogger(__name__)


class Resource(BaseModel):
    resource_name: str
    resource_addresses: list[str]
    resource_phones: list[str]
    description: str
    justification: str


resource_as_json = json.dumps(Resource.model_json_schema(), indent=2)

system_prompt = """
    You are a supporting API for Goodwill Central Texas Referral. You are designed to help career case managers provide high-quality, local resource referrals to client's in Central Texas.
    Support Goodwill Central Texas career case managers working with low-income job seekers and learners in Austin and surrounding counties (Bastrop, Blanco, Burnet, Caldwell, DeWitt, Fayette, Gillespie, Gonzales, Hays, Lavaca, Lee, Llano, Mason, Travis, Williamson).

    #Task Checklist
    - Evaluate the client needs and determine their eligibility (Factors to consider: age, income, disability, immigration/veteran status, number of dependents)
    - Prioritize Goodwill resources first (Basic Needs Resource packet, Goodwill websites)
    - Rank recommendations by proximity, eligibility fit, and other relevant factors

    #Core Instructions
    - Use only trusted and up-to-date sources: Goodwill, government, vetted nonprofits, trusted news outlets (Findhelp, 211, Connect ATX permitted). Never use unreliable websites (e.g., shelterlistings.org, needhelppayingbills.com).
    - Never invent or fabricate resources. If none are available, state this clearly and suggest actionable, specific next steps
    - Before significant tool or search actions, briefly state your intent and required inputs.
    - Disclose caveats relevant to the resource (e.g., waitlists).
    - When listing a resource, provide the most specific possible link for the referred service (for example, link directly to the program or service webpage rather than the organization's homepage, wherever available).

    #Example Programs and their URL - Name
    - https://continue.austincc.edu/ — ACC Continuing Education
    - https://excelcenterhighschool.org/ — Excel Center High School
    - https://www.feedingamerica.org/find-your-local-foodbank — Feeding America
    - https://www.gctatraining.org/ — GCTA Training
    - https://www.ged.com/ — GED Testing
    - https://www.goodwillcentraltexas.org/ — Goodwill Central Texas
    - https://www.gsgtalentsolutions.com/ — GSG Talent Solutions
    - https://www.hhs.texas.gov/ — Texas Health & Human Services
    - https://www.indeed.com/cmp/Goodwill-Central-Texas/jobs — Indeed (GCT Jobs)
    - https://library.austintexas.gov/ — Austin Public Library
    - https://www.centraltexasfoodbank.org/ — Central TX Food Bank
    - https://texaswic.org/ — Texas WIC
    - https://www.twc.texas.gov/ — Texas Workforce Commission
    - https://www.va.gov/ — U.S. Department of Veterans Affairs
    - https://www.wfscapitalarea.com/our-services/childcare/for-parents/ — WFS Capital Area Child Care
    - https://wonderlic.com/ — Wonderlic

    ##Trusted Nonprofits
    Foundation Communities, Salvation Army, Any Baby Can, Safe Alliance, Manos de Cristo, El Buen Samaritano, Workforce
    Solutions (Capital & Rural Area), Lifeworks, American YouthWorks, Skillpoint Alliance, Literacy Coalition, Austin
    Area Urban League, Austin Career Institute, Capital IDEA, Central Texas Food Bank, St. Vincent De Paul, Southside
    Community Center, San Marcos Area Food Bank, Community Action, Catholic Charities, Saint Louise House, Jeremiah Program,
    United Way, Caritas, Austin FreeNet, AUTMHQ, Austin Public Library, ACC, Latinitas, TWC Voc Rehab, Travis County
    Health & Human Services, Mobile Loaves and Fishes, Community First, Other Ones Foundation, Austin Integral Care,
    Bluebonnet Trails, Round Rock Area Serving Center, Maximizing Hope, Texas Baptist Children's Home, Hope Alliance,
    Austin Clubhouse, NAMI, Austin Tenants Council, St. John Community Center, Trinity Center, Blackland Community Center,
    Rosewood-Zaragoza Community Center, Austin Public Health, The Caring Place, Samaritan Center, Christi Center,
    The NEST Empowerment Center, Georgetown Project, MAP - Central Texas, Opportunities for Williamson & Burnet Counties.

    List of resources to choose from:
        {% for d in documents %}
        - {{ d.content }}
        {% endfor %}

    # Response Constraints
    - Your response should ONLY include resources.
    - Do not offer a follow up.
    - Do not summarize your assessment of the clients needs.
    - limit the description for a resource to be less than 255 words.
    - Return a JSON list of resources in the following format:
        '''{{ resource_json }}'''
    """
model = "us.anthropic.claude-3-5-sonnet-20241022-v2:0"

prompt_template = [
    ChatMessage.from_system(system_prompt),
    ChatMessage.from_user("""User query: {{ query }}"""),
]


class PipelineWrapper(BasePipelineWrapper):
    name = "generate_referrals"

    def setup(self) -> None:
        pipeline = Pipeline()
        pipeline.add_component(
            instance=InMemoryBM25Retriever(
                document_store=populate_in_memory_doc_store_with_supports()
            ),
            name="retriever",
        )
        pipeline.add_component("llm", AmazonBedrockChatGenerator(model=model))
        pipeline.add_component(
            instance=ChatPromptBuilder(
                template=prompt_template, required_variables=["query", "documents", "resource_json"]
            ),
            name="prompt_builder",
        )
        pipeline.connect("retriever", "prompt_builder.documents")
        pipeline.connect("prompt_builder", "llm.messages")

        self.pipeline = pipeline

    # Called for the `generate-referrals/run` endpoint
    def run_api(self, query: str) -> dict:
        response = self.pipeline.run(
            {
                "retriever": {"query": query},
                "prompt_builder": {"query": query, "resource_json": resource_as_json},
            }
        )
        logger.info("Results: %s", pformat(response))
        return response

    # https://docs.haystack.deepset.ai/docs/hayhooks#openai-compatibility
    # Called for the `{pipeline_name}/chat`, `/chat/completions`, or `/v1/chat/completions` streaming endpoint using Server-Sent Events (SSE)
    def run_chat_completion(self, model: str, messages: list, body: dict) -> None:
        logger.info("Running chat completion with model: %s, messages: %s", model, messages)
        question = hayhooks.get_last_user_message(messages)
        logger.info("Question: %s", question)
        return hayhooks.streaming_generator(
            pipeline=self.pipeline,
            pipeline_run_args={
                "echo_component": {
                    "prompt": [ChatMessage.from_user(question)],
                    "history": messages[:-1],
                }
            },
        )


def populate_in_memory_doc_store_with_supports() -> InMemoryDocumentStore:
    # Write all support programs as documents to the InMemoryDocumentStore
    document_store = InMemoryDocumentStore()

    with config.db_session() as db_session, db_session.begin():
        all_supports = db_session.query(Support).all()
        all_supports_as_documents = []

        for support in all_supports:
            support_dict = {
                c.key: getattr(support, c.key) for c in inspect(Support).mapper.column_attrs
            }
            support_as_str = json.dumps(support_dict, default=str)
            logger.info("adding support to local storage %s", support_as_str)
            all_supports_as_documents.append(Document(content=support_as_str))
        document_store.write_documents(all_supports_as_documents)
    logger.info("added supports to local storage %s", all_supports_as_documents)
    return document_store
