import json
import os

os.environ["SENTENCE_TRANSFORMERS_HOME"] = os.curdir + "/sentence_transformers"

import logging
from enum import Enum
from pprint import pformat
from typing import Optional

from fastapi import HTTPException
from haystack.dataclasses.chat_message import ChatMessage
from hayhooks import BasePipelineWrapper
from haystack import Document, Pipeline
from haystack.components.builders import ChatPromptBuilder
from haystack.components.converters import MultiFileConverter, OutputAdapter
from haystack.components.embedders import (
    SentenceTransformersDocumentEmbedder,
    SentenceTransformersTextEmbedder,
)
from haystack.components.preprocessors import DocumentPreprocessor
from haystack.components.writers import DocumentWriter
from haystack.core.errors import PipelineRuntimeError
from haystack_integrations.components.retrievers.chroma import ChromaEmbeddingRetriever
from haystack_integrations.document_stores.chroma import ChromaDocumentStore
from pydantic import BaseModel

from src.app_config import config
from src.common import components
from src.db.models.support_listing import Support

logger = logging.getLogger(__name__)


class ReferralType(str, Enum):
    EXTERNAL = "external"
    GOODWILL = "goodwill"
    GOVERNMENT = "government"


class Resource(BaseModel):
    name: str
    addresses: list[str]
    phones: list[str]
    emails: list[str]
    website: Optional[str] = None
    description: str
    justification: str
    referral_type: Optional[ReferralType] = None


class ResourceList(BaseModel):
    resources: list[Resource]

response_schema = """
{
    "resources": {
        "name": string;
        "addresses": string[];
        "phones": string[];
        "emails": string[];
        "website"?: string | null;
        "description": string;
        "justification": string;
        "referral_type"?: "external" | "goodwill" | "government" | null;
    }[];
}
"""


