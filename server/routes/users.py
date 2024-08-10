from fastapi import APIRouter, HTTPException, Depends, Response
from sqlalchemy.orm import Session
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr
from datetime import timedelta
from passlib.context import CryptContext
from server.models import User
from server.models import get_skt_time
from server.schemas import UserSchema  # Pydantic 모델 임포트
from server.db import get_db
from server.schemas import UserSchema, UserCreate, UserLogin
import os
import jwt as pyjwt
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

SECRET_KEY = os.getenv('SECRET_KEY')
# 비밀번호 해싱
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

users_router = APIRouter(
  prefix="/users"
)

def create_jwt_token(user):
  payload = {
    "uid": user.uid,
    "std_id": user.std_id,
    "exp": get_skt_time() + timedelta(hours=1)  # 토큰 유효 기간 설정 (예: 1시간)
  }
  token = pyjwt.encode(payload, SECRET_KEY, algorithm="HS256")
  return token

# 유저 전체 리스트 조회 API
# response_model는 반환되는 데이터가 UserSchema와 일치하지 않으면 오류를 발생시키는 데이터 검증 코드
@users_router.get('', response_model=list[UserSchema])
# Depends는 의존성 주입을 처리하는 코드 (다른 함수를 호출하고 그 결과를 가져와서 매개변수로 활용하는 것)
# Session은 SQLAlchemy에서 데이터베이스와의 모든 상호작용을 관리하는 주요 도구로 쿼리를 실행하거나, 트랜잭션을 관리하고, 변경 사항을 커밋함
async def read_users(db: Session = Depends(get_db)):
  users = db.query(User).all()
  return users

  # return JSONResponse(status_code=200, content={'success' : True, 'message' : '유저들 조회 완료', 'body' : userList})
  #'_sa_instance_state': <sqlalchemy.orm.state.InstanceState object>는 SQLAlchemy ORM 객체를 그대로 출력하거나 JSON으로 변환하려고 할 대, 자동으로 추가하여 내부상태도 함께 출력됨.
  # SQLAlchemy 모델 객체를 Pydantic모델로 변환해야함

# 이메일 검증 API
@users_router.post('/valid-email')
async def check_email(email: EmailStr, db: Session = Depends(get_db)):

  existing_user = db.query(User).filter(User.email == email).first()
  if existing_user:
    raise HTTPException(status_code=400, detail="중복된 이메일입니다.")
  
  return JSONResponse(status_code=200, content={'success' : True, 'message' : '가입 가능한 이메일'})


# 유저 생성 API
@users_router.post('', response_model=UserCreate)
async def create_user(createData: UserCreate,db: Session = Depends(get_db)):
  existing_user = db.query(User).filter(User.email == createData.email).first()
  if existing_user:
    raise HTTPException(status_code=400, detail="중복된 이메일입니다.")
  
  hashed_password = pwd_context.hash(createData.password)
  
  # 새 유저 객체 생성
  new_user = User(
    std_id=createData.std_id,
    name=createData.name,
    email=createData.email,
    password=hashed_password,
    school_id=createData.school_id,
    sign_url=createData.sign_url,
    created_at=get_skt_time()
  )
  
  # 새 유저 등록
  db.add(new_user)
  db.commit()
  db.refresh(new_user) # 새로 추가된 유저의 정보를 최신화
  
  return JSONResponse(status_code=201, content={'success': True, 'message' : '계정 생성 완료'})

# 유저 한 명 조회 API
@users_router.get('/{std_id}', response_model=UserSchema)
async def read_user(std_id: str, db: Session = Depends(get_db)):
  # std_id에 해당하는 유저를 조회
  user = db.query(User).filter(User.std_id == std_id).first()
  
  if not user:
    raise HTTPException(status_code=404, detail="유저를 찾을 수 없습니다.")
  # 유저 정보 업데이트
  return user

@users_router.put('/{std_id}', response_model=UserSchema)
async def update_user(std_id: str, email:EmailStr, sign_url: str, db: Session = Depends(get_db)):
  # std_id에 해당하는 유저를 조회
  user = db.query(User).filter(User.std_id == std_id).first()
  
  if not user:
    raise HTTPException(status_code=404, detail="유저를 찾을 수 없습니다.")
  
  # 유저 정보 업데이트
  user.email = email
  user.sign_url = sign_url
  
  db.commit()
  db.refresh(user)
  
  return JSONResponse(status_code=200, content={'success': True, 'message': '유저 정보 업데이트'})

@users_router.delete('/{std_id}')
async def delete_user(std_id:str, db: Session = Depends(get_db)):
  
  # user_id에 해당하는 유저를 조회
  user = db.query(User).filter(User.std_id == std_id).first()
  
  # 해당 유저가 존재하지 않으면 404 에러 반환
  if not user:
    raise HTTPException(status_code=404, detail="유저를 찾을 수 없습니다.")
  
  # 유저 삭제
  db.delete(user)
  db.commit()

  return JSONResponse(status_code=200, content={'success': True, 'message': '유저 삭제'})

# 유저 로그인 API
@users_router.post('/signin', response_model=UserLogin)
async def login_user(loginData: UserLogin, db: Session = Depends(get_db)):

  user = db.query(User).filter(User.std_id == loginData.std_id).first()
  
  # 유저 검증
  if not user:
    raise HTTPException(status_code=400, detail="학번이 존재하지 않습니다.")
  
  # 해당 유저 비밀번호 검증
  if not pwd_context.verify(loginData.password, user.password):
    raise HTTPException(status_code=400, detail="잘못된 비밀번호입니다.")
  
  # JWT 생성
  token = create_jwt_token(user)
  
  # HTTP 응답 헤더에 토큰을 포함
  response = JSONResponse(content={"success": True, "message": "로그인 성공"}, media_type="application/json")
  response.headers["Authorization"] = f"Bearer {token}"
  return response
