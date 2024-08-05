from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr
from datetime import datetime
from passlib.context import CryptContext

# 비밀번호 해싱을 위한 설정
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 가짜 데이터베이스
fake_db = []

class UserCreate(BaseModel):
  uid: int
  std_id: str
  name: str
  email: EmailStr
  password: str
  sign_url: str
  created_at: datetime

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class User(BaseModel):
  uid: int
  std_id: str
  name: str
  email: EmailStr
  sign_url: str
  created_at: datetime
  

users_router = APIRouter(
  prefix="/user"
)

def get_user_by_email(email:str):
  for user in fake_db:
    if user['email'] == email:
      return user
  return None

@users_router.get('')
async def get_users():
  users_list = [User(**user).dict() for user in fake_db]
  return JSONResponse(status_code=200, content={'success' : True, 'message' : '유저들 조회 완료', 'body' : users_list})

@users_router.post('/check-email')
async def check_email(email: EmailStr):
  existing_user = get_user_by_email(email)
  print(existing_user)
  if existing_user:
    return JSONResponse(status_code=400, content={'success' : False, 'message' : '이메일 중복'})
  return JSONResponse(status_code=200, content={'success' : True, 'message' : '가입 가능한 이메일'})

@users_router.post('/signup')
async def create_user(user: UserCreate):
    hashed_password = pwd_context.hash(user.password)
    
    user_data = user.dict()
    user_data['password'] = hashed_password
    fake_db.append(user_data)
    
    return JSONResponse(status_code=201, content={'success': True, 'message': '계정 생성 완료'})

@users_router.post('/login')
async def login(user: UserLogin):
    db_user = get_user_by_email(user.email)
    if not db_user:
        raise HTTPException(status_code=400, detail="Invalid email or password")
    
    if not pwd_context.verify(user.password, db_user["password"]):
        raise HTTPException(status_code=400, detail="Invalid email or password")

    return JSONResponse(status_code=200, content={"success": True, "message": "Login successful", "user": User(**db_user)})
