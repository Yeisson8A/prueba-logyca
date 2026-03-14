import pandas as pd
from sqlalchemy.orm import Session
from app.config.worker_config import CHUNK_SIZE
from app.core.models import JobStatus
from app.config.database_config import engine
import io
from app.enums.job_status_enum import Status

class ProcessorService:
    def __init__(self, db: Session):
        self.db = db

    def update_job_status(self, job_id: str, status: str):
        job = self.db.query(JobStatus).filter(JobStatus.job_id == job_id).first()
        if job:
            job.status = status
            self.db.commit()

    def process_csv_from_stream(self, file_content: bytes, job_id: str):
        self.update_job_status(job_id, Status.PROCESSING.value)
        
        try:
            chunk_size = int(CHUNK_SIZE) 
            # Leemos el stream
            df_stream = pd.read_csv(io.BytesIO(file_content), chunksize=chunk_size)

            # En SQLAlchemy 2.0, usamos engine.begin() para un manejo automático de transacciones
            with engine.begin() as conn:
                for chunk in df_stream:
                    # Cálculo del total solicitado
                    chunk['total'] = chunk['quantity'] * chunk['price']
                    
                    # Inserción masiva
                    chunk.to_sql(
                        name='sales', 
                        con=conn, 
                        if_exists='append', 
                        index=False, 
                        method='multi'
                    )
            
            self.update_job_status(job_id, Status.COMPLETED.value)
        except Exception as e:
            print(f"Error: {e}")
            self.update_job_status(job_id, Status.FAILED.value)