class PipelineWrapper(BasePipelineWrapper):
    name = "generate_referrals_rag"

    def setup(self) -> None:
        pipeline = Pipeline(max_runs_per_component=3)

        # Replace LoadSupports() with retrieval from vector DB
        pipeline.add_component("query_embedder", SentenceTransformersTextEmbedder())
        pipeline.add_component("retriever", ChromaEmbeddingRetriever(document_store))
        pipeline.add_component(
            "output_adapter",
            # https://docs.haystack.deepset.ai/docs/outputadapter
            # Use Jinja template to extract content field from documents and return as list of strings,
            # which is used as input to the prompt builder as supports
            OutputAdapter(
                template="{{ documents | map(attribute='content') | list }}",
                output_type=list,
            ),
        )
        pipeline.connect("query_embedder.embedding", "retriever.query_embedding")
        pipeline.connect("retriever.documents", "output_adapter")

        pipeline.add_component(
            "prompt_builder",
            ChatPromptBuilder(
                # List all variables (required and optional) that could be used in the prompt template.
                # Don't include "template" as it is implicitly required by ChatPromptBuilder
                variables=[
                    "query",
                    "supports",
                    "response_json",
                    "error_message",
                    "invalid_replies",
                ],
            ),
        )
        pipeline.add_component("llm", components.OpenAIWebSearchGenerator())
        pipeline.add_component("output_validator", components.LlmOutputValidator(ResourceList))
        # pipeline.add_component("save_result", components.SaveResult())

        pipeline.connect("output_adapter.output", "prompt_builder.supports")
        pipeline.connect("prompt_builder", "llm.messages")
        pipeline.connect("llm.replies", "output_validator")
        # pipeline.connect("output_validator.valid_replies", "save_result.replies")

        # Re-trigger the prompt builder with error_message and invalid_replies
        pipeline.connect("output_validator.error_message", "prompt_builder.error_message")
        pipeline.connect("output_validator.invalid_replies", "prompt_builder.invalid_replies")

        pipeline.add_component("logger", components.ReadableLogger())
        pipeline.connect("output_validator.valid_replies", "logger")

        pipeline.draw(path="generate_referrals_rag_pipeline.png")

        self.pipeline = pipeline



    def run_api(self, query: str, user_email: str, prompt_version_id: str = "") -> dict:
        result = self._run(query, user_email, prompt_version_id)
        logger.info("User query: %s", query)
        try:
            resp_obj = json.loads(result["llm"]["replies"][-1].text)
            logger.info("Response resources: %s", [r["name"] for r in resp_obj["resources"]])
        except (KeyError, IndexError):
            logger.warning("Failed to parse response: %s", result["llm"]["replies"][-1].text)
        return result

    def _run(self, query: str, user_email: str, prompt_version_id: str = "") -> dict:
        # Retrieve the requested prompt_version_id and error if requested prompt version is not found
        top_k = 5
        try:
            response = self.pipeline.run(
                {
                    "logger": {
                        "messages_list": [{"query": query, "user_email": user_email}],
                    },

                    # query RAG DB
                    "query_embedder": {"text": query},
                    "retriever": {"top_k": top_k, "filters": None},

                    "prompt_builder": {
                        "template": self.prompt_template,
                        "query": query,
                        "response_json": response_schema,
                    },
                    "llm": {"model": "gpt-5-mini", "reasoning_effort": "low"},
                },
                include_outputs_from={"llm", "save_result"},
            )
            logger.debug("Results: %s", pformat(response, width=160))
            return response
        except PipelineRuntimeError as re:
            logger.error("PipelineRuntimeError: %s", re, exc_info=True)
            raise HTTPException(status_code=500, detail=str(re)) from re
        except Exception as e:
            logger.error("Error %s: %s", type(e), e, exc_info=True)
            raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}") from e

    prompt_template = [
        ChatMessage.from_system("""\
You are an API endpoint for Goodwill Central Texas Referral and you return only a JSON object.
You are designed to help career case managers provide high-quality, local resource referrals to client's in Central Texas.
Your role is to support case managers working with low-income job seekers and learners in Austin and surrounding counties (Bastrop, Blanco, Burnet, Caldwell, DeWitt, Fayette, Gillespie, Gonzales, Hays, Lavaca, Lee, Llano, Mason, Travis, Williamson).

## Task Checklist
- Evaluate the client's needs and consider their eligibility for each resource, such as the client's age, income, disability, immigration/veteran status, and number of dependents.
- Suggest recommended resources and rank by proximity and eligibility.
- Never invent or fabricate resources. If none are available, state this clearly. Use trusted sources such as Goodwill, government, vetted nonprofits, and trusted news outlets (Findhelp, 211, Connect ATX permitted). Never use unreliable websites (e.g., shelterlistings.org, needhelppayingbills.com, thehelplist.com). Prefer direct sources rather than websites that aggregate listings.
- NEVER invent or guess URLs. Use only verified URLs that will actually work.
- NEVER recommend Goodwill Workforce Advancement programs unless the user specifically searches for them. Most clients are already enrolled in one of these programs.
- NEVER recommend GCTA classes if the user is searching for Goodwill's Workforce Advancement programs specifically; they aren't interchangeable. 
- NEVER offer Texas Workforce Commission OR Capital IDEA unless there's a more specific resource that these services specifically offer that GoodWill does not offer.
- NEVER recommend a resource that is no longer available (e.g., a course with a start date in the past) OR a resource that is unlikely to be available soon (e.g., a site opening in 2027.)

## Response Constraints
- Your response should ONLY include resources from the list below or resources you find searching the web.
- If no resources are found, return only an empty JSON list without any extra text.
- Do not summarize your assessment of the clients needs.
- Limit the description for a resource to be less than 255 words.
- Set referral_type to: "goodwill" if the resource offered by Goodwill (such as the Goodwill Career and Training Academy), "government" for resources provided by the city, county, or state, and "external" for all others.
- Return a JSON object containing relevant resources in the following format:
```
{{ response_json }}
```

IMPORTANT: ALWAYS leave the email in your response as an empty list / array if the email provided by the resource is invalid (or is some variant of "email_protected", "email protected", etc.). NEVER provide an invalid email address.

Client needs: {{query}}

{% if error_message %}
The response was:
```
{{invalid_replies}}
```

This response doesn't comply with the JSON format requirements and caused this Python exception:
{{error_message}}

Try again and return only the JSON output without any non-JSON text.

{% else %}
## Resources
In addition to what you find searching the web, choose from following list of resources:
{% for s in supports %}
{{ s }}
{% endfor %}

Additional resources:

Career Advancement Training (CAT)
Free short-term training courses (1-4 weeks) covering essential workplace skills and prerequisites. CAT serves as both standalone skill-building and as required preparation for GCTA programs.

⚠️ CRITICAL DISTINCTION: CAT ≠ GCTA CAT trainings are NOT the same as GCTA trainings. Key differences:

 - Duration: CAT classes are much shorter (1-4 weeks) vs GCTA programs (4-12 weeks)
 - Enrollment: CAT has a simpler, faster enrollment process - often just requires online registration through Wufoo forms
 - Prerequisites: CAT courses often serve as prerequisites TO GCTA programs (e.g., Career Advancement Essentials must be completed before GCTA enrollment)
 - Certification: GCTA leads to industry certifications and job placement; CAT builds foundational skills
 - Complexity: GCTA requires extensive documentation, assessments (Wonderlic/CASAS), and multi-level approvals; CAT enrollment is streamlined

CAT Class Registration Links by Location:

Goodwill Resource Center (GRC/South):
 - Career Advancement Essentials: https://gwcareeradvancement.wufoo.com/forms/grc-career-advancement-essentials/
 - Computer Basics/Keyboarding: https://gwcareeradvancement.wufoo.com/forms/grc-computer-basics/
 - Digital Skills 1:1: https://gwcareeradvancement.wufoo.com/forms/grc-digital-skills-11/
 - Financial Empowerment Training: https://gwcareeradvancement.wufoo.com/forms/grc-11-financial-empowerment-trainings/
 - Indeed Lab: https://gwcareeradvancement.wufoo.com/forms/grc-indeed-lab/
 - Interview Preparation & Practice: https://gwcareeradvancement.wufoo.com/forms/grc-interview-preparation-and-practice/
 - Job Preparation 1:1: https://gwcareeradvancement.wufoo.com/forms/grc-job-preparation-11/
 - Online Safety: https://gwcareeradvancement.wufoo.com/forms/grc-online-safety/
 - Virtual Career Advancement Essentials: https://gwcareeradvancement.wufoo.com/forms/virtual-career-advancement-essentials/

Goodwill Community Center (GCC/North):
 - Career Advancement Essentials: https://gwcareeradvancement.wufoo.com/forms/gcc-career-advancement-essentials/
 - Computer Basics/Keyboarding: https://gwcareeradvancement.wufoo.com/forms/gcc-computer-basics/
 - Digital Skills 1:1: https://gwcareeradvancement.wufoo.com/forms/gcc-digital-skills-11/
 - Financial Empowerment Training: https://gwcareeradvancement.wufoo.com/forms/gcc-11-financial-empowerment-trainings/
 - Indeed Lab: https://gwcareeradvancement.wufoo.com/forms/gcc-indeed-lab/
 - Interview Preparation & Practice: https://gwcareeradvancement.wufoo.com/forms/gcc-interview-preparation-and-practice/
 - Job Preparation 1:1: https://gwcareeradvancement.wufoo.com/forms/gcc-job-preparation-11/
 - Wonderlic Prep & Practice: https://gwcareeradvancement.wufoo.com/forms/gcc-wonderlic-prep-and-practice/
 - AI Basics: https://gwcareeradvancement.wufoo.com/forms/zjgi3bu0u7t757/
 - Online Safety: https://gwcareeradvancement.wufoo.com/forms/zs43hn608egpxa/
 - Virtual Career Advancement Essentials: https://gwcareeradvancement.wufoo.com/forms/virtual-career-advancement-essentials/

When recommending CAT classes:
 - Direct clients to the appropriate location-specific registration link
 - GRC serves South Austin and surrounding areas
 - GCC serves North Austin, Round Rock, Georgetown, and surrounding areas
 - Most classes require pre-registration through the Wufoo forms
 - Classes run on monthly schedules - check with Career Case Manager for current availability
 
🔍 CRITICAL: Always Include Specific Training Dates When recommending CAT classes, you MUST visit the Wufoo registration form and extract information from the "Select a training date" dropdown. This dropdown shows:
 - Specific dates (e.g., "10/10/25, 2:00-3:00pm; Alex -- 1 remaining")
 - Times and duration
 - Instructor names (Alex, Mary, Cindy, etc.)
 - Availability/spots remaining ("X remaining" or "0 remaining")

DO:
 - Pull actual upcoming class dates from the form's dropdown
 - Include date, time, instructor, and availability in your recommendation
 - Example: "10/16/25, 10:00am-11:00am, Mary -- 1 remaining"
 - ONLY recommend classes with future dates (after today's date)

DON'T:
 - Recommend CAT classes without checking specific dates
 - Give generic "classes available" responses
 - List classes that show "0 remaining" (full)
 - Recommend classes with dates in the past (check today's date first)


Excel Center High School
Goodwill's tuition-free high school completion program for adults ages 18-50:

Earn accredited high school diploma (not GED)
Flexible schedules designed for working adults
Free childcare during classes
Career coaching integrated into curriculum
College prep included
Small class sizes (15-20 students)
Usually 12-18 months to complete
Website: https://excelcenterhighschool.org/
When to recommend: Clients without high school diploma asking about GED should be informed about Excel Center as a superior alternative to traditional GED programs.

{% endif %}
""")
    ]


