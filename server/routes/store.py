from fastapi import APIRouter, HTTPException, Depends, Response
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from server.models import Store, Notice, User, get_skt_time, StoreHours, DayOfWeek
from server.schemas import StoreSchema, StoreListSchema, StoreNoticeSchema, StoreUpdateNoticeSchema, StoreUpdateSchema
# from server.db import get_haksik_db_connection
from server.db import get_db
from server.auth import verify_jwt_token


store_router = APIRouter(
  prefix="/store"
)


@store_router.get('', response_model=list[StoreListSchema], summary="전체 매장 조회")
async def get_store_list(db: Session = Depends(get_db)):
  # 연세대 미래
  store_list = db.query(Store).filter(Store.school_id == 1).all()
    
  return store_list


# 음식점 매장 조회
@store_router.get('/food', response_model=list[StoreListSchema], summary="음식점 매장 조회")
async def get_food_store_list(db: Session = Depends(get_db)):
  # 연세대 미래
  store_list = db.query(Store).filter(Store.school_id == 1, Store.category_id == 1).all()
    
  return store_list

# 카페 매장 조회
@store_router.get('/cafe', response_model=list[StoreListSchema], summary="카페 매장 조회")
async def get_cafe_store_list(db: Session = Depends(get_db)):
  # 연세대 미래
  store_list = db.query(Store).filter(Store.school_id == 1, Store.category_id == 2).all()
    
  return store_list

# 편의점 매장 조회
@store_router.get('/cafe', response_model=list[StoreListSchema], summary="카페 매장 조회")
async def get_con_store_list(db: Session = Depends(get_db)):
  # 연세대 미래
  store_list = db.query(Store).filter(Store.school_id == 1, Store.category_id == 3).all()
    
  return store_list

# 편의시설 매장 조회
@store_router.get('/facilities', response_model=list[StoreListSchema], summary="편의시설 매장 조회")
async def get_con_store_list(db: Session = Depends(get_db)):
  # 연세대 미래
  store_list = db.query(Store).filter(Store.school_id == 1, Store.category_id.in_([4,5,6,7,8])).all()
    
  return store_list



@store_router.get('/{store_id}', response_model=StoreSchema, summary="각 매장 상세 정보 조회")
async def get_store(store_id: int, db:Session = Depends(get_db)):
  store = db.query(Store).filter(Store.sid == store_id).first()
  
  if not store:
    raise HTTPException(status_code=400, detail='없는 매장입니다')
  
  # store_hours를 Dict로 변환
  store_hours_dict = {}
  for store_hour in store.store_hours:
    day_of_week = store_hour.day_of_week.name  # 요일 이름 가져오기
    store_hours_dict[day_of_week] = {
      'runing_time': {
        'opening_time': store_hour.opening_time.strftime('%H:%M') if store_hour.opening_time else None,
        'closing_time': store_hour.closing_time.strftime('%H:%M') if store_hour.closing_time else None
      },
      'break_time': {
        'break_start_time': store_hour.break_start_time.strftime('%H:%M') if store_hour.break_start_time else None,
        'break_exit_time': store_hour.break_exit_time.strftime('%H:%M') if store_hour.break_exit_time else None
      }
    }
  
  result_store = {
    'sid': store.sid,
    'store_name': store.store_name,
    'store_number': store.store_number,
    'store_location': store.store_location,
    'is_open': store.is_open,
    'store_img_url': store.store_img_url,
    'category': store.category,
    'store_hours': store_hours_dict,  # Dict 형식으로 변환된 store_hours 반환
    'store_notice' : store.store_notice
  }

    # 최종 데이터를 Pydantic 모델에 맞게 반환
  return result_store


