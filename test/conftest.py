from unittest.mock import MagicMock
import pytest
from app.services.processor_service import ProcessorService


# Mock del servicio de storage para evitar conexiones reales a Azure/DB
@pytest.fixture
def mock_storage_service(mocker):
    # Mockeamos la instancia que usa el router
    return mocker.patch("app.routes.sales_routes.storage_service")

@pytest.fixture
def mock_db_session():
    return MagicMock()

@pytest.fixture
def processor_service(mock_db_session):
    return ProcessorService(db=mock_db_session)