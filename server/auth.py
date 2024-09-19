import os
import jwt
from fastapi import HTTPException, Depends
from sqlalchemy.orm import Session
from server.utils import get_skt_time
from fastapi.security import OAuth2PasswordBearer
from server.db import get_db
from server.models import User

from datetime import timedelta


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# 비밀키와 알고리즘 설정
SECRET_KEY = "your_secret_key"
ALGORITHM = "HS256"
SECRET_KEY = os.getenv('SECRET_KEY')


# 토큰 생성 함수
def create_jwt_token(user):
  payload = {
    "uid": user.uid,
    "std_id": user.std_id,
    "exp": get_skt_time() + timedelta(hours=1)  # 토큰 유효 기간 설정 (예: 1시간)
  }
  
  token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
  return token

# 토큰 검증 함수
def verify_jwt_token(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
  print(token)
  try:
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    user_id: str = payload.get("uid")
    
    if user_id is None:
      raise HTTPException(status_code=403, detail="토큰이 유효하지 않음")
    
    
    # 유저 정보 조회
    user = db.query(User).filter(User.uid == user_id).first()
    
    if user is None:
      raise HTTPException(status_code=403, detail="유저를 찾을 수 없음")
    
    return user

  except jwt.ExpiredSignatureError:
    raise HTTPException(status_code=403, detail="토큰이 만료됨")
  except jwt.InvalidTokenError:
    raise HTTPException(status_code=403, detail="토큰이 유효하지 않음")