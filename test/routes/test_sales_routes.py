from io import BytesIO
from unittest.mock import AsyncMock, MagicMock
import uuid
from fastapi.testclient import TestClient
from app.enums.job_status_enum import Status
from app.main import app

client = TestClient(app)

# Prueba que el endpoint /upload recibe un archivo y devuelve un job_id
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

# Valida que un archivo que no termine en .csv sea rechazado (Error 400)
def test_upload_invalid_extension(mock_storage_service):
    file_content = b"contenido de imagen falso"
    # Enviamos un .png
    files = {
        "file": ("foto.png", BytesIO(file_content), "image/png")
    }
    
    response = client.post("/upload", files=files)
    
    assert response.status_code == 400
    assert "El archivo debe ser un formato .csv válido" in response.json()["detail"]
    # Verificamos que el servicio NUNCA fue llamado
    mock_storage_service.upload_and_enqueue.assert_not_called()

# Valida que un archivo .csv con un MIME type incorrecto sea rechazado
def test_upload_invalid_mimetype(mock_storage_service):
    file_content = b"date,product,qty"
    # Enviamos extensión .csv pero MIME type de PDF para engañar al sistema
    files = {
        "file": ("datos.csv", BytesIO(file_content), "application/pdf")
    }
    
    response = client.post("/upload", files=files)
    
    assert response.status_code == 400
    assert "Tipo de contenido no permitido" in response.json()["detail"]

# Prueba que el endpoint devuelve 200 con un UUID válido y existente
def test_get_status_success(mock_storage_service):
    # Generamos un UUID real para las pruebas de éxito
    valid_uuid = str(uuid.uuid4())

    # 1. Simular objeto de base de datos
    mock_job = MagicMock()
    mock_job.job_id = valid_uuid
    mock_job.status = Status.COMPLETED.value
    mock_job.created_at = "2026-01-01T10:00:00"
    
    mock_storage_service.get_job_status.return_value = mock_job
    
    # 2. Ejecutar petición con el UUID válido
    response = client.get(f"/job/{valid_uuid}")
    
    # 3. Aserciones
    assert response.status_code == 200
    assert response.json()["job_id"] == valid_uuid
    assert response.json()["status"] == Status.COMPLETED.value

# Prueba que devuelve 400 cuando el formato no es UUID (ej. 123-hola)
def test_get_status_invalid_uuid_format():
    # Aquí ni siquiera necesitamos el mock_storage_service porque la 
    # validación ocurre antes de llamar al servicio.
    
    response = client.get("/job/123-hola")
    
    assert response.status_code == 400
    assert "no es un UUID válido" in response.json()["detail"]

# Prueba que devuelve 404 cuando el UUID es válido pero no existe en DB"""
def test_get_status_not_found(mock_storage_service):
    # Usamos un UUID con formato correcto pero que no estará en la DB
    random_uuid = str(uuid.uuid4())
    mock_storage_service.get_job_status.return_value = None
    
    response = client.get(f"/job/{random_uuid}")
    
    assert response.status_code == 404
    assert response.json()["detail"] == "Job ID no encontrado"