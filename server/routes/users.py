import os
import requests
import base64
import hmac
import hashlib
import re
import json
from server.auth import create_jwt_token
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from fastapi.responses import JSONResponse
from pydantic import EmailStr
from passlib.context import CryptContext
from server.models import User, UserFavoriteStore, Store
# from server.models import User, School
# from server.models import get_skt_time
from server.schemas import UserSchema, UserLoginSchema, StoreListSchema, UserCreateSchema
from server.db import get_db
from server.auth import verify_jwt_token
from server.utils import get_skt_time
import time
# from server.schemas import UserSchema, UserCreate, UserLogin, VerifyEmail


univcert_url="https://univcert.com/api/v1"


UNIVCERT_API_KEY = os.getenv('UNIVCERT_API_KEY')
NAVER_CLOUD_ACCESS_KEY = os.getenv('NAVER_CLOUD_ACCESS_KEY')
NAVER_CLOUD_SECRET_KEY = os.getenv('NAVER_CLOUD_SECRET_KEY')
NOTIFICATION_SERVICE_ID = os.getenv('NOTIFICATION_SERVICE_ID')


URL = "https://sens.apigw.ntruss.com"
URI = f"/sms/v2/services/{NOTIFICATION_SERVICE_ID}/messages"

# 비밀번호 해싱
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

users_router = APIRouter(
  prefix="/v1/users"
)



def makeSignature():
  access_key=NAVER_CLOUD_ACCESS_KEY
  secret_key=NAVER_CLOUD_SECRET_KEY
  
  timestamp = int(time.time() * 1000)
  timestamp = str(timestamp)

  secret_key=bytes(secret_key, 'UTF-8')
  method = "POST"
  
  message = method + " " + URI + "\n" + timestamp + "\n" + access_key
  message = bytes(message, 'UTF-8')
  
  signingKey = base64.b64encode(hmac.new(secret_key, message, digestmod=hashlib.sha256).digest())
  return signingKey
  

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
  # 추후에 User모델에 Store연결해서 sid값 저장해서 보내줘야 함.
  store_sid = user.store_id if manager else None
  
  # 응답에 토큰을 포함
  response = JSONResponse(content={"success": True, "message": "로그인 성공", 'body' : token, 'user' : user.name, 'manager' : manager, 'sid' : store_sid})
  return response

# 유저 생성 API
@users_router.post('/register', response_model=UserCreateSchema, summary="유저 회원가입 기능")
async def create_user(createData: UserCreateSchema,db: Session = Depends(get_db)):
  existing_user = db.query(User).filter(User.std_id == createData.std_id).first()
  if existing_user:
    raise HTTPException(status_code=400, detail="가입된 학번이 이미 존재합니다.")
  
  existing_user = db.query(User).filter(User.phone_number == createData.phone_number).first()
  if existing_user:
    raise HTTPException(status_code=400, detail="이미 인증된 전화번호가 있습니다.")
  
  hashed_password = pwd_context.hash(createData.password)
  
  # 사인 데이터 처리
  if createData.sign_url:
    try:
      # Base64 인코딩 부분을 추출 및 디코딩
      sign_data = createData.sign_url.split(",")[1]
      sign_image_data = base64.b64decode(sign_data)
      
      # 파일 이름 생성 및 파일 경로 지정
      file_name = f"{createData.std_id}_sign.png"
      file_path = os.path.join("server","static", "signatures", file_name)
      
      # 이미지 데이터를 파일로 저장
      with open(file_path, "wb") as f:
        f.write(sign_image_data)
      
      sign_url_data = f"/server/static/signatures/{file_name}"
    except Exception as e:
      raise HTTPException(status_code=500, detail="사인을 등록하지 못하였습니다")

  else:
    sign_url_data = None
  
  # 새 일반 유저 객체 생성
  new_user = User(
    std_id=createData.std_id,
    name=createData.name,
    # email=createData.email,
    phone_number=createData.phone_number,
    password=hashed_password,
    school_id=createData.school_id,
    sign_url=sign_url_data,
    created_at=get_skt_time(),
    role=1,
  )
  
  # 새 유저 등록
  db.add(new_user)
  db.commit()
  db.refresh(new_user) # 새로 추가된 유저의 정보를 최신화
  
  return JSONResponse(status_code=201, content={'success': True, 'message' : '계정 생성 완료'})

