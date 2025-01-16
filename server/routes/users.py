import random
import os
import requests
import base64
import re
import json
import time

from sqlalchemy.orm import Session
from pydantic import EmailStr
from passlib.context import CryptContext

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from server.auth import create_jwt_token
from server.models import User, UserFavoriteStore, Store, School
from server.schemas import UserSchema, UserLoginSchema, StoreListSchema, UserCreateSchema, UserSignSchema, VerifyPhoneNum, VerifyId, VerifySchool, VerifyEmail
from server.db import get_db

from server.util.custom_exception import CustomHTTPException
from server.util.auth import verify_jwt_token
from server.util.time import get_skt_time
from server.util.config import KAKAO_ACCESS_TOKEN, INFO_BANK_URL, INFO_BANK_TEMPLATE_CODE, INFO_BANK_SENDER_KEY, INFO_BANK_IB_ID, INFO_BANK_IB_PW, UNIVCERT_API_KEY, UNIVCERT_URL

# 비밀번호 해싱
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

users_router = APIRouter(
  prefix="/v1/users"
)
    
    
# 유저 로그인 API
@users_router.post('/login', summary="001. 유저 로그인 기능")
async def login_user(login_data: UserLoginSchema, db: Session = Depends(get_db)):

  # 일치하는 유저 탐색
  user = db.query(User).filter(User.user_id == login_data.user_id).first()
  
  # 사용자가 없을 시 처리
  if not user:
    raise CustomHTTPException(status_code=404, message="존재하지 않는 사용자입니다.")
  
  # 해당 유저 비밀번호 검증
  if not pwd_context.verify(login_data.user_pw, user.user_pw):
    raise CustomHTTPException(status_code=400, message="잘못된 비밀번호입니다.")
  
  # JWT 생성
  token = create_jwt_token(user)
  
  # 로그인한 사용자의 역할에 따른 매니저 여부
  # role : 1 => 일반 사용자
  # role : 2 => 매장 사장님
  # role : 3 => 쿠폰 관리자(교직원)
  # TODO: 쿠폰 관리자도 manager로 부여해야하는지 확인
  manager = True if user.role == 2 else False
  
  # 매니저일 시 운영하고 있는 매장 id
  store_sid = user.store_id if manager else None
  
  response = JSONResponse(status_code=200, content={
    "status" : 200,
    "isSuccess" : True,
    "message" : f"로그인 완료",
    "result": {
      "user" : user.name,
      "accessToken" : token,
      "manager" : manager,
      "sid" : store_sid,
    },
  })
  
  return response



# 유저 생성 API
@users_router.post('/signup', summary="002. 유저 회원가입 기능")
async def create_user(create_data: UserCreateSchema, db: Session = Depends(get_db)):
  
  # 아이디 중복 확인
  existing_user = db.query(User).filter(User.user_id == create_data.user_id).first()
  if existing_user:
    raise CustomHTTPException(status_code=409, message="이미 존재하는 아이디입니다.")
  
  # 전화번호 중복 확인
  existing_user = db.query(User).filter(User.phone_number == create_data.phone_number).first()
  if existing_user:
    raise CustomHTTPException(status_code=409, message="이미 인증된 전화번호입니다.")
  
  # 생년월일 검증
  if not create_data.user_birth or create_data.user_birth.strip() == "":
      raise CustomHTTPException(status_code=400, message="생년월일은 필수 입력 항목입니다. 올바른 값을 입력하세요.")
  
  
  # 비밀번호 암호화
  hashed_password = pwd_context.hash(create_data.user_pw)
  
  # 새 일반 유저 객체 생성
  new_user = User(
    name=create_data.name,
    user_id=create_data.user_id,
    user_pw=hashed_password,
    user_birth=create_data.user_birth,
    std_id=None,              # 기본값
    email="",                 # 기본값
    major=None,               # 기본값
    gender=create_data.gender,
    phone_number=create_data.phone_number,
    is_school_selected=create_data.is_school_selected,
    is_school_verified=False, # 기본값
    sign_url=None,            # 기본값
    marketing_term=create_data.marketing_term,
    created_at=get_skt_time(),
    role=1,                   # 기본값
  )
  
  # 새 유저 등록 및 유저 정보 최신화
  db.add(new_user)
  db.commit()
  db.refresh(new_user) 
  
  response = JSONResponse(status_code=201, content={
    "status" : 201,
    "isSuccess" : True,
    "message" : f"{new_user.name}님의 계정이 생성되었습니다.",
    "result": None,
  })
  
  return response

