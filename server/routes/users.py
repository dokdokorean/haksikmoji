import random
import os
import requests
import base64
import hmac
import hashlib
import re
import json
import certifi
from server.auth import create_jwt_token
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from fastapi.responses import JSONResponse
from pydantic import EmailStr
from passlib.context import CryptContext
from server.models import User, UserFavoriteStore, Store
# from server.models import User, School
# from server.models import get_skt_time
from server.schemas import UserSchema, UserLoginSchema, StoreListSchema, UserCreateSchema, UserSignSchema, UserStdSchema, VerifyPhoneNum
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

KAKAO_ACCESS_TOKEN = os.getenv('KAKAO_ACCESS_TOKEN')
YONSEI_AUTH_URL = os.getenv('YONSEI_AUTH_URL')

INFO_BANK_URL=os.getenv('INFO_BANK_URL')
INFO_BANK_TEMPLATE_CODE=os.getenv('INFO_BANK_TEMPLATE_CODE')
INFO_BANK_SENDER_KEY=os.getenv('INFO_BANK_SENDER_KEY')

INFO_BANK_IB_ID=os.getenv('INFO_BANK_IB_ID')
INFO_BANK_IB_PW=os.getenv('INFO_BANK_IB_PW')

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
@users_router.post('/register', summary="유저 회원가입 기능")
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
      file_path = os.path.join("server","static", str(createData.school_id),"signatures", file_name)
      os.makedirs(os.path.dirname(file_path), exist_ok=True)
      
      # 이미지 데이터를 파일로 저장
      with open(file_path, "wb") as f:
        f.write(sign_image_data)
      
      sign_url_data = f"/server/static/{str(createData.school_id)}/signatures/{file_name}"
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
    marketing_term=createData.marketing_term,
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
async def verification_phone(input_data: VerifyPhoneNum ,db: Session = Depends(get_db)):
  
  if not re.fullmatch(r"^010\d{8}$", input_data.phone_number):
    raise HTTPException(status_code=400, detail="휴대폰 번호 형식이 올바르지 않습니다. 010으로 시작하는 11자리 번호를 입력하세요.")
  
  timestamp = int(time.time() * 1000)
  timestamp = str(timestamp)
  
  existing_user = db.query(User).filter(User.phone_number == input_data.phone_number).first()
  if existing_user:
    raise HTTPException(status_code=400, detail="이미 인증된 전화번호가 있습니다.")
  
  # 인증번호
  verify_code = str(random.randint(0, 999999)).zfill(6)
  
  token_payload={}
  token_headers={
    'X-IB-Client-Id' : INFO_BANK_IB_ID,
    'X-IB-Client-Passwd' : INFO_BANK_IB_PW,
    'Accept' : 'application/json'
  }
  
  # 토큰 가져오기
  try:
    token_response = requests.post(f"{INFO_BANK_URL}/v1/auth/token", headers=token_headers, data=token_payload)
    
    token_response = token_response.json()
    
    if token_response.get('result') == 'Success':
      token = token_response.get('data', {}).get('token')
      schema = token_response.get('data', {}).get('schema')
      
      
      alim_headers={
        "Authorization" : f"{schema} {token}",
        "Content-Type" : "application/json",
        "Accept" : "application/json"
      }
      
      alim_payload=json.dumps({
        "senderKey" : INFO_BANK_SENDER_KEY,
        "msgType" : "AT",
        "to" : input_data.phone_number,
        "templateCode" : INFO_BANK_TEMPLATE_CODE,
        "text" : 
          f"[학식모지] \n\n본인확인을 위해 인증번호 [{verify_code}]를 입력해주세요."
      })
      
      try:
        alim_response = requests.post(f"{INFO_BANK_URL}/v1/send/alimtalk", headers=alim_headers, data=alim_payload)
        
        print(alim_response.text)
        
        
      except:
        print("error")
        raise HTTPException(status_code=500, detail="서버오류로 인증번호를 보내지 못하였습니다. 다시 시도해주세요.")
      
      
  except:
    print("error")
    raise HTTPException(status_code=500, detail="서버오류로 토큰을 발급하지 못하였습니다. 다시 시도해주세요.")
    
  # 인증번호도 함께 담아서 전송
  return JSONResponse(status_code=200, content={'success': True, 'message' : '정상적으로 인증번호를 발송하였습니다!', 'body': verify_code})

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
                    store_thumb_url=store.store_thumb_url, 
                    store_banner_url=store.store_banner_url,
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
            marketing_term=user.marketing_term,
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
        favorite_stores.append(StoreListSchema(sid=store.sid, store_name=store.store_name, store_number=store.store_number, store_location=store.store_location, store_thumb_url=store.store_thumb_url, store_banner_url=store.store_banner_url, is_open=store.is_open, category=store.category))

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
    marketing_term=user.marketing_term,
    created_at=user.created_at,
    role=user.role,
    favorite_stores=favorite_stores,  # 즐겨찾기한 매장 리스트 추가
    store_id=user.store_id
  )

  return user_data