@store_router.put('/{store_id}', response_model=StoreSchema, summary="각 매장 상세 정보 수정")
async def update_store(store_id: int, store_data: StoreUpdateSchema, db: Session = Depends(get_db)):
  # 해당 매장을 조회
  store = db.query(Store).filter(Store.sid == store_id).first()

  if not store:
      raise HTTPException(status_code=400, detail='없는 매장입니다')

  # 전화번호와 위치 업데이트
  if store_data.store_number is not None:
      store.store_number = store_data.store_number
  if store_data.store_location is not None:
      store.store_location = store_data.store_location

  # 운영시간 업데이트
  if store_data.store_hours:
      for updated_hours in store_data.store_hours:
        # day_of_week.name을 이용하여 day_of_week_id 찾기
        day_of_week = db.query(DayOfWeek).filter(DayOfWeek.name == updated_hours.date).first()

        if not day_of_week:
            raise HTTPException(status_code=400, detail=f'잘못된 요일: {updated_hours.date}')

        # store_hours에 맞는 요일 찾기
        store_hour = db.query(StoreHours).filter(
            StoreHours.store_id == store.sid,
            StoreHours.day_of_week_id == day_of_week.id  # 찾은 day_of_week ID 사용
        ).first()

        # store_hours가 있는 경우 업데이트
        if store_hour:
          # 운영시간 업데이트
          store_hour.opening_time = updated_hours.content.runing_time.opening_time if updated_hours.content.runing_time.opening_time is not None else None
          store_hour.closing_time = updated_hours.content.runing_time.closing_time if updated_hours.content.runing_time.closing_time is not None else None

          # 휴식시간 업데이트
          store_hour.break_start_time = updated_hours.content.break_time.break_start_time if updated_hours.content.break_time.break_start_time is not None else None
          store_hour.break_exit_time = updated_hours.content.break_time.break_exit_time if updated_hours.content.break_time.break_exit_time is not None else None
        else:
            # store_hours 데이터가 없으면 새로운 레코드 추가
            new_store_hour = StoreHours(
              store_id=store.sid,
              day_of_week_id=day_of_week.id,
              opening_time=updated_hours.content.runing_time.opening_time if updated_hours.content.runing_time.opening_time is not None else None,
              closing_time=updated_hours.content.runing_time.closing_time if updated_hours.content.runing_time.closing_time is not None else None,
              break_start_time=updated_hours.content.break_time.break_start_time if updated_hours.content.break_time.break_start_time is not None else None,
              break_exit_time=updated_hours.content.break_time.break_exit_time if updated_hours.content.break_time.break_exit_time is not None else None
            )
            db.add(new_store_hour)

  # 변경사항 커밋
  db.commit()

  return JSONResponse(status_code=200, content={'success' : True, 'message' : '매장 정보가 정상적으로 수정되었습니다!'})


# 공지 관련
@store_router.get('/{store_id}/notice', response_model=list[StoreNoticeSchema], summary="각 매장 공지사항 조회")
async def add_notice(store_id: int, db:Session = Depends(get_db)):
  
  notices = db.query(Notice).filter(Notice.store_id == store_id).all()
  
  return notices
  

@store_router.post('/{store_id}/notice', summary="각 매장 공지사항 등록")
async def get_notice(store_id: int, noticeData: StoreUpdateNoticeSchema, db:Session = Depends(get_db), current_user: User = Depends(verify_jwt_token)):
  
  if current_user.role != 2:
    raise HTTPException(status_code=403, detail="해당 작업을 수행할 권한이 없습니다.")
  
  new_notice = Notice(
    title=noticeData.title,
    store_id=store_id,
    content=noticeData.content,
    created_at=get_skt_time(),
    updated_at=get_skt_time(),
  )
  
  db.add(new_notice)
  db.commit()
  db.refresh(new_notice)
  
  return JSONResponse(status_code=200, content={'success' : True, 'message' : '정상적으로 수정되었습니다!'})

@store_router.put('/{store_id}/notice/{notice_id}', summary="각 매장 공지사항 수정")
async def update_notice(store_id: int, notice_id:int, noticeData:StoreUpdateNoticeSchema, db:Session = Depends(get_db), current_user: User = Depends(verify_jwt_token)):
  
  if current_user.role != 2:
    raise HTTPException(status_code=403, detail="해당 작업을 수행할 권한이 없습니다.")
  
  notice = db.query(Notice).filter(Notice.store_id == store_id, Notice.id == notice_id).first()
  
  if not notice:
    raise HTTPException(status_code=400, detail='해당 공지사항이 존재하지 않습니다!')

  notice.title = noticeData.title
  notice.content = noticeData.content
  notice.updated_at = get_skt_time()
  
  db.commit()
  
  return JSONResponse(status_code=200, content={'success' : True, 'message' : '정상적으로 수정되었습니다!'})

@store_router.delete('/{store_id}/notice/{notice_id}', summary="각 매장 공지사항 삭제")
async def delete_notice(store_id: int, notice_id:int, db:Session = Depends(get_db), current_user: User = Depends(verify_jwt_token)):

  # 사장님이 이 매장에 해당하는 사장님인지 체크하는 로직도 짜야할 것
  
  if current_user.role != 2:
    raise HTTPException(status_code=403, detail="해당 작업을 수행할 권한이 없습니다.")
  
  notice = db.query(Notice).filter(Notice.store_id == store_id, Notice.id == notice_id).first()
  
  if not notice:
    raise HTTPException(status_code=400, detail='해당 공지사항이 존재하지 않습니다!')
  
  
  db.delete(notice)
  db.commit()
  
  return JSONResponse(status_code=200, content={'success' : True, 'message' : '정상적으로 삭제되었습니다!'})
  
  