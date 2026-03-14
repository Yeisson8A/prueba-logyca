from datetime import UTC, datetime
from sqlalchemy import Column, DateTime, Float, Integer, Date, Numeric, String, func
from app.config.database_config import Base
from app.enums.job_status_enum import Status

class Sale(Base):
    __tablename__ = "sales"
    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False)
    product_id = Column(Integer, nullable=False)
    quantity = Column(Integer, nullable=False)
    price = Column(Numeric(10, 2), nullable=False)
    total = Column(Numeric(12, 2), nullable=False) # total = quantity * price

class JobStatus(Base):
    __tablename__ = "job_status"
    job_id = Column(String, primary_key=True, index=True)
    status = Column(String, default=Status.PENDING.value) # PENDING, PROCESSING, COMPLETED, FAILED
    filename = Column(String)
    created_at = Column(DateTime, default=datetime.now(UTC))
    updated_at = Column(DateTime, default=datetime.now(UTC), onupdate=datetime.now(UTC))

class SalesDailySummary(Base):
    __tablename__ = "sales_daily_summary"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, unique=True, nullable=False, index=True)
    total_sales = Column(Float, nullable=False, default=0.0)
    last_updated = Column(DateTime, server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<SalesDailySummary(date={self.date}, total={self.total_sales})>"