# View contents: poetry run chroma browse documents
document_store = ChromaDocumentStore(persist_path="chroma_db")
embedding_model = "multi-qa-mpnet-base-cos-v1"


def export_db_supports_to_md_file() -> None:  # pragma: no cover
    """Save extracted support entries to a markdown file for easier viewing."""
    with config.db_session() as db_session, db_session.begin():
        supports = [
            (
                f"Name: {support.name}\n"
                f"- Description: {support.description}\n"
                f"- Addresses: {', '.join(support.addresses)}\n"
                f"- Phones: {', '.join(support.phone_numbers)}\n"
                f"- Website: {support.website}\n"
                f"- Email Addresses: {', '.join(support.email_addresses)}\n"
            )
            for support in db_session.query(Support).all()
        ]
        # print("\n\n".join(supports))
        with open("extracted_support_entries.md", "w") as f:
            f.write("\n\n".join(supports))


def populate_vector_db() -> None:  # pragma: no cover
    # Check if the vector DB path exists
    if os.path.exists("chroma_db"):
        # Check if the vector DB is already populated
        if (doc_count := document_store.count_documents()) > 0:
            logger.info("Skipping: vector DB already populated with %d documents.", doc_count)
            return

    ingest_documents(
        [
            "referral-docs-for-RAG/LocationListInfo (5).pdf",
            # "referral-docs-for-RAG/Basic Needs Resource Guide.pdf",
            "referral-docs-for-RAG/extracted_support_entries.md",
            "referral-docs-for-RAG/from-Sharepoint/Austin Area Resource List 2025.pdf",
        ]
    )


