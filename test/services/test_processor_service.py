from unittest.mock import MagicMock

import pandas as pd
from app.enums.job_status_enum import Status


# Valida que el estado del job se actualice en la DB
def test_update_job_status(processor_service, mock_db_session):
    mock_job = MagicMock()
    mock_db_session.query.return_value.filter.return_value.first.return_value = mock_job
    
    processor_service.update_job_status("job-123", Status.COMPLETED.value)
    
    assert mock_job.status == Status.COMPLETED.value
    assert mock_db_session.commit.called

# Valida el cálculo del total y la inserción masiva
def test_process_csv_from_stream_success(processor_service, mock_db_session, mocker):
    # 1. Preparar datos de prueba
    csv_content = b"date,product_id,quantity,price\n2026-01-01,101,5,10.0\n2026-01-01,102,2,20.0"
    job_id = "job-123"

    # 2. Mock de engine.begin()
    # En SQLAlchemy 2.0, engine.begin() devuelve un objeto que al entrar en el 'with'
    # devuelve una Connection.
    mock_engine = mocker.patch("app.services.processor_service.engine")
    mock_connection = MagicMock()
    
    # Esto simula el comportamiento del context manager 'with engine.begin() as conn'
    mock_engine.begin.return_value.__enter__.return_value = mock_connection

    # 3. Espiar el método update_job_status
    spy_status = mocker.spy(processor_service, "update_job_status")

    # 4. Ejecutar el proceso
    # IMPORTANTE: Mockear to_sql para evitar que intente inspeccionar el engine real
    mocker.patch("pandas.DataFrame.to_sql")

    processor_service.process_csv_from_stream(csv_content, job_id)

    # 5. Verificaciones
    # Verificamos que se llamó a to_sql (la lógica de Pandas funcionó)
    assert pd.DataFrame.to_sql.called
    
    # Verificamos que los estados pasaron por PROCESSING y COMPLETED
    assert spy_status.call_args_list[0][0][1] == Status.PROCESSING.value
    assert spy_status.call_args_list[1][0][1] == Status.COMPLETED.value
    
    # Verificamos que se hizo commit en la DB para los cambios de estado
    assert mock_db_session.commit.called

# Valida que el estado cambie a FAILED si hay un error en el CSV
def test_process_csv_from_stream_error(processor_service, mock_db_session, mocker):
    
    # CSV malformado o error inesperado
    csv_content = b"data_invalida"
    job_id = "job-fail"
    
    # Forzamos un error en pandas
    mocker.patch("pandas.read_csv", side_effect=Exception("Data error"))
    spy_status = mocker.spy(processor_service, "update_job_status")

    processor_service.process_csv_from_stream(csv_content, job_id)

    # Verificamos que el último estado fue FAILED
    assert spy_status.call_args_list[-1][0][1] == Status.FAILED.value