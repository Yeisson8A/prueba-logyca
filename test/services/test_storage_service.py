import pytest
from unittest.mock import MagicMock, AsyncMock
from app.services.storage_service import StorageService

@pytest.mark.asyncio
async def test_upload_and_enqueue_success(mocker):
    # 1. Mocks de Base de Datos
    mock_db = MagicMock()
    
    # 2. Mocks de Archivo (FastAPI UploadFile)
    mock_file = AsyncMock()
    mock_file.filename = "ventas.csv"
    mock_file.read.return_value = b"contenido,del,archivo"

    # 3. Mocks de Azure (Simulamos la cadena de llamadas)
    # Mock para Blob Storage
    mock_blob_service = mocker.patch("app.services.storage_service.BlobServiceClient.from_connection_string")
    mock_blob_client = MagicMock()
    mock_blob_service.return_value.get_blob_client.return_value = mock_blob_client

    # Mock para Queue Storage
    mock_queue_service = mocker.patch("app.services.storage_service.QueueClient.from_connection_string")
    mock_queue_client = MagicMock()
    mock_queue_service.return_value = mock_queue_client

    # 4. Ejecución del servicio
    service = StorageService()
    job_id = await service.upload_and_enqueue(mock_file, mock_db)

    # 5. Verificaciones (Assertions)
    
    # ¿Se guardó en la DB?
    assert mock_db.add.called
    assert mock_db.commit.called
    
    # ¿Se subió el blob con el contenido correcto?
    mock_blob_client.upload_blob.assert_called_once_with(b"contenido,del,archivo")
    
    # ¿Se envió el mensaje correcto a la cola?
    mock_queue_client.send_message.assert_called_once()
    sent_msg = mock_queue_client.send_message.call_args[0][0]
    assert job_id in sent_msg
    assert ".csv" in sent_msg

def test_get_job_status(mocker):
    # Mock de DB
    mock_db = MagicMock()
    mock_query = mock_db.query.return_value.filter.return_value.first
    
    # Simulamos que el registro existe
    mock_job = MagicMock()
    mock_job.job_id = "123"
    mock_query.return_value = mock_job
    
    service = StorageService()
    result = service.get_job_status("123", mock_db)
    
    assert result.job_id == "123"
    mock_db.query.assert_called_once()