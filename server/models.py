from sqlalchemy import Column, Integer, String, TIMESTAMP, ForeignKey, Enum, Time
# SQLAlchemy 모델에서 테이블의 각 필드를 정의하기 위한 모듈
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import time
from server.utils import get_skt_time


# 기본 클래스를 생성
Base = declarative_base()

# 학교
class School(Base):
  __tablename__ = 'school'
  
  id = Column(Integer, primary_key=True, autoincrement=True)
  name = Column(String(50), nullable=False)
  campus = Column(String(50), nullable=False)


# 매장 카테고리
class StoreCategory(Base):
  __tablename__ = 'category'
  
  id = Column(Integer, primary_key=True, autoincrement=True)
  main_category = Column(String(50), nullable=False)
  sub_category = Column(String(50))
  
class DayOfWeek(Base):
  __tablename__ = 'day_of_week'
  
  id = Column(Integer, primary_key=True, autoincrement=True)
  name = Column(Enum('MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT', 'SUN'))

# 매장 운영 및 쉬는시간
class StoreHours(Base):
  __tablename__ = 'store_hours'
  
  id = Column(Integer, primary_key=True, autoincrement=True)
  store_id = Column(Integer, ForeignKey('store.sid'))
  day_of_week_id = Column(Integer, ForeignKey('day_of_week.id'))
  day_of_week = relationship(DayOfWeek)
  opening_time = Column(Time)
  closing_time = Column(Time)
  break_start_time = Column(Time)
  break_exit_time = Column(Time)

# 매장 공지사항
class StoreNotice(Base):
  __tablename__ = 'notice'
  
  id = Column(Integer, primary_key=True, autoincrement=True)
  store_id = Column(Integer, ForeignKey('store.sid'))
  title = Column(String(200))
  content = Column(String(5000))
  created_at = Column(TIMESTAMP, default=get_skt_time(), nullable=False)
  updated_at = Column(TIMESTAMP, default=get_skt_time(), nullable=False)


class Store(Base):
  __tablename__ = 'store'
  
  sid = Column(Integer, primary_key=True, autoincrement=True)
  store_name = Column(String(255), nullable=True)
  store_number = Column(String(255), nullable=True)
  store_location = Column(String(200), nullable=True)
  is_open = Column(Enum('opened', 'closed', 'breaktime'), nullable=True)
  store_img_url = Column(String(3000), nullable=True)
  school_id = Column(Integer, ForeignKey('school.id'))
  school = relationship(School)
  category_id = Column(Integer, ForeignKey('category.id'))
  category = relationship(StoreCategory)
  
  store_hours = relationship(StoreHours)
  store_notice = relationship(StoreNotice)
  
  def update_is_open(self, db_session):
    now = get_skt_time().time().replace(microsecond=0)
    today_day_id = get_skt_time().weekday() + 1
    
    store_hours_today = db_session.query(StoreHours).filter_by(store_id=self.sid, day_of_week_id=today_day_id).first()
    
    if store_hours_today and store_hours_today.opening_time != None and store_hours_today.closing_time != None:
      closing_time = store_hours_today.closing_time
      
      if closing_time == time(0, 0):
        closing_time = time(23, 59, 59)
      
      if store_hours_today.opening_time <= now <= closing_time:
        if store_hours_today.break_start_time and store_hours_today.break_exit_time:
          if store_hours_today.break_start_time <= now <= store_hours_today.break_exit_time:
            self.is_open = 'breaktime'
          else:
            self.is_open = 'opened'
        else:
          self.is_open = 'opened'
      else:
        self.is_open = 'closed'
    else:
      self.is_open = 'closed'
    
    db_session.commit()
  

# Base를 상속받아 모델 정의
class User(Base):
  __tablename__ = 'user' # 테이블 이름
  
  uid = Column(Integer, primary_key=True, autoincrement=True)
  std_id = Column(String(30), nullable=False)
  name = Column(String(20), nullable=False)
  email = Column(String(30), nullable=False)
  password = Column(String(500), nullable=False)
  school_id = Column(Integer, ForeignKey('school.id'), nullable=False)
  school = relationship('School')
  
  sign_url = Column(String(3000))
  created_at = Column(TIMESTAMP, default=get_skt_time, nullable=False)
  role = Column(Integer, nullable=False)


# class Cafeteria(Base):
#   __tablename__ = 'cafeteria'
  
#   id = Column(Integer, primary_key=True, autoincrement=True)
#   name = Column(String(100), nullable=False)
#   school_id = Column(Integer, ForeignKey('school.id'),nullable=False)
#   school = relationship('School')