# 유저 핸드폰 번호 중복검사 및 인증번호 검증
@users_router.post('/verification/phone', summary='003. 유저 휴대폰번호 중복체크 및 인증번호 검증')
async def verification_phone(input_data: VerifyPhoneNum ,db: Session = Depends(get_db)):
  
  if not re.fullmatch(r"^010\d{8}$", input_data.phone_number):
    raise CustomHTTPException(status_code=422, message="휴대폰 번호 형식이 올바르지 않습니다. 010으로 시작하는 11자리 번호를 입력하세요.")
  
  
  timestamp = int(time.time() * 1000)
  timestamp = str(timestamp)
  
  existing_user = db.query(User).filter(User.phone_number == input_data.phone_number).first()
  if existing_user:
    raise CustomHTTPException(status_code=409, message="이미 인증된 전화번호가 있습니다.")
  
  # TODO: 카카오 비즈메세지에서 드림시큐리티 인증으로 변경 예정
  # 인증번호
  verify_code = str(random.randint(0, 999999)).zfill(6)
  
  # 비즈고 요청 헤더
  token_headers={
    'X-IB-Client-Id' : INFO_BANK_IB_ID,
    'X-IB-Client-Passwd' : INFO_BANK_IB_PW,
    'Accept' : 'application/json'
  }
  
  # 비즈고 토큰 발급
  try:
    token_response = requests.post(f"{INFO_BANK_URL}/v1/auth/token", headers=token_headers)
    
    
    token_response = token_response.json()
    
    # 토큰 발급 완료시
    if token_response.get('result') == 'Success':
      token = token_response.get('data', {}).get('token')
      schema = token_response.get('data', {}).get('schema')
      
      # 카카오 비즈메세지 알림톡 요청 헤더
      alim_headers={
        "Authorization" : f"{schema} {token}",
        "Content-Type" : "application/json",
        "Accept" : "application/json"
      }
      
      # 카카오 비즈메세지 알림톡 요청 바디
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
        raise CustomHTTPException(status_code=500, message="서버오류로 인증번호를 보내지 못하였습니다. 다시 시도해주세요.")
      
      
  except:
    raise CustomHTTPException(status_code=500, message="서버오류로 인증번호를 보내지 못하였습니다. 다시 시도해주세요.")
  
    
  # 인증번호도 함께 담아서 전송
  response = JSONResponse(status_code=200, content={
    "status" : 200,
    "isSuccess" : True,
    "message" : f"인증번호가 요청되었습니다.",
    "result": {
      "code" : verify_code
    },
  })
  
  return response

# 아이디 중복 체크
@users_router.post('/verification/id', summary='004. 유저 아이디 중복 검증')
async def verification_id(input_data:VerifyId, db: Session = Depends(get_db)):
  
  # 아이디 중복 확인
  existing_user = db.query(User).filter(User.user_id == input_data.user_id).first()
  if existing_user:
    raise CustomHTTPException(status_code=409, message="이미 존재하는 아이디입니다.")
  
  response = JSONResponse(status_code=200, content={
    "status" : 200,
    "isSuccess" : True,
    "message" : f"가입 가능한 아이디입니다.",
    "result": None,
  })
  
  return response


@users_router.post('/verification/school', summary="005. 학교 인증")
async def verified_school(input_data: VerifySchool, db: Session = Depends(get_db), token: str = Depends(verify_jwt_token)):
  
  # token의 uid에 해당하는 유저를 조회
  user = db.query(User).filter(User.uid == token.uid).first()
  
  # 사용자가 없을 시 처리
  if not user:
    raise CustomHTTPException(status_code=404, message="존재하지 않는 사용자입니다.")
  
  try:
    # 유저 정보 업데이트
    if user.email != "" and user.school_id is not None:
      user.major = input_data.major
      user.std_id = input_data.std_id
      user.is_school_verified = True
      
      db.commit()
      db.refresh(user)
      
      response = JSONResponse(status_code=200, content={
        "status": 200,
        "isSuccess": True,
        "message": "성공적으로 학교 인증이 완료되었습니다.",
        "result": {
          "uid": user.uid,
          "school_id": user.school_id,
          "email": user.email,
          "major": user.major,
          "std_id": user.std_id,
          "is_school_verified": user.is_school_verified,
        },
      })
    else:
      response = JSONResponse(status_code=400, content={
        "status": 400,
        "isSuccess": False,
        "message": "학교 이메일이 인증되지 않았습니다.",
        "result": None,
      })
  except Exception as e:
    raise CustomHTTPException(status_code=500, message="학교 인증 중 문제가 발생했습니다.")
  
  return response

