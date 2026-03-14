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

# Prueba que si falla la conexión inicial a Azure, se registra un error CRITICAL y el worker se detiene.
def test_worker_critical_azure_connection_error(mocker):
    # 1. Mockear los clientes de Azure para que lancen una excepción al conectar
    # Simulamos un error de autenticación o conexión
    error_msg = "Connection string is malformed"
    mocker.patch(
        "app.workers.worker.QueueClient.from_connection_string", 
        side_effect=Exception(error_msg)
    )
    
    # 2. Mockear el logger para verificar la trazabilidad
    mock_logger = mocker.patch("app.workers.worker.logger")
    
    # 3. Mockear el bucle while True o el inicio del procesamiento 
    # para asegurar que NO se ejecute si hay error
    mock_receive = mocker.patch("app.workers.worker.QueueClient.receive_messages")

    # 4. Ejecutar el worker
    # No debería lanzar excepción hacia afuera porque el código tiene un try-except con return
    run_worker()

    # 5. Verificaciones (Assertions)
    
    # Verificamos que se registró el error crítico con el mensaje esperado
    mock_logger.critical.assert_called_once_with(
        f"Fallo crítico al conectar con Azure: {error_msg}"
    )
    
    # Verificamos que el worker NO intentó recibir mensajes (se detuvo antes)
    mock_receive.assert_not_called()
    
    # Verificamos que se imprimió el inicio pero falló después
    mock_logger.info.assert_any_call("Iniciando Worker de Procesamiento de Ventas...")

# Prueba que si un Job falla, se registra un ERROR en el log, pero el worker continúa su ejecución.
def test_worker_job_processing_error_traceability(mocker):
    # 1. Mocks de conexión exitosa
    mocker.patch("app.workers.worker.QueueClient.from_connection_string")
    mocker.patch("app.workers.worker.BlobServiceClient.from_connection_string")
    mock_logger = mocker.patch("app.workers.worker.logger")
    
    # 2. Simular un mensaje en la cola
    job_id = "job-error-123"
    mock_message = MagicMock()
    mock_message.content = json.dumps({"job_id": job_id, "blob": "fail.csv"})
    
    # Configuramos para que reciba un mensaje y luego lance KeyboardInterrupt para salir del bucle
    mock_queue_client = mocker.patch("app.workers.worker.QueueClient.from_connection_string").return_value
    mock_queue_client.receive_messages.side_effect = [[mock_message], KeyboardInterrupt()]

    # 3. Forzar un error en el ProcessorService (Simulamos falla de lógica o datos)
    mocker.patch("app.workers.worker.SessionLocal")
    mock_processor = mocker.patch("app.workers.worker.ProcessorService").return_value
    
    error_msg = "Formato de CSV inválido"
    mock_processor.process_csv_from_stream.side_effect = Exception(error_msg)

    # 4. Mock del descargador de blobs (necesario para llegar al procesador)
    mock_blob_client = mocker.patch("app.workers.worker.BlobServiceClient.from_connection_string").return_value
    mock_downloader = MagicMock()
    mock_blob_client.get_blob_client.return_value.download_blob.return_value = mock_downloader

    # 5. Ejecutar el worker
    try:
        run_worker()
    except KeyboardInterrupt:
        pass

    # 6. Verificaciones (Assertions)
    
    # Verificamos que se registró el error específico del Job
    # El mensaje debe coincidir con el f-string: f"Error procesando Job {job_id}: {str(e)}"
    mock_logger.error.assert_called_once_with(
        f"Error procesando Job {job_id}: {error_msg}"
    )
    
    # Verificamos que NO se eliminó el mensaje de la cola (porque falló el proceso)
    mock_queue_client.delete_message.assert_not_called()

# Prueba que si falla el ciclo principal (ej. receive_messages), se registra un WARNING, se espera un tiempo y el worker continúa.
def test_worker_main_cycle_error_resilience(mocker):
    # 1. Mockear los clientes de Azure (conexión exitosa inicial)
    mocker.patch("app.workers.worker.QueueClient.from_connection_string")
    mocker.patch("app.workers.worker.BlobServiceClient.from_connection_string")
    
    # 2. Mock del Logger y Time.sleep
    mock_logger = mocker.patch("app.workers.worker.logger")
    # Mockeamos sleep para que el test no dure 10 segundos realmente
    mock_sleep = mocker.patch("app.workers.worker.time.sleep")
    
    # 3. Forzar error en el ciclo principal
    # Simulamos que la primera llamada a la cola falla, y la segunda lanza KeyboardInterrupt para salir
    mock_queue_client = mocker.patch("app.workers.worker.QueueClient.from_connection_string").return_value
    
    error_msg = "Error temporal de red en la cola"
    mock_queue_client.receive_messages.side_effect = [
        Exception(error_msg), 
        KeyboardInterrupt()  # Esto rompe el bucle while True en el test
    ]

    # 4. Ejecutar el worker
    try:
        run_worker()
    except KeyboardInterrupt:
        pass

    # 5. Verificaciones (Assertions)
    
    # Verificamos que se registró el WARNING con el mensaje correcto
    mock_logger.warning.assert_called_once_with(
        f"Error en el ciclo principal del worker: {error_msg}"
    )
    
    # Verificamos que se ejecutó el sleep de 10 segundos para reintento
    mock_sleep.assert_any_call(10)
    
    # Verificamos que el proceso no se detuvo tras el primer error
    # (El hecho de que haya intentado la segunda vez y llegara al KeyboardInterrupt lo confirma)
    assert mock_queue_client.receive_messages.call_count == 2