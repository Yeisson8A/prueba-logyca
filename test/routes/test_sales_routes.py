from unittest.mock import AsyncMock, MagicMock
from fastapi.testclient import TestClient
from app.enums.job_status_enum import Status
from app.main import app

client = TestClient(app)

# Prueba que el endpoint /upload recibe un archivo y devuelve un job_id"""
def test_upload_sales_success(mock_storage_service):
    # Configuración del mock
    mock_storage_service.upload_and_enqueue = AsyncMock(return_value="test-uuid-123")
    
    # Simular archivo CSV
    file_content = b"date,product_id,quantity,price\n2026-01-01,1001,2,10.5"
    files = {"file": ("test.csv", file_content, "text/csv")}
    
    response = client.post("/upload", files=files)
    
    assert response.status_code == 200
    assert response.json() == {"job_id": "test-uuid-123", "status": Status.PENDING.value}
    mock_storage_service.upload_and_enqueue.assert_called_once()

# Prueba que el endpoint /job/{job_id} devuelve el estado correcto"""
def test_get_status_success(mock_storage_service):
    # Simular objeto de base de datos retornado por el servicio
    mock_job = MagicMock()
    mock_job.job_id = "test-uuid-123"
    mock_job.status = Status.COMPLETED.value
    mock_job.created_at = "2026-01-01T10:00:00"
    
    mock_storage_service.get_job_status.return_value = mock_job
    
    response = client.get("/job/test-uuid-123")
    
    assert response.status_code == 200
    assert response.json()["status"] == Status.COMPLETED.value
    assert response.json()["job_id"] == "test-uuid-123"

# Prueba el error 404 cuando el job_id no existe"""
def test_get_status_not_found(mock_storage_service):
    mock_storage_service.get_job_status.return_value = None
    
    response = client.get("/job/invalid-id")
    
    assert response.status_code == 404
    assert response.json()["detail"] == "Job ID no encontrado"