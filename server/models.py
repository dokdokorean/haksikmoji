from sqlalchemy import Column, Integer, String, TIMESTAMP, ForeignKey
# SQLAlchemy 모델에서 테이블의 각 칠드를 정의하기 위한 모듈
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
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
  
class Cafeteria(Base):
  __tablename__ = 'cafeteria'
  
  id = Column(Integer, primary_key=True, autoincrement=True)
  name = Column(String(100), nullable=False)
  school_id = Column(Integer, ForeignKey('school.id'), nullable=False)
  school=relationship('School')