import json
from unittest.mock import MagicMock
from app.workers.worker import run_worker

def test_worker_processing_flow(mocker):
    # 1. Mocks de Azure Storage
    mock_queue_factory = mocker.patch("app.workers.worker.QueueClient.from_connection_string")
    mock_blob_factory = mocker.patch("app.workers.worker.BlobServiceClient.from_connection_string")
    
    mock_queue_client = MagicMock()
    mock_blob_client = MagicMock()
    mock_queue_factory.return_value = mock_queue_client
    mock_blob_factory.return_value = mock_blob_client

    # 2. Simular un mensaje en la cola
    mock_message = MagicMock()
    mock_message.content = json.dumps({"job_id": "test-123", "blob": "test-123.csv"})
    
    # Configuramos receive_messages para que devuelva el mensaje una vez y luego rompa
    # Usamos side_effect para que la segunda llamada lance una excepción y detenga el loop
    mock_queue_client.receive_messages.side_effect = [[mock_message], KeyboardInterrupt()]

    # 3. Mocks de DB y Procesador
    mocker.patch("app.workers.worker.SessionLocal")
    mock_processor_class = mocker.patch("app.workers.worker.ProcessorService")
    mock_processor_instance = mock_processor_class.return_value

    # 4. Mock del contenido del Blob
    mock_downloader = MagicMock()
    mock_downloader.readall.return_value = b"date,product_id,quantity,price\n2026-01-01,1,10,5.0"
    mock_blob_client.get_blob_client.return_value.download_blob.return_value = mock_downloader

    # 5. Ejecutar el worker (capturamos el KeyboardInterrupt para que el test termine)
    try:
        run_worker()
    except KeyboardInterrupt:
        pass

    # 6. Verificaciones
    # ¿Se descargó el blob correcto?
    mock_blob_client.get_blob_client.assert_called_with(
        container="sales-uploads", 
        blob="test-123.csv"
    )
    
    # ¿Se llamó al procesador con los datos correctos?
    mock_processor_instance.process_csv_from_stream.assert_called_once_with(
        b"date,product_id,quantity,price\n2026-01-01,1,10,5.0", 
        "test-123"
    )
    
    # ¿Se eliminó el mensaje de la cola tras procesarlo?
    mock_queue_client.delete_message.assert_called_once_with(mock_message)