# This file is used to configure Gunicorn server settings.
from src.app_config import config
from src.ingestion import rag_utils


# This function is called once regardless of the number of workers.
# https://stackoverflow.com/questions/24101724/gunicorn-with-multiple-workers-is-there-an-easy-way-to-execute-certain-code-onl
def on_starting(server):
    print("Ingesting into ChromaDB...")
    rag_utils.populate_vector_db()
    print("ChromaDB populated. Collections:", config.chroma_client().list_collections())
