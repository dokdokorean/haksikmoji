from pydantic import BaseModel, EmailStr, Field
from datetime import datetime, time
from typing import Optional, List

class SchoolSchema(BaseModel):
  id: int
  name: str
  campus: str
  
  class Config:
    from_attributes = True
    
class DayOfWeekSchema(BaseModel):
  name: str
  
  class Config:
    from_attributes = True

class CategorySchema(BaseModel):
  main_category: str
  sub_category: Optional[str] = None

class UserSchema(BaseModel):
  uid: int = Field(..., description="DB에서 자동적으로 id 증가")
  std_id: str
  name:str
  email: EmailStr
  password: str
  school: SchoolSchema
  sign_url: Optional[str] = None
  created_at: Optional[datetime] = None
  role: int = Field(1, description="1 : 일반 유저 / 2 : 매장 사장님 / 3 : 쿠폰 관리 교직원")
  
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



# Store 관련

class StoreHoursSchema(BaseModel):
  day_of_week: DayOfWeekSchema
  opening_time: Optional[time] = None
  closing_time: Optional[time] = None

  class Config:
    from_attributes = True
    
class StoreUpdateNoticeSchema(BaseModel):
  title:str
  content:str
  

class StoreNoticeSchema(BaseModel):
  id: int
  title: str
  content: str
  created_at: Optional[datetime] = None
  updated_at: Optional[datetime] = None

class StoreSchema(BaseModel):
  sid: int
  store_name: str
  store_number: str
  store_location: str
  is_open: str
  store_img_url: str
  category: CategorySchema
  store_hours: List[StoreHoursSchema]
  store_notice: List[StoreNoticeSchema]

  class Config:
    from_attributes = True
    
class StoreListSchema(BaseModel):
  sid: int
  store_name: str
  store_location: str
  is_open: str
  store_img_url: str
  school: SchoolSchema
  category: CategorySchema
  
  class Config:
    from_attributes = True
