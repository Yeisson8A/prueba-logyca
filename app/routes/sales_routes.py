from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlalchemy.orm import Session
from app.config.database_config import SessionLocal
from app.enums.job_status_enum import Status
from app.services.storage_service import StorageService
from app.utils.file_functions import validate_csv_file

router = APIRouter()
storage_service = StorageService()

# Dependencia para obtener la sesión de DB
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/upload")
async def upload_sales(file: UploadFile, db: Session = Depends(get_db)):
    file = await validate_csv_file(file)
    job_id = await storage_service.upload_and_enqueue(file, db)
    return {"job_id": job_id, "status": Status.PENDING.value}

@router.get("/job/{job_id}")
async def get_status(job_id: str, db: Session = Depends(get_db)):
    try:
        uuid_obj = UUID(job_id)
    except ValueError:
        raise HTTPException(
            status_code=400, 
            detail=f"El formato del job_id '{job_id}' no es un UUID válido."
        )

    job = storage_service.get_job_status(str(uuid_obj), db)
    if not job:
        raise HTTPException(status_code=404, detail="Job ID no encontrado")
    
    return {
        "job_id": job.job_id,
        "status": job.status,
        "created_at": job.created_at
    }