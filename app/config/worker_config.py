import os
from dotenv import load_dotenv


load_dotenv()

CHUNK_SIZE = os.getenv("CHUNK_SIZE", "0")