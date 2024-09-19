import os
import requests
import base64
from server.auth import create_jwt_token
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from fastapi.responses import JSONResponse
from pydantic import EmailStr
from passlib.context import CryptContext
from server.models import User
# from server.models import User, School
# from server.models import get_skt_time
from server.schemas import UserSchema, UserLoginSchema
from server.db import get_db
# from server.schemas import UserSchema, UserCreate, UserLogin, VerifyEmail


univcert_url="https://univcert.com/api/v1"


UNIVCERT_API_KEY = os.getenv('UNIVCERT_API_KEY')
# 비밀번호 해싱
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

users_router = APIRouter(
  prefix="/v1/users"
)

# # 이메일 검증 API
# @users_router.post('/valid-email', summary="이메일을 통한 검증 및 인증코드 발송")
# async def check_email(inputData: VerifyEmail, db: Session = Depends(get_db)):


#   existing_user = db.query(User).filter(User.email == inputData.email).first()
#   if existing_user:
#     raise HTTPException(status_code=400, detail="중복된 이메일입니다.")
  
  
#   headers={
#     "Content-Type" : "application/json"
#   }
  
#   school = db.query(School).filter(School.id == inputData.school_id).first()
  
#   if inputData.verify_code is None:
#     # 인증 코드 발송
#     payload={
#       "key" : UNIVCERT_API_KEY,
#       "email" : inputData.email,
#       "univName" : f"{school.name}학교",
#       "univ_check" : True
#     }
    
#     try:
#       response = requests.post(f"{univcert_url}/certify", json=payload, headers=headers)
      
#       api_response = response.json()
      
#       if api_response.get('success') == True:
#         return JSONResponse(status_code=200, content={'success' : True, 'message' : '인증 메일이 발송되었습니다.'})
#       else:
#         return JSONResponse(status_code=400, content={'success' : False, 'message': api_response.get('message')})
      
#     except requests.exceptions.RequestException as e:
#       return JSONResponse(status_code=400, content={'success' : False, 'message' : e})
  
#   else:
#     # 인증 코드 검증
#     payload={
#       "key" : UNIVCERT_API_KEY,
#       "email" : inputData.email,
#       "univName" : f"{school.name}학교",
#       "code" : inputData.verify_code
#     }
    
#     try:
#       response = requests.post(f"{univcert_url}/certifycode", json=payload, headers=headers)
      
#       api_response = response.json()
#       print(api_response)
      
#       if api_response.get('success') == True:
#         return JSONResponse(status_code=200, content={'success' : True, 'message' : '인증 완료'})
#       else:
#         return JSONResponse(status_code=400, content={'success' : False, 'message' : api_response.get('message')})
      
#     except requests.exceptions.RequestException as e:
#       return JSONResponse(status_code=400, content={'success' : False, 'message' : e})
    
# @users_router.get('/valid-email/list', summary="검증된 이메일 리스트 조회")
# async def get_valid_email():
#   headers={
#     "Content-Type" : "application/json"
#   }
#   # 인증된 유저 목록 초기화
#   payload={
#     "key" : UNIVCERT_API_KEY,
#   }
  
#   response=requests.post(f"{univcert_url}/certifiedlist", json=payload, headers=headers)
#   api_response = response.json()
  
#   return JSONResponse(status_code=200, content={'success': True, 'message' : '목록 조회 완료', 'body': api_response})
  

# @users_router.post('/valid-email/reset', summary="검증된 이메일 초기화")
# async def reset_verify():
#   headers={
#     "Content-Type" : "application/json"
#   }
#   # 인증된 유저 목록 초기화
#   payload={
#     "key" : UNIVCERT_API_KEY,
#   }
#   response=requests.post(f"{univcert_url}/clear", json=payload, headers=headers)
  
#   if response.json().get('success') == True:
#     return JSONResponse(status_code=200, content={'success': True, 'message' : '목록 초기화 완료'})
#   else:
#     return JSONResponse(status_code=400, content={'success': False, 'message' : '목록 초기화 실패'})
    
# 유저 로그인 API
@users_router.post('/signin', summary="유저 로그인 기능")
async def login_user(login_data: UserLoginSchema, db: Session = Depends(get_db)):

  user = db.query(User).filter(User.std_id == login_data.std_id).first()
  
  # 유저 검증
  if not user:
    raise HTTPException(status_code=400, detail="학번이 존재하지 않습니다.")
  
  # 해당 유저 비밀번호 검증
  if not pwd_context.verify(login_data.password, user.password):
    raise HTTPException(status_code=400, detail="잘못된 비밀번호입니다.")
  
  # JWT 생성
  token = create_jwt_token(user)
  
  manager = True if user.role == 2 else False
  
  # 응답에 토큰을 포함
  response = JSONResponse(content={"success": True, "message": "로그인 성공", 'body' : token, 'user' : user.name, 'manager' : manager})
  return response

