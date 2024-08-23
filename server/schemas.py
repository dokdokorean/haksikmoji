from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional

class SchoolSchema(BaseModel):
  id: int
  name: str
  campus: str
  
  class Config:
    from_attributes = True

class UserSchema(BaseModel):
  uid: int = Field(..., description="DB에서 자동적으로 id 증가")
  std_id: str
  name:str
  email: EmailStr
  password: str
  school: SchoolSchema
  sign_url: Optional[str] = None
  created_at: Optional[datetime] = None
  role: int = Field(..., description="1 : 일반 유저 / 2 : 매장 사장님 / 3 : 쿠폰 관리 교직원")
  
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
  
class VerifyEmail(BaseModel):
  email: EmailStr
  school_id: int
  verify_code: str = None

class Cafeteria(BaseModel):
  id: int
  name: str
  school: SchoolSchema