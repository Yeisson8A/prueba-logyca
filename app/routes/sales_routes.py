from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlalchemy.orm import Session
from app.config.database_config import SessionLocal
from app.enums.job_status_enum import Status
from app.services.storage_service import StorageService

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
    job_id = await storage_service.upload_and_enqueue(file, db)
    return {"job_id": job_id, "status": Status.PENDING.value}

@router.get("/job/{job_id}")
async def get_status(job_id: str, db: Session = Depends(get_db)):
    job = storage_service.get_job_status(job_id, db)
    if not job:
        raise HTTPException(status_code=404, detail="Job ID no encontrado")
    
    return {
        "job_id": job.job_id,
        "status": job.status,
        "created_at": job.created_at
    }