def ingest_documents(sources: list[str]) -> None:
    """Ingest documents into the vector store."""

    indexing_pipeline = Pipeline()
    indexing_pipeline.add_component("converter", MultiFileConverter())
    indexing_pipeline.add_component(
        "preprocessor",
        DocumentPreprocessor(
            # The parameters can be adjusted based on the desired chunk size
            # split_length=2000,
            # split_overlap=200,
            # Use smaller chunks for testing retrieval
            split_length=200,
            split_overlap=20,
            remove_empty_lines=False,
            remove_extra_whitespaces=False,
        ),
    )
    indexing_pipeline.add_component(
        "embedder", SentenceTransformersDocumentEmbedder(model=embedding_model)
    )
    indexing_pipeline.add_component("writer", DocumentWriter(document_store=document_store))

    # Connect the components
    indexing_pipeline.connect("converter.documents", "preprocessor.documents")
    indexing_pipeline.connect("preprocessor.documents", "embedder.documents")
    indexing_pipeline.connect("embedder.documents", "writer.documents")

    # Run the pipeline to index documents
    indexing_pipeline.run({"converter": {"sources": sources}})


retriever = ChromaEmbeddingRetriever(document_store=document_store)
text_embedder = SentenceTransformersTextEmbedder(model=embedding_model)
text_embedder.warm_up()


