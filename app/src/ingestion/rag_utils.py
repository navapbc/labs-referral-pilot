import logging
import os
import threading

from botocore.exceptions import NoCredentialsError
from haystack import Pipeline
from haystack.components.converters import MultiFileConverter
from haystack.components.embedders import SentenceTransformersDocumentEmbedder
from haystack.components.preprocessors import DocumentPreprocessor
from haystack.components.writers import DocumentWriter
from haystack_integrations.document_stores.chroma import ChromaDocumentStore

from src.app_config import config
from src.util import file_util

logger = logging.getLogger(__name__)


def populate_vector_db() -> None:
    logging.basicConfig(format="%(levelname)s - %(name)s -  %(message)s", level=logging.INFO)
    logger.info("populate_vector_db()...")

    doc_store = config.chroma_document_store()
    if config.reset_rag_db and doc_store.count_documents() > 0:
        logger.info("Resetting RAG vector DB...")
        doc_store.delete_all_documents()

    if count := doc_store.count_documents():
        logger.info("Document collection exists with %d documents. Skipping ingestion.", count)
        return

    local_folder = download_s3_folder_to_local()
    ingest_documents(doc_store, [f"{local_folder}/{file}" for file in config.files_to_ingest])

    print("ChromaDB collections:", config.chroma_client().list_collections())


def download_s3_folder_to_local(s3_folder: str = "files_to_ingest_into_vector_db") -> str:
    """Download the contents of a folder directory from S3 to a local folder."""
    bucket = os.environ.get("BUCKET_NAME", f"labs-referral-pilot-app-{config.environment}")
    try:
        local_folder = s3_folder
        os.makedirs(local_folder, exist_ok=True)
    except Exception as e:
        logger.error("Error creating directories for %s: %s", s3_folder, e)
        local_folder = f"/tmp/{s3_folder}"
    logger.info("Downloading s3://%s/%s to local folder %s", bucket, s3_folder, local_folder)

    if config.environment == "local":
        assert os.path.exists(
            local_folder
        ), f"Local folder {local_folder} should exist with manually downloaded files from S3"
        return local_folder

    s3 = file_util.get_s3_client()
    paginator = s3.get_paginator("list_objects_v2")
    try:
        for result in paginator.paginate(Bucket=bucket, Prefix=s3_folder):
            for obj in result.get("Contents", []):
                s3_key = obj["Key"]
                if s3_key.endswith("/"):
                    continue  # Skip folders
                local_file_path = os.path.join(local_folder, os.path.relpath(s3_key, s3_folder))
                os.makedirs(os.path.dirname(local_file_path), exist_ok=True)
                s3.download_file(bucket, s3_key, local_file_path)
                logger.info("Downloaded %s to %s", s3_key, local_file_path)
        return local_folder
    except NoCredentialsError:
        logger.error("AWS credentials not found. Please configure your AWS credentials.")
        raise


def ingest_documents(doc_store: ChromaDocumentStore, sources: list[str]) -> None:
    """Ingest documents into the vector store."""

    pipeline = _create_ingest_pipeline(doc_store)

    # Run the pipeline to index documents
    logger.info("Ingesting documents into %s doc_count=%d", doc_store, doc_store.count_documents())
    pipeline.run({"converter": {"sources": sources}})
    logger.info("Ingested documents doc_count=%d", doc_store.count_documents())


def _create_ingest_pipeline(doc_store: ChromaDocumentStore) -> Pipeline:
    pipeline = Pipeline()
    pipeline.add_component("converter", MultiFileConverter())
    pipeline.add_component(
        "preprocessor",
        DocumentPreprocessor(
            split_length=config.rag_chunk_split_length,
            split_overlap=config.rag_chunk_split_overlap,
            remove_empty_lines=False,
            remove_extra_whitespaces=False,
        ),
    )
    pipeline.add_component(
        "embedder", SentenceTransformersDocumentEmbedder(model=config.rag_embedding_model)
    )
    pipeline.add_component("writer", DocumentWriter(document_store=doc_store))

    # Connect the components
    pipeline.connect("converter.documents", "preprocessor.documents")
    pipeline.connect("preprocessor.documents", "embedder.documents")
    pipeline.connect("embedder.documents", "writer.documents")
    return pipeline
