import os
from functools import cached_property

import chromadb
from chromadb.api import ClientAPI
from haystack_integrations.document_stores.chroma import ChromaDocumentStore

from src.adapters import db
from src.util.env_config import PydanticBaseEnvConfig


class AppConfig(PydanticBaseEnvConfig):
    environment: str = "local"
    # Preview environment bucket names look like 'p-###-labs-referral-pilot-app-dev'
    bucket_name: str = "local"
    # Set HOST to 127.0.0.1 by default to avoid other machines on the network
    # from accessing the application. This is especially important if you are
    # running the application locally on a public network. This needs to be
    # overridden to 0.0.0.0 when running in a container
    host: str = "127.0.0.1"
    port: int = 3000

    phoenix_collector_endpoint: str = "https://phoenix:6006"
    batch_otel: bool = True

    redact_pii: bool = False

    aws_ses_from_email: str = "no-reply@test.com"

    @cached_property
    def db_client(self) -> db.PostgresDBClient:
        return db.PostgresDBClient()

    def db_session(self) -> db.Session:
        return self.db_client.get_session()

    # These versions should only be used for the deployed Phoenix instance.
    # Version ids are base64 encodings of 'PromptVersion:N' where N is simply a counter,
    # so they are not unique across different Phoenix instances.
    PROMPT_VERSIONS: dict = {
        "extract_supports": "UHJvbXB0VmVyc2lvbjo0Ng==",
        "generate_referrals": "UHJvbXB0VmVyc2lvbjo3NA==",  # if no suffix, the default Austin area prompt will be used
        "generate_referrals_keystone": "UHJvbXB0VmVyc2lvbjo3Nw==",
        "generate_action_plan": "UHJvbXB0VmVyc2lvbjo3NQ==",
        "crawl_gcta": "UHJvbXB0VmVyc2lvbjozNg==",
        "crawl_indeed": "UHJvbXB0VmVyc2lvbjozNA==",
    }

    # For RAG vector DB
    rag_db_host: str = "52.4.126.145"
    rag_db_port: int = 8000
    collection_name_prefix: str = "referral_resources"
    # Whether to delete collections created for preview environments in ChromaDB
    delete_preview_collections: bool = True

    # The embedding model is downloaded by SentenceTransformersTextEmbedder when it first runs
    # multi-qa-mpnet-base-cos-v1 was used for pilot 1 but is large (400M)
    # all-MiniLM-L6-v2 is a smaller (100M), more efficient model
    # When this is changed, the vector DB should be re-populated with embeddings from the new model (populate-vector-db)
    rag_embedding_model: str = "multi-qa-mpnet-base-cos-v1"

    # The parameters can be adjusted based on the desired chunk size
    rag_chunk_split_length: int = 500
    rag_chunk_split_overlap: int = 50
    retrieval_top_k: int = 10

    # LLM Model Configuration per pipeline
    default_openai_model_version: str = "gpt-5.1"
    default_openai_reasoning_level: str = "none"

    generate_referrals_model_version: str = "gpt-5.1"
    generate_referrals_reasoning_level: str = "none"

    generate_referrals_rag_model_version: str = "gpt-5.1"
    generate_referrals_rag_reasoning_level: str = "none"

    generate_action_plan_model_version: str = "gpt-5.1"
    generate_action_plan_reasoning_level: str = "none"

    generate_referrals_from_doc_model_version: str = "gpt-5.1"
    generate_referrals_from_doc_reasoning_level: str = "none"

    def chroma_client(self) -> ClientAPI:
        return chromadb.HttpClient(host=self.rag_db_host, port=self.rag_db_port)

    def chroma_document_store(self) -> ChromaDocumentStore:
        # Note: since there's a single ChromaDB instance for all environments,
        # there can be collision if multiple developers are running RAG simultaneously,
        # but this is unlikely at this time.
        # If doing read-only RAG retrievals locally, temporarily change this to
        # "dev" to use the same collection as the deployed dev environment.
        bucket_name = self.bucket_name

        # Use bucket name as part of collection name to avoid collision with `dev` environment for PRs
        return ChromaDocumentStore(
            collection_name=f"{self.collection_name_prefix}_{bucket_name}",
            host=self.rag_db_host,
            port=self.rag_db_port,
        )


# SENTENCE_TRANSFORMERS_HOME is used by SentenceTransformersTextEmbedder Haystack component
if "SENTENCE_TRANSFORMERS_HOME" not in os.environ:
    os.environ["SENTENCE_TRANSFORMERS_HOME"] = os.curdir + "/sentence_transformers"

config = AppConfig()
