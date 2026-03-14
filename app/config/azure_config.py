import os

from dotenv import load_dotenv


load_dotenv()

AZURE_STORAGE_CONN = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
AZURE_BLOB_CONTAINER = os.getenv("AZURE_BLOB_CONTAINER_NAME")
AZURE_QUEUE_NAME = os.getenv("AZURE_QUEUE_NAME")