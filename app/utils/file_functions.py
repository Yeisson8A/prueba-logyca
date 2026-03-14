from fastapi import UploadFile, HTTPException, status

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
    return file