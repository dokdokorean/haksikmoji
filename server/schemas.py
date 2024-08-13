from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional

class UserSchema(BaseModel):
  uid: int
  std_id: str
  name:str
  email: EmailStr
  password: str
  school_id: int
  sign_url: Optional[str] = None
  created_at: Optional[datetime] = None
  
  class Config:
    # SQLAlchemy 모델과 호환되도록 설정
    from_attributes = True # 기존 orm_mode


class UserCreate(BaseModel):
  std_id: str
  name:str
  email: EmailStr
  password: str
  school_id: int
  sign_url: str = None # 선택적으로 받을 수 있는 필드
  
class UserLogin(BaseModel):
  std_id: str
  password: str