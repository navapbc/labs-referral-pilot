import logging
import os
from pathlib import Path

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

    chroma_client = config.chroma_client()
    logger.info("ChromaDB collections: %s", chroma_client.list_collections())
    doc_store = config.chroma_document_store()
    collection_name = doc_store._collection_name

    # Clear existing collection if any
    if doc_store.count_documents() > 0:
        logger.info("Deleting existing vector DB collection=%r", collection_name)
        chroma_client.delete_collection(collection_name)
        # Re-create the document store after deletion
        doc_store = config.chroma_document_store()

    # Download files from S3
    local_folder = download_s3_folder_to_local()
    files_to_ingest = [str(p) for p in Path(local_folder).rglob("*") if p.is_file()]
    logger.info("Files to ingest: %s", files_to_ingest)

    # Ingest documents into ChromaDB
    logger.info("Ingesting documents into collection=%r", collection_name)
    # Run the pipeline to index documents
    pipeline = _create_ingest_pipeline(doc_store)
    pipeline.run({"converter": {"sources": files_to_ingest}})
    logger.info("Ingested documents doc_count=%d", doc_store.count_documents())

    logger.info("ChromaDB collections: %s", chroma_client.list_collections())


def download_s3_folder_to_local(s3_folder: str = "files_to_ingest_into_vector_db") -> str:
    """Download the contents of a folder directory from S3 to a local folder."""
    bucket = os.environ.get("BUCKET_NAME", f"labs-referral-pilot-app-{config.environment}")
    try:
        local_folder = s3_folder
        os.makedirs(local_folder, exist_ok=True)
    except PermissionError as e:
        logger.error("Error creating directories for %s: %s", s3_folder, e)
        local_folder = f"/tmp/{s3_folder}"  # nosec B108
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
