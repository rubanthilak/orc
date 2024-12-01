from sqlalchemy import Column, String, Integer, DateTime, Boolean
from sqlalchemy.orm import relationship
from app.models.base import Base 

class Task(Base):  
    __tablename__ = "tasks"  
    id = Column(Integer, primary_key=True, autoincrement=True)  
    name = Column(String(255), unique=True, nullable=False)  
    scheduled_time = Column(DateTime, nullable=True)  
    cron = Column(String(255), nullable=True)  
    timezone = Column(String(255), nullable=True)  
    active = Column(Boolean, default=True)  
    webhook = relationship("Webhook", uselist=False, back_populates="task")

    class Config:
        orm_mode = True