# 유저 핸드폰 번호 중복검사 및 인증번호 검증
@users_router.post('/verification', summary='유저 휴대폰번호 중복체크 및 인증번호 검증')
async def verification_phone(phone_number: str ,db: Session = Depends(get_db)):
  
  if not re.fullmatch(r"^010\d{8}$", phone_number):
    raise HTTPException(status_code=400, detail="휴대폰 번호 형식이 올바르지 않습니다. 010으로 시작하는 11자리 번호를 입력하세요.")
  
  timestamp = int(time.time() * 1000)
  timestamp = str(timestamp)
  
  existing_user = db.query(User).filter(User.phone_number == phone_number).first()
  if existing_user:
    raise HTTPException(status_code=400, detail="이미 인증된 전화번호가 있습니다.")
  
  # signature = makeSignature()
  
  # print(signature)
  
  # header={
  #   "Content-Type" : "application/json",
  #   'x-ncp-apigw-timestamp' : timestamp,
  #   'x-ncp-iam-access-key' : NAVER_CLOUD_ACCESS_KEY,
  #   'x-ncp-apigw-signature-v2' : signature,
  # }
  
  # data={
  #   "type" : "SNS",
  #   "from" : "",
  #   "subject" : "학식모지 인증번호 테스트",
  #   "content" : "[인증번호] 1234",
  #   "messages" : [
  #     {
  #       "to": phone_number,
  #     }
  #   ]
  # }
  
  # try:
  #   response = requests.post(URL+URI, headers=header, data=json.dumps(data))
  #   print(response.text)
  # except requests.exceptions.HTTPError as e:
  #   print('HTTP 에러 발생', e)
  #   print('응답 상태 코드:', response.status_code)
  #   print("응답 본문", response.text)
  #   return JSONResponse(status_code=response.status_code, content={'success':False, 'message': response.text})
  # except requests.exceptions.RequestException as e:
  #   print(e)
  #   return JSONResponse(status_code=400, content={'success': False, 'message' : '인증번호 인증 실패'})
  
  return JSONResponse(status_code=200, content={'success': True, 'message' : '휴대폰번호 검증 완료'})


# 유저 전체 리스트 조회 API
@users_router.get('', response_model=list[UserSchema], summary="가입된 유저들 리스트 조회")
async def read_users(db: Session = Depends(get_db)):
    # 모든 유저 조회
    users = db.query(User).all()

    # 결과 저장을 위한 리스트
    user_list = []

    # 각 유저의 즐겨찾기 매장을 포함한 데이터를 구성
    for user in users:
        favorite_store_records = db.query(UserFavoriteStore).filter(UserFavoriteStore.uid == user.uid).all()

        # 각 유저의 favorite_stores 정보 저장
        favorite_stores = []
        for favorite in favorite_store_records:
            store = db.query(Store).filter(Store.sid == favorite.store_id).first()
            if store:
                favorite_stores.append(StoreListSchema(
                    sid=store.sid,
                    store_name=store.store_name,
                    store_number=store.store_number,
                    store_location=store.store_location,
                    store_img_url=store.store_img_url,
                    is_open=store.is_open,
                    category=store.category
                ))

        # 유저 데이터를 UserSchema로 변환
        user_data = UserSchema(
            uid=user.uid,
            std_id=user.std_id,
            name=user.name,
            phone_number=user.phone_number,
            # email=user.email,
            password=user.password,
            school=user.school,
            sign_url=user.sign_url,
            created_at=user.created_at,
            role=user.role,
            favorite_stores=favorite_stores,  # 즐겨찾기한 매장 리스트 추가
            store_id=user.store_id
        )

        # 결과 리스트에 추가
        user_list.append(user_data)

    return user_list
  # return JSONResponse(status_code=200, content={'success' : True, 'message' : '유저들 조회 완료', 'body' : userList})