@users_router.put('/me/password', summary="현재 로그인된 유저 비밀번호 수정")
async def update_password(current_paassword: str, new_password: str, db: Session = Depends(get_db), token: str = Depends(verify_jwt_token)):
  
  # std_id에 해당하는 유저를 조회
  user = db.query(User).filter(User.uid == token.uid).first()
  
  # 현재 로그인 된 유저 조회
  if not user:
    raise HTTPException(status_code=404, detail="로그인 유저를 찾을 수 없습니다.")
  
  # 현재 비밀번호가 맞는지 검증
  if not pwd_context.verify(current_paassword, user.password):
    raise HTTPException(status_code=400, detail="현재 비밀번호가 올바르지 않습니다")
  
  # 새로운 비밀번호와 기존 비밀번호가 동일하면 예외처리
  if pwd_context.verify(new_password, user.password):
    raise HTTPException(status_code=400, detail="새로운 비밀번호는 기존 비밀번호와 동일할 수 없습니다.")
  
  hashed_password = pwd_context.hash(new_password)
  user.password = hashed_password
  
  db.commit()
  db.refresh(user)
  
  return JSONResponse(status_code=200, content={'success': True, 'message': '비밀번호 수정 완료'})

@users_router.put('/me/sign', summary="현재 로그인된 유저 사인 수정")
async def update_sign(sign_update_url: UserSignSchema, db: Session = Depends(get_db), token: str = Depends(verify_jwt_token)):
  
  # std_id에 해당하는 유저를 조회
  user = db.query(User).filter(User.uid == token.uid).first()
  
  # 현재 로그인 된 유저 조회
  if not user:
    raise HTTPException(status_code=404, detail="로그인 유저를 찾을 수 없습니다.")
  
  # 사인 데이터 처리
  try:
    # Base64 인코딩 부분을 추출 및 디코딩
    sign_data = sign_update_url.sign_url.split(",")[1]
    sign_image_data = base64.b64decode(sign_data)
    
    # 파일 이름 생성 및 파일 경로 지정
    file_name = f"{user.std_id}_sign.png"
    file_path = os.path.join("server","static", str(user.school.id),"signatures", file_name)
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    # 이미지 데이터를 파일로 저장
    with open(file_path, "wb") as f:
      f.write(sign_image_data)
    
    sign_url_data = f"/server/static/{str(user.school.id)}/signatures/{file_name}"
  except Exception as e:
    raise HTTPException(status_code=500, detail="사인을 등록하지 못하였습니다")
  
  
  user.sign_url = sign_url_data
  
  db.commit()
  db.refresh(user)
  
  return JSONResponse(status_code=200, content={'success': True, 'message': '사인 수정 완료'})



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
    marketing_term=user.marketing_term,
    created_at=user.created_at,
    role=user.role,
    favorite_stores=favorite_stores  # 즐겨찾기한 매장 리스트 추가
  )

  return user_data

@users_router.delete('', summary="현재 로그인 된 유저 삭제")
async def delete_user(pw:str, db: Session = Depends(get_db), token: str = Depends(verify_jwt_token)):
  # user_id에 해당하는 유저를 조회
  user = db.query(User).filter(User.uid == token.uid).first()
  
  # 해당 유저가 존재하지 않으면 404 에러 반환
  if not user:
    raise HTTPException(status_code=404, detail="유저를 찾을 수 없습니다.")
  
  if pwd_context.verify(pw, user.password):
    db.delete(user)
    db.commit()
  else:
    raise HTTPException(status_code=404, detail="비밀번호가 틀렸습니다!")

  return JSONResponse(status_code=200, content={'success': True, 'message': '유저 삭제'})

@users_router.post('/stdIdValidation', summary="학번 인증 API")
async def validation_student(input_data: UserStdSchema):
  
  headers = {
    'Content-Type' : 'application/json'
  }
  
  params = {
    'uid' : input_data.std_id
  }
  
  try:
    response = requests.get(f'{YONSEI_AUTH_URL}/ywis/admin/yonsei_check.jsp', headers=headers, params=params, verify=True)
    
    if response.status_code != 200:
      raise HTTPException(status_code=500, detail=f"요청 실패: {response.status_code}")
    
    student_state = response.json()
    
    if not student_state.get('name'):
      return JSONResponse(status_code=200, content={'success': False, 'body': student_state, 'message': '교내에 존재하지 않는 사용자'})
    
  except Exception as e:
    print(f'서버 오류: {e}')
    raise HTTPException(status_code=500, detail="유저 정보 조회 불가능")
  
  return JSONResponse(status_code=200, content={'success': True, 'body': student_state})