@users_router.get('/verification/email', summary='[TEST용] 학교 이메일 인증 리스트 조회')
async def verified_email():
  try:
    
    headers={
      "Content-Type" : "application/json",
    }
    
    payload={
      "key" : UNIVCERT_API_KEY
    }
    
    email_response = requests.post(f"{UNIVCERT_URL}/certifiedlist", json=payload, headers=headers)
    email_response = email_response.json()
    
    if email_response.get('success') == True:
      response = JSONResponse(status_code=200, content={
        "status" : 200,
        "isSuccess" : True,
        "message" : f"조회가 완료되었습니다",
        "result": email_response.get('data'),
      })
      
    else:
      response = JSONResponse(status_code=400, content={
        "status" : 400,
        "isSuccess" : False,
        "message" : email_response.get('message'),
        "result": None,
      })
    
  except:
    response = JSONResponse(status_code=500, content={
      "status" : 500,
      "isSuccess" : False,
      "message" : f"서버오류 - 관리자에게 문의바람",
      "result": None,
    })
  
  return response

@users_router.post('/verification/email', summary='006. 학교 이메일 인증', description="이메일만 먼저 post요청 보낸 후 이후에 이메일과 인증코드를 함께 요청하면 인증 결과가 나옴")
async def verification_email(input_data:VerifyEmail, db: Session = Depends(get_db), token: str = Depends(verify_jwt_token)):
  
  # token의 uid에 해당하는 유저를 조회
  user = db.query(User).filter(User.uid == token.uid).first()
  
  if not user:
    raise CustomHTTPException(status_code=404, message="로그인 된 유저를 찾을 수 없습니다.")
  
  existing_user = db.query(User).filter(User.email == input_data.email).first()
  if existing_user and existing_user.uid != token.uid:
    raise CustomHTTPException(
        status_code=409,
        message="이미 사용 중인 이메일입니다. 다른 이메일을 입력해주세요."
    )
  
  school = db.query(School).filter(School.id == input_data.school_id).first()
  
  if input_data.verify_code is None:
    try:
      
      headers={
        "Content-Type" : "application/json",
      }
      
      payload={
        "key" : UNIVCERT_API_KEY,
        "email" : input_data.email,
        "univName" : f"{school.name}학교",
        "univ_check" : True
      }
      
      email_response = requests.post(f"{UNIVCERT_URL}/certify", json=payload, headers=headers)
      email_response = email_response.json()
      
      if email_response.get('success') == True:
        response = JSONResponse(status_code=200, content={
          "status" : 200,
          "isSuccess" : True,
          "message" : f"인증 메일이 발송되었습니다.",
          "result": None,
        })
        
      else:
        response = JSONResponse(status_code=400, content={
          "status" : 400,
          "isSuccess" : False,
          "message" : email_response.get('message'),
          "result": None,
        })
      
    except:
      response = JSONResponse(status_code=500, content={
        "status" : 500,
        "isSuccess" : False,
        "message" : f"서버오류 - 관리자에게 문의바람",
        "result": None,
      })
  else:
    try:
      headers={
        "Content-Type" : "application/json",
      }
      
      payload={
        "key" : UNIVCERT_API_KEY,
        "email" : input_data.email,
        "univName" : f"{school.name}학교",
        "code" : input_data.verify_code
      }
      
      verify_response = requests.post(f"{UNIVCERT_URL}/certifycode", json=payload, headers=headers)
      verify_response = verify_response.json()
      
      if verify_response.get('success') == True:
        
        user.school_id = input_data.school_id
        user.email = input_data.email
        
        # 데이터베이스 업데이트
        db.commit()
        db.refresh(user)
        
        response = JSONResponse(status_code=200, content={
          "status" : 200,
          "isSuccess" : True,
          "message" : f"이메일 인증이 완료되었습니다.",
          "result": None,
        })
        
      else:
        response = JSONResponse(status_code=400, content={
          "status" : 400,
          "isSuccess" : False,
          "message" : verify_response.get('message'),
          "result": None,
        })
      
    except:
      response = JSONResponse(status_code=500, content={
        "status" : 500,
        "isSuccess" : False,
        "message" : f"서버오류 - 관리자에게 문의바람",
        "result": None,
      })
  return response

