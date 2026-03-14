import uuid
from azure.storage.blob import BlobServiceClient
from azure.storage.queue import QueueClient
from sqlalchemy.orm import Session
from app.config.azure_config import AZURE_BLOB_CONTAINER, AZURE_QUEUE_NAME, AZURE_STORAGE_CONN
from app.core.models import JobStatus
from app.enums.job_status_enum import Status

class StorageService:
    def __init__(self):
        self.conn_str = AZURE_STORAGE_CONN
        self.container = AZURE_BLOB_CONTAINER
        self.queue = AZURE_QUEUE_NAME

    async def upload_and_enqueue(self, file, db: Session):
        job_id = str(uuid.uuid4())
        blob_name = f"{job_id}.csv"

        # Crear registro en DB con estado PENDING
        new_job = JobStatus(job_id=job_id, status=Status.PENDING.value, filename=file.filename)
        db.add(new_job)
        db.commit()
        
        # Lógica de subida a Blob Storage
        blob_service_client = BlobServiceClient.from_connection_string(self.conn_str)
        blob_client = blob_service_client.get_blob_client(container=self.container, blob=blob_name)
        blob_client.upload_blob(await file.read())

        # Notificar a la cola para procesamiento asíncrono
        queue_client = QueueClient.from_connection_string(self.conn_str, self.queue)
        queue_client.send_message(f'{{"job_id": "{job_id}", "blob": "{blob_name}"}}')
        
        return job_id
    
    def get_job_status(self, job_id: str, db: Session):
        return db.query(JobStatus).filter(JobStatus.job_id == job_id).first()