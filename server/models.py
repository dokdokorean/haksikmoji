from sqlalchemy import Column, Integer, String, TIMESTAMP, ForeignKey, Enum, Time
# SQLAlchemy 모델에서 테이블의 각 칠드를 정의하기 위한 모듈
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime, time
import pytz

# 기본 클래스를 생성
Base = declarative_base()

def get_skt_time():
  kst = pytz.timezone('Asia/Seoul')
  return datetime.now(kst)

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

class School(Base):
  __tablename__ = 'school'
  
  id = Column(Integer, primary_key=True, autoincrement=True)
  name = Column(String(50), nullable=False)
  campus = Column(String(50), nullable=False)
  
class Category(Base):
  __tablename__ = 'category'
  
  id = Column(Integer, primary_key=True, autoincrement=True)
  main_category = Column(String(50), nullable=False)
  sub_category = Column(String(50))

class Cafeteria(Base):
  __tablename__ = 'cafeteria'
  
  id = Column(Integer, primary_key=True, autoincrement=True)
  name = Column(String(100), nullable=False)
  school_id = Column(Integer, ForeignKey('school.id'),nullable=False)
  school = relationship('School')
  
class Store(Base):
  __tablename__ = 'store'
  
  sid = Column(Integer, primary_key=True, autoincrement=True)
  store_name = Column(String(255))
  store_number = Column(String(255))
  store_location = Column(String(200))
  is_open = Column(Enum('opened', 'closed', 'breaktime'))
  store_img_url = Column(String(3000))
  school_id = Column(Integer, ForeignKey('school.id'))
  school = relationship('School')
  category_id = Column(Integer, ForeignKey('category.id'))
  category = relationship('Category')
  
  store_hours = relationship('StoreHours', back_populates='store')
  store_notice = relationship('Notice')
  
  def update_is_open(self, db_session):
    now = get_skt_time().time().replace(microsecond=0)
    today_day_id = get_skt_time().weekday() + 1
    
    store_hours_today = db_session.query(StoreHours).filter_by(store_id=self.sid, day_of_week_id=today_day_id).first()
    
    if store_hours_today and store_hours_today.opening_time != None and store_hours_today.closing_time != None:
      closing_time = store_hours_today.closing_time
      
      if closing_time == time(0, 0):
        
        closing_time = time(23, 59, 59)
      
      if store_hours_today.opening_time <= now <= closing_time:
        self.is_open = 'opened'
      else:
        self.is_open = 'closed'
    else:
      self.is_open = 'closed'
    
    db_session.commit()
    
class StoreHours(Base):
  __tablename__ = 'store_hours'
  
  id = Column(Integer, primary_key=True, autoincrement=True)
  store_id = Column(Integer, ForeignKey('store.sid'))
  day_of_week_id = Column(Integer, ForeignKey('day_of_week.id'))
  day_of_week = relationship('DayOfWeek')
  opening_time = Column(Time)
  closing_time = Column(Time)
  
  store = relationship('Store', back_populates='store_hours')



class DayOfWeek(Base):
  __tablename__ = 'day_of_week'
  
  id = Column(Integer, primary_key=True, autoincrement=True)
  name = Column(Enum('MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT', 'SUN'))


class Notice(Base):
  __tablename__ = 'notice'
  
  id = Column(Integer, primary_key=True, autoincrement=True)
  store_id = Column(Integer, ForeignKey('store.sid'))
  title = Column(String(200))
  content = Column(String(5000))
  created_at = Column(TIMESTAMP, default=get_skt_time(), nullable=False)
  updated_at = Column(TIMESTAMP, default=get_skt_time(), nullable=False)