@users_router.delete('/verification/email', summary='007. 인증된 이메일 삭제')
async def verification_email():
  try:
    headers={
      "Content-Type" : "application/json",
    }
    
    payload={
      "key" : UNIVCERT_API_KEY,
    }
    
    email_response = requests.post(f"{UNIVCERT_URL}/clear", json=payload, headers=headers)
    email_response = email_response.json()
    
    if email_response.get('success') == True:
      response = JSONResponse(status_code=200, content={
        "status" : 200,
        "isSuccess" : True,
        "message" : f"정상적으로 삭제되었습니다.",
        "result": None,
      })
    else:
      response = JSONResponse(status_code=400, content={
        "status" : 400,
        "isSuccess" : False,
        "message" : f"값이 유효하지 않습니다.",
        "result": None,
      })
  except:
    response = JSONResponse(status_code=500, content={
      "status" : 500,
      "isSuccess" : False,
      "message" : f"서버오류 - 관리자에게 문의바람",
      "result": None,
    })
  
  return response

# 유저 전체 리스트 조회 API
@users_router.get('', summary="[TEST용] 가입된 유저들 리스트 조회")
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
      name=user.name,
      user_id=user.user_id,
      user_pw=user.user_pw,
      user_birth=user.user_birth,
      std_id=user.std_id,
      email=user.email,
      major=user.major,
      gender=user.gender,
      phone_number=user.phone_number,
      marketing_term=user.marketing_term,
      sign_url=user.sign_url,
      created_at=user.created_at,
      role=user.role,
      store_id=user.store_id,
      is_school_verified=user.is_school_verified,
      school_selected=user.school_selected,
      school=user.school,
      favorite_stores=favorite_stores,  # 즐겨찾기한 매장 리스트 추가
    )

    # 결과 리스트에 추가
    user_list.append(user_data)

  response = JSONResponse(status_code=200, content={
    "status" : 200,
    "isSuccess" : True,
    "message" : f"정상적으로 조회가 완료되었습니다.",
    "result": [user.model_dump() for user in user_list],
  })

  return response
# return JSONResponse(status_code=200, content={'success' : True, 'message' : '유저들 조회 완료', 'body' : userList})
#   #'_sa_instance_state': <sqlalchemy.orm.state.InstanceState object>는 SQLAlchemy ORM 객체를 그대로 출력하거나 JSON으로 변환하려고 할 대, 자동으로 추가하여 내부상태도 함께 출력됨.
#   # SQLAlchemy 모델 객체를 Pydantic모델로 변환해야함


# 현재 로그인 된 유저 정보 조회
@users_router.get('/me', summary="008. 현재 로그인 된 유저 조회")
async def read_current_user(db: Session = Depends(get_db), token: str = Depends(verify_jwt_token)):
  
  # uid에 해당하는 유저를 조회
  user = db.query(User).filter(User.uid == token.uid).first()

  if not user:
    raise CustomHTTPException(status_code=404, message="로그인 유저를 찾을 수 없습니다.")

  # 유저의 즐겨찾기 매장 가져오기
  favorite_store_records = db.query(UserFavoriteStore).filter(UserFavoriteStore.uid == user.uid).all()
  # Favorite 조회 에러 수정해야 함
  
  # Store 정보 추출 및 StoreSchema로 변환
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

  # UserSchema로 변환할 때 favorite_stores 필드에 매장 리스트 추가
  user_data = UserSchema(
    uid=user.uid,
    name=user.name,
    user_id=user.user_id,
    user_pw=user.user_pw,
    user_birth=user.user_birth,
    std_id=user.std_id,
    email=user.email,
    major=user.major,
    gender=user.gender,
    phone_number=user.phone_number,
    marketing_term=user.marketing_term,
    sign_url=user.sign_url,
    # created_at=user.created_at,
    role=user.role,
    store_id=user.store_id,
    is_school_verified=user.is_school_verified,
    school_selected=user.school_selected,
    school=user.school,
    favorite_stores=favorite_stores,  # 즐겨찾기한 매장 리스트 추가
  )
  
  response = JSONResponse(status_code=200, content={
    "status" : 200,
    "isSuccess" : True,
    "message" : f"정상적으로 조회가 완료되었습니다.",
    "result": user_data.model_dump(),
  })

  return response

