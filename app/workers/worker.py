import json
import time
from azure.storage.queue import QueueClient
from azure.storage.blob import BlobServiceClient
from app.config.azure_config import AZURE_BLOB_CONTAINER, AZURE_QUEUE_NAME, AZURE_STORAGE_CONN
from app.config.database_config import SessionLocal
from app.services.processor_service import ProcessorService

def run_worker():
    queue_client = QueueClient.from_connection_string(AZURE_STORAGE_CONN, AZURE_QUEUE_NAME)
    blob_service_client = BlobServiceClient.from_connection_string(AZURE_STORAGE_CONN)
    
    print("Worker escuchando cola...")
    
    while True:
        messages = queue_client.receive_messages(messages_per_page=1, visibility_timeout=300)
        
        for msg in messages:
            data = json.loads(msg.content)
            job_id = data['job_id']
            blob_name = data['blob']
            print(f"Procesando Job ID: {job_id}")
            
            db = SessionLocal()
            processor = ProcessorService(db)
            
            # 1. Descargar CSV
            blob_client = blob_service_client.get_blob_client(container=AZURE_BLOB_CONTAINER, blob=blob_name)
            downloader = blob_client.download_blob()
            
            # 2. Procesar e insertar
            processor.process_csv_from_stream(downloader.readall(), job_id)
            print(f"Procesamiento de Job ID {job_id} finalizado")
            
            # 3. Eliminar mensaje de la cola
            queue_client.delete_message(msg)
            db.close()
            
        time.sleep(5) # Evitar consumo excesivo de CPU

if __name__ == "__main__":
    run_worker()