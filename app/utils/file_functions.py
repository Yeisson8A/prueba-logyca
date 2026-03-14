import csv
import io
from fastapi import UploadFile, HTTPException, status

# Definimos los encabezados requeridos
REQUIRED_COLUMNS = ["date", "product_id", "quantity", "price"]

async def validate_csv_file(file: UploadFile):
    # 1. Validar por extensión
    if not file.filename.endswith('.csv'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El archivo debe ser un formato .csv válido."
        )
    
    # 2. Validar por MIME type
    if file.content_type not in ["text/csv", "application/vnd.ms-excel"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tipo de contenido no permitido. Debe ser CSV."
        )
    
    # 3. Leer el inicio del archivo para validar contenido
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="El archivo CSV está vacío")

    # Convertir bytes a string para el lector de CSV
    try:
        stream = io.StringIO(content.decode('utf-8'))
        reader = csv.DictReader(stream)
        
        # 4. Validar si tiene encabezados y si coinciden
        headers = reader.fieldnames
        if not headers:
            raise HTTPException(status_code=400, detail="El archivo no contiene encabezados")

        # 5. Verificamos que todas las columnas requeridas estén presentes
        missing_columns = [col for col in REQUIRED_COLUMNS if col not in headers]
        if missing_columns:
            raise HTTPException(
                status_code=400, 
                detail=f"Encabezados inválidos. Faltan columnas: {', '.join(missing_columns)}"
            )

        # 6. Validar que tenga al menos una fila de datos
        first_row = next(reader, None)
        if first_row is None:
            raise HTTPException(status_code=400, detail="El archivo CSV contiene encabezados pero no tiene datos")

    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="El archivo no tiene una codificación UTF-8 válida")
    finally:
        # Importante: Reiniciar el puntero para que el servicio de carga pueda leerlo desde el inicio
        await file.seek(0)
    return file