@users_router.put('/me/password', summary="010. 현재 로그인된 유저 비밀번호 수정")
async def update_password(current_password: str, new_password: str, db: Session = Depends(get_db), token: str = Depends(verify_jwt_token)):
  
  # uid에 해당하는 유저를 조회
  user = db.query(User).filter(User.uid == token.uid).first()
  
  # 현재 로그인 된 유저 조회
  if not user:
    raise CustomHTTPException(status_code=404, message="로그인 된 유저를 찾을 수 없습니다.")
  
  # 현재 비밀번호가 맞는지 검증
  if not pwd_context.verify(current_password, user.user_pw):
    raise CustomHTTPException(status_code=400, message="현재 비밀번호가 올바르지 않습니다.")
  
  # 새로운 비밀번호와 기존 비밀번호가 동일하면 예외처리
  if pwd_context.verify(new_password, user.user_pw):
    raise CustomHTTPException(status_code=400, message="새로운 비밀번호는 기존 비밀번호와 동일할 수 없습니다.")
  
  hashed_password = pwd_context.hash(new_password)
  user.user_pw = hashed_password
  
  db.commit()
  db.refresh(user)
  
  response = JSONResponse(status_code=200, content={
    "status" : 200,
    "isSuccess" : True,
    "message" : f"비밀번호 수정이 완료되었습니다.",
    "result": None,
  })
  
  return response

@users_router.put('/me/sign', summary="011. 현재 로그인된 유저 사인 수정")
async def update_sign(sign_update_url: UserSignSchema, db: Session = Depends(get_db), token: str = Depends(verify_jwt_token)):
  
  # std_id에 해당하는 유저를 조회
  user = db.query(User).filter(User.uid == token.uid).first()
  
  # 현재 로그인 된 유저 조회
  if not user:
    raise CustomHTTPException(status_code=404, message="로그인 된 유저를 찾을 수 없습니다.")
  
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
    
    sign_url_data = f"/static/{str(user.school.id)}/signatures/{file_name}"
  except Exception as e:
    raise CustomHTTPException(status_code=500, message="서버에러 - 관리자에게 문의바람")
  
  
  user.sign_url = sign_url_data
  
  db.commit()
  db.refresh(user)
  
  response = JSONResponse(status_code=200, content={
    "status" : 200,
    "isSuccess" : True,
    "message" : f"사인 수정이 완료되었습니다.",
    "result": None,
  })
  
  return response


# 유저 한 명 조회 API
@users_router.get('/{user_id}', response_model=UserSchema, summary="[TEST용] 아이디를 통한 유저 조회")
async def read_user(user_id: str, db: Session = Depends(get_db)):
  # std_id에 해당하는 유저를 조회
  user = db.query(User).filter(User.user_id == user_id).first()

  if not user:
    raise CustomHTTPException(status_code=404, message="해당 사용자를 찾을 수 없습니다.")

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
    name=user.name,
    user_id=user.user_id,
    user_pw=user.user_pw,
    user_birth=user.user_birth,
    std_id=user.std_id,
    email=user.email,
    major=user.major,
    gender=user.gender,
    phone_number=user.phone_number,
    marketing_term=user.marketing_term,
    sign_url=user.sign_url,
    # created_at=user.created_at,
    role=user.role,
    store_id=user.store_id,
    is_school_verified=user.is_school_verified,
    school_selected=user.school_selected,
    school=user.school,
    favorite_stores=favorite_stores,  # 즐겨찾기한 매장 리스트 추가
  )

  return user_data

@users_router.delete('/me', summary="009. 현재 로그인 된 유저 삭제")
async def delete_user(pw:str, db: Session = Depends(get_db), token: str = Depends(verify_jwt_token)):
  # user_id에 해당하는 유저를 조회
  user = db.query(User).filter(User.uid == token.uid).first()
  
  # 해당 유저가 존재하지 않으면 404 에러 반환
  if not user:
    raise CustomHTTPException(status_code=404, message="로그인 된 유저를 찾을 수 없습니다.")
  
  if pwd_context.verify(pw, user.user_pw):
    db.delete(user)
    try:
      payload={
        "key" : UNIVCERT_API_KEY
      }
      
      requests.post(f"{UNIVCERT_URL}/clear/{user.email}", json=payload)
    except:
      response = JSONResponse(status_code=500, content={
        "status" : 500,
        "isSuccess" : False,
        "message" : f"서버오류 - 관리자에게 문의바람",
        "result": None,
      })
    db.commit()
  else:
    raise CustomHTTPException(status_code=400, message="비밀번호가 일치하지 않습니다.")

  response = JSONResponse(status_code=200, content={
    "status" : 200,
    "isSuccess" : True,
    "message" : f"유저 삭제가 완료되었습니다.",
    "result": None,
  })
  
  return response