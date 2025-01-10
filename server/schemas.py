
from pydantic import BaseModel, EmailStr, Field, validator
from datetime import datetime, time
from typing import Optional, List, Dict

# ------------------------- School(학교) 관련 Schema ----------------------------

# 학교 Schema
class SchoolSchema(BaseModel):
  id: int
  name: str
  campus: Optional[str] = None
  
  class Config:
    from_attributes = True


# ------------------------- Store(매장) 관련 Schema ----------------------------

# 매장 카테고리 Schema
class StoreCategorySchema(BaseModel):
  # id: int
  main_category: str
  sub_category: Optional[str] = None

  class Config:
    from_attributes = True

# 매장 운영시간
class RunningTime(BaseModel):
  opening_time: Optional[time] = None
  closing_time: Optional[time] = None
  
  class Config:
    json_encoders = {
      time: lambda v: v.strftime('%H:%M') if v else None
    }

# 매장 휴게시간
class BreakTime(BaseModel):
  break_start_time: Optional[time] = None
  break_exit_time: Optional[time] = None
  
  class Config:
    json_encoders = {
      time: lambda v: v.strftime('%H:%M') if v else None
    }

# 요일 Schema
class DayOfWeekSchema(BaseModel):
  name: str
  
  class Config:
    from_attributes = True

# 매장 시간 정의 Schema
class StoreHoursSchema(BaseModel):
  running_time: RunningTime
  break_time: BreakTime
  
  class Config:
    from_attributes = True

# 매장 공지사항 Schema
class StoreNoticeSchema(BaseModel):
  id: int
  title: str
  content: str
  is_pinned: bool
  created_at: Optional[datetime] = None
  updated_at: Optional[datetime] = None

# 전체 매장 조회 Schema
class StoreListSchema(BaseModel):
  sid: int
  store_name: Optional[str] = None
  store_number: Optional[str] = None
  store_location: Optional[str] = None
  is_open: Optional[str] = None
  store_thumb_url: Optional[str] = None
  store_banner_url: Optional[str] = None
  category: StoreCategorySchema

# 매장 검색 Schema
class StoreSearchSchema(BaseModel):
  # sid:int
  store_name: Optional[str] = None
  
  class Config:
    from_attributes = True

# 옵션별 메뉴 가격
class MenuOptionSchema(BaseModel):
    option_name: Optional[str]
    price: str

    class Config:
        from_attributes = True

# 매장 메뉴 Schema
class MenuSchema(BaseModel):
    menu_name: str
    menu_image_url: Optional[str]
    options: List[MenuOptionSchema]

    class Config:
        from_attributes = True

# 매장 카테고리 Schema
class MenuCategorySchema(BaseModel):
    category_name: str
    menus: List[MenuSchema]

    class Config:
        from_attributes = True

# 상세 매장 조회 Schema
class StoreDetailSchema(StoreListSchema):
  store_hours: Dict[str, StoreHoursSchema]
  store_notice: List[StoreNoticeSchema]
  menu: List[MenuCategorySchema]
  
  class Config:
    from_attributes = True

# 매장 시간 업데이트 Schema
class StoreUpdateHoursSchema(BaseModel):
  date: str
  content: StoreHoursSchema

# 매장 정보 업데이트 Schema
class StoreUpdateSchema(BaseModel):
  store_number: Optional[str] = None
  store_location: Optional[str] = None
  store_hours: Optional[List[StoreUpdateHoursSchema]] = None

# 매장 공지사항 생성 및 업데이트 Schema
class StoreUpdateNoticeSchema(BaseModel):
  title:str
  content:str
  is_pinned:bool


# ------------------------- User 관련 Schema ----------------------------

# 유저 전체 Schema
class UserSchema(BaseModel):
  uid: int = Field(..., description="DB에서 자동적으로 id 증가")
  name:str
  user_id:str
  user_pw:str
  user_birth:str
  std_id: Optional[str] = None
  email: str
  major: Optional[str] = None
  gender: str
  phone_number: str
  marketing_term: bool
  sign_url: Optional[str] = None
  created_at: Optional[datetime] = None
  role: int = Field(1, description="1 : 일반 유저 / 2 : 매장 사장님 / 3 : 쿠폰 관리 교직원")
  school: SchoolSchema
  
  # 즐겨찾기한 매장 리스트 추가
  favorite_stores: List[StoreListSchema] = []  # 유저가 즐겨찾기한 매장 리스트
  store_id: Optional[int] = None
  is_school_verified: bool
  
  class Config:
    # SQLAlchemy 모델과 호환되도록 설정
    from_attributes = True # 기존 orm_mode
    
# 유저 생성 Schema
class UserCreateSchema(BaseModel):
  name: str
  user_id:str
  user_pw:str
  user_birth:str
  gender:str
  phone_number: str
  school_id: int
  marketing_term: bool

# 유저 로그인 Schema
class UserLoginSchema(BaseModel):
  user_id: str
  user_pw: str

# 유저 사인 Schema
class UserSignSchema(BaseModel):
  sign_url: str

# 유저 아이디 Schema
class VerifyId(BaseModel):
  user_id: str

# 유저 휴대폰 Schema
class VerifyPhoneNum(BaseModel):
  phone_number: str

# 학교인증 Schema
class VerifySchool(BaseModel):
  school_id: int
  email: str
  major: str
  std_id: str

# 이메일 검증 Schema
class VerifyEmail(BaseModel):
  email: str
  verify_code: Optional[str] = None

# ------------------------- Cafeteria(학식) 관련 Schema ----------------------------

# 카페테리아 정보 Schema
class CafeteriaSchema(BaseModel):
  id: int
  name: str
  school: SchoolSchema

# 카페테리아 학식 메뉴 Schema
class CafeteriaMenuSchema(BaseModel):
  id:int
  cafeteria_id: int
  # cafeteria: Optional[CafeteriaSchema] = None
  day_id: int
  # day_of_week: DayOfWeekSchema
  menu_id: int
  meal_id: int