#   #'_sa_instance_state': <sqlalchemy.orm.state.InstanceState object>는 SQLAlchemy ORM 객체를 그대로 출력하거나 JSON으로 변환하려고 할 대, 자동으로 추가하여 내부상태도 함께 출력됨.
#   # SQLAlchemy 모델 객체를 Pydantic모델로 변환해야함


# 현재 로그인 된 유저 정보 조회
@users_router.get('/me', response_model=UserSchema, summary="현재 로그인 된 유저 조회")
async def read_current_user(db: Session = Depends(get_db), token: str = Depends(verify_jwt_token)):
  # std_id에 해당하는 유저를 조회
  user = db.query(User).filter(User.uid == token.uid).first()

  if not user:
      raise HTTPException(status_code=404, detail="로그인 유저를 찾을 수 없습니다.")

  # 유저의 즐겨찾기 매장 가져오기
  favorite_store_records = db.query(UserFavoriteStore).filter(UserFavoriteStore.uid == user.uid).all()
  # Favorite 조회 에러 수정해야 함
  
  # Store 정보 추출 및 StoreSchema로 변환
  favorite_stores = []
  for favorite in favorite_store_records:
      store = db.query(Store).filter(Store.sid == favorite.store_id).first()
      
      if store:
        favorite_stores.append(StoreListSchema(sid=store.sid, store_name=store.store_name, store_number=store.store_number, store_location=store.store_location, store_img_url=store.store_img_url, is_open=store.is_open, category=store.category))

  # UserSchema로 변환할 때 favorite_stores 필드에 매장 리스트 추가
  user_data = UserSchema(
    uid=user.uid,
    std_id=user.std_id,
    name=user.name,
    # email=user.email,
    phone_number=user.phone_number,
    password=user.password,
    school=user.school,
    sign_url=user.sign_url,
    created_at=user.created_at,
    role=user.role,
    favorite_stores=favorite_stores,  # 즐겨찾기한 매장 리스트 추가
    store_id=user.store_id
  )

  return user_data



# 유저 한 명 조회 API
@users_router.get('/{std_id}', response_model=UserSchema, summary="학번을 통해 가입된 유저 조회")
async def read_user(std_id: str, db: Session = Depends(get_db)):
  # std_id에 해당하는 유저를 조회
  user = db.query(User).filter(User.std_id == std_id).first()

  if not user:
      raise HTTPException(status_code=404, detail="유저를 찾을 수 없습니다.")

  # 유저의 즐겨찾기 매장 가져오기
  favorite_store_records = db.query(UserFavoriteStore).filter(UserFavoriteStore.uid == user.uid).all()
  # Favorite 조회 에러 수정해야 함
  # Store 정보 추출 및 StoreSchema로 변환
  favorite_stores = []
  for favorite in favorite_store_records:
      store = db.query(Store).filter(Store.sid == favorite.store_id).first()
      
      if store:
        favorite_stores.append(StoreListSchema(sid=store.sid, store_name=store.store_name, store_number=store.store_number, store_location=store.store_location, store_img_url=store.store_img_url, is_open=store.is_open, category=store.category))

  # UserSchema로 변환할 때 favorite_stores 필드에 매장 리스트 추가
  user_data = UserSchema(
    uid=user.uid,
    std_id=user.std_id,
    name=user.name,
    phone_number=user.phone_number,
    # email=user.email,
    password=user.password,
    school=user.school,
    sign_url=user.sign_url,
    created_at=user.created_at,
    role=user.role,
    favorite_stores=favorite_stores  # 즐겨찾기한 매장 리스트 추가
  )

  return user_data

# @users_router.put('', response_model=UserSchema, summary="학번을 통한 유저의 email과 sign 정보 수정")
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

@users_router.delete('', summary="학번을 통한 유저 삭제")
async def delete_user(db: Session = Depends(get_db), token: str = Depends(verify_jwt_token)):
  # user_id에 해당하는 유저를 조회
  user = db.query(User).filter(User.uid == token.uid).first()
  
  # 해당 유저가 존재하지 않으면 404 에러 반환
  if not user:
    raise HTTPException(status_code=404, detail="유저를 찾을 수 없습니다.")
  
  # 유저 삭제
  db.delete(user)
  db.commit()

  return JSONResponse(status_code=200, content={'success': True, 'message': '유저 삭제'})

