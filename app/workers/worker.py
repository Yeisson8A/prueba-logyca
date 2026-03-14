import json
import time
from azure.storage.queue import QueueClient
from azure.storage.blob import BlobServiceClient
from app.config.azure_config import AZURE_BLOB_CONTAINER, AZURE_QUEUE_NAME, AZURE_STORAGE_CONN
from app.config.database_config import SessionLocal
from app.logger.logger import setup_logger
from app.services.processor_service import ProcessorService

logger = setup_logger("SalesWorker")

def run_worker():
    logger.info("Iniciando Worker de Procesamiento de Ventas...")

    try:
        queue_client = QueueClient.from_connection_string(AZURE_STORAGE_CONN, AZURE_QUEUE_NAME)
        blob_service_client = BlobServiceClient.from_connection_string(AZURE_STORAGE_CONN)
        logger.info("Conexión exitosa con Azure Storage.")
    except Exception as e:
        logger.critical(f"Fallo crítico al conectar con Azure: {str(e)}")
        return
    
    logger.info("Worker escuchando cola...")
    
    while True:
        try:
            messages = queue_client.receive_messages(messages_per_page=1, visibility_timeout=300)
            
            for msg in messages:
                data = json.loads(msg.content)
                job_id = data['job_id']
                blob_name = data['blob']
                logger.info(f"Iniciando Job: {job_id} | Archivo: {blob_name}")
                
                db = SessionLocal()
                processor = ProcessorService(db)
                
                try:
                    # 1. Descargar CSV
                    logger.debug(f"Descargando blob {blob_name}...")
                    blob_client = blob_service_client.get_blob_client(container=AZURE_BLOB_CONTAINER, blob=blob_name)
                    downloader = blob_client.download_blob()
                    
                    # 2. Procesar e insertar
                    content = downloader.readall()
                    logger.info(f"Procesando contenido de {job_id} ({len(content)} bytes)...")
                    processor.process_csv_from_stream(content, job_id)
                    
                    # 3. Eliminar mensaje de la cola
                    queue_client.delete_message(msg)
                    logger.info(f"Job {job_id} completado con éxito y eliminado de la cola.")
                except Exception as e:
                    logger.error(f"Error procesando Job {job_id}: {str(e)}")
                finally:
                    db.close()
                
            time.sleep(5) # Evitar consumo excesivo de CPU

        except Exception as e:
            logger.warning(f"Error en el ciclo principal del worker: {str(e)}")
            time.sleep(10)

if __name__ == "__main__":
    run_worker()