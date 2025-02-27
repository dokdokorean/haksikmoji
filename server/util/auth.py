import os
import jwt
from fastapi import HTTPException, Depends
from sqlalchemy.orm import Session
from server.util.time import get_skt_time
from fastapi.security import APIKeyHeader
from server.db import get_db
from server.models import User
from server.util.custom_exception import CustomHTTPException

from datetime import timedelta


oauth2_scheme = APIKeyHeader(name="Authorization")

# 비밀키와 알고리즘 설정
SECRET_KEY = "qlalfzldkwlrdjqtdma"
ALGORITHM = "HS256"
SECRET_KEY = os.getenv('SECRET_KEY')


# 토큰 생성 함수
def create_jwt_token(user):
  payload = {
    "uid": user.uid,
    "std_id": user.std_id,
    "exp": get_skt_time() + timedelta(days=1)  # 토큰 유효 기간 설정 (1시간)
  }
  
  token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
  return token

# 토큰 검증 함수
def verify_jwt_token(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
  try:
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    user_id: str = payload.get("uid")
    
    if user_id is None:
      raise CustomHTTPException(status_code=403, message="토큰이 유효하지 않습니다.")
    
    
    # 유저 정보 조회
    user = db.query(User).filter(User.uid == user_id).first()
    
    if user is None:
      raise CustomHTTPException(status_code=400, message="유저를 찾을 수 없습니다.")
    
    return user

  except jwt.ExpiredSignatureError:
    raise CustomHTTPException(status_code=403, message="토큰이 만료되었습니다.")
  except jwt.InvalidTokenError:
    raise CustomHTTPException(status_code=403, message="토큰이 유효하지 않습니다.")
  except Exception as e:
    raise CustomHTTPException(status_code=500, message=f"서버 오류가 발생하였습니다. 관리자에게 문의해주세요 : {str(e)}")