# # 유저 생성 API
# @users_router.post('/register', response_model=UserCreate, summary="유저 회원가입 기능")
# async def create_user(createData: UserCreate,db: Session = Depends(get_db)):
#   existing_user = db.query(User).filter(User.std_id == createData.std_id).first()
#   if existing_user:
#     raise HTTPException(status_code=400, detail="가입된 학번이 이미 존재합니다.")
  
#   existing_user = db.query(User).filter(User.email == createData.email).first()
#   if existing_user:
#     raise HTTPException(status_code=400, detail="중복된 이메일입니다.")
  
#   hashed_password = pwd_context.hash(createData.password)
  
#   # 사인 데이터 처리
#   if createData.sign_url:
#     try:
#       # Base64 인코딩 부분을 추출 및 디코딩
#       sign_data = createData.sign_url.split(",")[1]
#       sign_image_data = base64.b64decode(sign_data)
      
#       # 파일 이름 생성 및 파일 경로 지정
#       file_name = f"{createData.std_id}_sign.png"
#       file_path = os.path.join("server","static", "signatures", file_name)
      
#       # 이미지 데이터를 파일로 저장
#       with open(file_path, "wb") as f:
#         f.write(sign_image_data)
      
#       sign_url_data = f"/server/static/signatures/{file_name}"
#     except Exception as e:
#       raise HTTPException(status_code=500, detail="사인을 등록하지 못하였습니다")

#   else:
#     sign_url_data = None
  
#   # 새 일반 유저 객체 생성
#   new_user = User(
#     std_id=createData.std_id,
#     name=createData.name,
#     email=createData.email,
#     password=hashed_password,
#     school_id=createData.school_id,
#     sign_url=sign_url_data,
#     created_at=get_skt_time(),
#     role=1,
#   )
  
#   # 새 유저 등록
#   db.add(new_user)
#   db.commit()
#   db.refresh(new_user) # 새로 추가된 유저의 정보를 최신화
  
#   return JSONResponse(status_code=201, content={'success': True, 'message' : '계정 생성 완료'})


# 유저 전체 리스트 조회 API
@users_router.get('', response_model=list[UserSchema], summary="가입된 유저들 리스트 조회")
# Depends는 의존성 주입을 처리하는 코드 (다른 함수를 호출하고 그 결과를 가져와서 매개변수로 활용하는 것)
# Session은 SQLAlchemy에서 데이터베이스와의 모든 상호작용을 관리하는 주요 도구로 쿼리를 실행하거나, 트랜잭션을 관리하고, 변경 사항을 커밋함
async def read_users(db: Session = Depends(get_db)):
  users = db.query(User).all()
  
  return users
  # return JSONResponse(status_code=200, content={'success' : True, 'message' : '유저들 조회 완료', 'body' : userList})
#   #'_sa_instance_state': <sqlalchemy.orm.state.InstanceState object>는 SQLAlchemy ORM 객체를 그대로 출력하거나 JSON으로 변환하려고 할 대, 자동으로 추가하여 내부상태도 함께 출력됨.
#   # SQLAlchemy 모델 객체를 Pydantic모델로 변환해야함

# 유저 한 명 조회 API
@users_router.get('/{std_id}', response_model=UserSchema, summary="학번을 통해 가입된 유저 조회")
async def read_user(std_id: str, db: Session = Depends(get_db)):
  # std_id에 해당하는 유저를 조회
  user = db.query(User).filter(User.std_id == std_id).first()
  print(user)
  
  if not user:
    raise HTTPException(status_code=404, detail="유저를 찾을 수 없습니다.")
  # 유저 정보 업데이트
  return user

# @users_router.put('/{std_id}', response_model=UserSchema, summary="학번을 통한 유저의 email과 sign 정보 수정")
# async def update_user(std_id: str, email:EmailStr, sign_url: str, db: Session = Depends(get_db)):
#   # std_id에 해당하는 유저를 조회
#   user = db.query(User).filter(User.std_id == std_id).first()
  
#   if not user:
#     raise HTTPException(status_code=404, detail="유저를 찾을 수 없습니다.")
  
#   # 유저 정보 업데이트
#   user.email = email
#   user.sign_url = sign_url
  
#   db.commit()
#   db.refresh(user)
  
#   return JSONResponse(status_code=200, content={'success': True, 'message': '유저 정보 업데이트'})

# @users_router.delete('/{std_id}', summary="학번을 통한 유저 삭제")
# async def delete_user(std_id:str, db: Session = Depends(get_db)):
  
#   # user_id에 해당하는 유저를 조회
#   user = db.query(User).filter(User.std_id == std_id).first()
  
#   # 해당 유저가 존재하지 않으면 404 에러 반환
#   if not user:
#     raise HTTPException(status_code=404, detail="유저를 찾을 수 없습니다.")
  
#   # 유저 삭제
#   db.delete(user)
#   db.commit()

#   return JSONResponse(status_code=200, content={'success': True, 'message': '유저 삭제'})