def retrieve_documents(query: str, top_k: int = 5) -> list[Document]:
    """Retrieve documents from the vector store."""

    # input_docs = [Document(content=query)]
    print("Running retrieval...", query)
    query_embedding = text_embedder.run(query)['embedding']
    retrieval: dict = retriever.run(query_embedding=query_embedding, top_k=top_k)
    return retrieval["documents"]


def retrieve_documents_pipeline(query: str, top_k: int = 5) -> list[Document]:
    querying = Pipeline()
    querying.add_component("query_embedder", SentenceTransformersTextEmbedder())
    querying.add_component("retriever", ChromaEmbeddingRetriever(document_store))
    querying.connect("query_embedder.embedding", "retriever.query_embedding")
    print("Running retrieval pipeline...", query)
    result = querying.run(
        {"query_embedder": {"text": query}, "retriever": {"top_k": top_k, "filters": None}}
    )
    return result["retriever"]["documents"]


def rag_query(query: str, user_email: str) -> dict:
    pipeline_wrapper = PipelineWrapper()
    pipeline_wrapper.setup()
    return pipeline_wrapper.run_api(query, user_email)

## Create extracted_support_entries.md file:
# make extract-supports NAME="Basic Needs Resources" FILE="Basic Needs Resource Guide.pdf"
# docker compose run  --rm app poetry run direct-export

## Ingest documents into vector DB:
# rm -rf chroma_db && poetry run python -m src.pipelines.generate_referrals_rag.direct ingest
# poetry run chroma browse documents --path chroma_db

## Directly query the vector DB:
# poetry run python -m src.pipelines.generate_referrals_rag.direct retrieve "rent assistance"
# poetry run python -m src.pipelines.generate_referrals_rag.direct retrieve_pipeline "rent assistance"

## RAG query using the pipeline wrapper:
# export OPENAI_API_KEY=...
# poetry run python -m src.pipelines.generate_referrals_rag.direct rag_query "rent assistance"

## Query endpoint:
# make start
# curl -X 'POST' 'http://localhost:4000/generate_referrals_rag/run' -H 'accept: application/json' -H 'Content-Type: application/json' -d '{"query": "rent assistance", "user_email": "my_email"}'


def print_retrieved_docs(docs: list[Document]) -> None:
    for i, doc in enumerate(docs, start=1):
        print(f"Document {i}: {doc.score:.4f} score")
        print(f"{doc.content}")
        print(f"{'-'*40}")


if __name__ == "__main__":
    import sys

    logging.basicConfig(format="%(levelname)s - %(name)s -  %(message)s", level=logging.INFO)
    command = sys.argv[1]
    docs = None
    if command == "export":
        export_db_supports_to_md_file()
    elif command == "ingest":
        populate_vector_db()
    elif command == "retrieve":
        query = sys.argv[2]
        docs = retrieve_documents(query)
        print_retrieved_docs(docs)
    elif command == "retrieve_pipeline":
        query = sys.argv[2]
        docs = retrieve_documents_pipeline(query)
        print_retrieved_docs(docs)
    elif command == "rag_query":
        query = sys.argv[2]
        response = rag_query(query, user_email="any@email.com")
        resp_obj = json.loads(response["llm"]["replies"][-1].text)
        print(json.dumps(resp_obj, indent=2))
