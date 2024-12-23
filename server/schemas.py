
from pydantic import BaseModel, EmailStr, Field, validator
from datetime import datetime, time
from typing import Optional, List, Dict


# 학교 Schema
class SchoolSchema(BaseModel):
  id: int
  name: str
  campus: Optional[str] = None
  
  class Config:
    from_attributes = True


# *매장 관련*

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

class MenuSchema(BaseModel):
    menu_name: str
    menu_image_url: Optional[str]
    options: List[MenuOptionSchema]

    class Config:
        from_attributes = True

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

class UserSchema(BaseModel):
  uid: int = Field(..., description="DB에서 자동적으로 id 증가")
  std_id: str
  name:str
  phone_number: str
  # email: EmailStr
  password: str
  marketing_term: bool
  school: SchoolSchema
  sign_url: Optional[str] = None
  created_at: Optional[datetime] = None
  role: int = Field(1, description="1 : 일반 유저 / 2 : 매장 사장님 / 3 : 쿠폰 관리 교직원")
  # 즐겨찾기한 매장 리스트 추가
  favorite_stores: List[StoreListSchema] = []  # 유저가 즐겨찾기한 매장 리스트
  store_id: Optional[int] = None
  
  class Config:
    # SQLAlchemy 모델과 호환되도록 설정
    from_attributes = True # 기존 orm_mode


class UserSignSchema(BaseModel):
  sign_url: str

class UserCreateSchema(BaseModel):
  std_id: str
  name: str
  phone_number: str
  # email: EmailStr
  password: str
  school_id: int
  marketing_term: bool
  sign_url: str = None # 선택적으로 받을 수 있는 필드
  
class UserLoginSchema(BaseModel):
  std_id: str
  password: str
  
class UserStdSchema(BaseModel):
  std_id: str
  
# class VerifyEmail(BaseModel):
#   email: EmailStr
#   school_id: int
#   verify_code: str = None

class VerifyPhoneNum(BaseModel):
  phone_number: str

class CafeteriaSchema(BaseModel):
  id: int
  name: str
  school: SchoolSchema

class CafeteriaMenuSchema(BaseModel):
  id:int
  cafeteria_id: int
  # cafeteria: Optional[CafeteriaSchema] = None
  day_id: int
  # day_of_week: DayOfWeekSchema
  menu_id: int
  meal_id: int


# # Store 관련

# class BreakTimeSchema(BaseModel):
#   break_start_time: Optional[time] = None
#   break_exit_time: Optional[time] = None
  
#   class Config:
#     from_attributes = True
#     json_encoders = {
#       time: lambda v: v.strftime('%H:%M') if v else None
#     }


# class TimePeriodSchema(BaseModel):
#   opening_time: Optional[time] = None
#   closing_time: Optional[time] = None
  
#   class Config:
#     from_attributes = True
#     json_encoders = {
#       time: lambda v: v.strftime('%H:%M') if v else None
#     }

# class StoreHoursSchema(BaseModel):
#   runing_time: TimePeriodSchema
#   break_time: BreakTimeSchema
  
# 매장 공지사항 생성 및 업데이트 Schema
class StoreUpdateNoticeSchema(BaseModel):
  title:str
  content:str
  is_pinned:bool
  

# class StoreNoticeSchema(BaseModel):
#   id: int
#   title: str
#   content: str
#   created_at: Optional[datetime] = None
#   updated_at: Optional[datetime] = None

# class StoreSchema(BaseModel):
#   sid: int
#   store_name: str
#   store_number: str
#   store_location: str
#   is_open: str
#   store_img_url: str
#   category: CategorySchema
#   store_hours: Dict[str, StoreHoursSchema]
#   store_notice: List[StoreNoticeSchema]

#   class Config:
#     from_attributes = True
    
# class StoreListSchema(BaseModel):
#   sid: int
#   store_name: str
#   store_location: str
#   is_open: str
#   store_img_url: str
#   category: CategorySchema
  
#   class Config:
#     from_attributes = True
    
# class StoreHoursUpdateSchema(BaseModel):
#   date: str
#   content: StoreHoursSchema

# class StoreUpdateSchema(BaseModel):
#   store_number: Optional[str] = None
#   store_location: Optional[str] = None
#   store_hours: Optional[List[StoreHoursUpdateSchema]] = None

#   class Config:
#     from_attributes = True
