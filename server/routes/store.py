from fastapi import APIRouter, HTTPException, Depends, Response
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
# from server.models import Store, Notice, User, get_skt_time, StoreHours, DayOfWeek
# from server.schemas import StoreSchema, StoreListSchema, StoreNoticeSchema, StoreUpdateNoticeSchema, StoreUpdateSchema
# from server.db import get_haksik_db_connection
from server.schemas import StoreDetailSchema, StoreListSchema, StoreUpdateSchema, StoreUpdateNoticeSchema 
from server.models import Store, DayOfWeek, StoreHours, StoreNotice, User
from fastapi.security.api_key import APIKeyHeader
from server.db import get_db
from server.auth import verify_jwt_token
from server.utils import get_skt_time


store_router = APIRouter(
  prefix="/v1/store"
)

@store_router.get('', response_model=list[StoreListSchema],summary="전체 매장 조회")
async def get_store_all(db: Session = Depends(get_db)):
  
  store_all = db.query(Store).filter(Store.school_id == 1).all()
  
  return store_all


# 음식점 매장 조회
@store_router.get('/food', response_model=list[StoreListSchema], summary="카페 매장 조회")
async def get_cafe_store_list(db: Session = Depends(get_db)):
  # 연세대 미래
  store_list = db.query(Store).filter(Store.school_id == 1, Store.category_id == 2).all()
    
  return store_list

# 카페 매장 조회
@store_router.get('/cafe', response_model=list[StoreListSchema], summary="카페 매장 조회")
async def get_cafe_store_list(db: Session = Depends(get_db)):
  # 연세대 미래
  store_list = db.query(Store).filter(Store.school_id == 1, Store.category_id == 2).all()
    
  return store_list

# 편의점 매장 조회
@store_router.get('/convenience', response_model=list[StoreListSchema], summary="편의점 매장 조회")
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


@store_router.get('/{store_id}', response_model=StoreDetailSchema, summary="매장 상세 정보 조회")
async def get_store_detail(store_id: str ,db: Session = Depends(get_db)):
  
  store = db.query(Store).filter(Store.sid == store_id).first()
  
  store_hours_dict = {}
  for store_hour in store.store_hours:
    day_of_week = store_hour.day_of_week.name
    store_hours_dict[day_of_week] = {
      'running_time' : {
        'opening_time' : store_hour.opening_time.strftime('%H:%M') if store_hour.opening_time else None,
        'closing_time' : store_hour.closing_time.strftime('%H:%M') if store_hour.closing_time else None
      },
      'break_time' : {
        'break_start_time' : store_hour.break_start_time.strftime('%H:%M') if store_hour.break_start_time else None,
        'break_exit_time' : store_hour.break_exit_time.strftime('%H:%M') if store_hour.break_exit_time else None,
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
    'store_hours': store_hours_dict,
    'store_notice': store.store_notice
  }
  
  return result_store

@store_router.put('/{store_id}', summary="각 매장 상세 정보 수정")
async def update_store(store_id: int, store_data: StoreUpdateSchema, db: Session = Depends(get_db)):
  store = db.query(Store).filter(Store.sid == store_id).first()
  
  if not store:
    raise HTTPException(status_code=400, detail='없는 매장입니다')

  if store_data.store_number is not None:
    store.store_number = store_data.store_number
  if store_data.store_location is not None:
    store.store_location = store_data.store_location
  
  if store_data.store_hours:
    for updated_hours in store_data.store_hours:
      day_of_week = db.query(DayOfWeek).filter(DayOfWeek.name == updated_hours.date).first()
      
      if not day_of_week:
        raise HTTPException(status_code=400, detail=f'잘못된 요일: {updated_hours.date}')

      store_hour = db.query(StoreHours).filter(StoreHours.store_id == store.sid, StoreHours.day_of_week_id == day_of_week.id).first()
      
      if store_hour:
        store_hour.opening_time = updated_hours.content.running_time.opening_time if updated_hours.content.running_time.opening_time is not None else None
        store_hour.closing_time = updated_hours.content.running_time.closing_time if updated_hours.content.running_time.closing_time is not None else None
        
        store_hour.break_start_time = updated_hours.content.break_time.break_start_time if updated_hours.content.break_time.break_start_time is not None else None
        store_hour.break_exit_time = updated_hours.content.break_time.break_exit_time if updated_hours.content.break_time.break_exit_time is not None else None
        
  store.update_is_open(db)
  
  db.commit()
  return JSONResponse(status_code=200, content={'success' : True, 'message' : '정상적으로 수정되었습니다!'})


# *공지 관련*
@store_router.get('/{store_id}/notice', summary="각 매장 공지사항 조회")
async def get_notice_store(store_id: int, db: Session = Depends(get_db)):
  
  notice_list = db.query(StoreNotice).filter(StoreNotice.store_id == store_id).all()
  
  return notice_list


@store_router.post('/{store_id}/notice', summary="각 매장 공지사항 등록")
async def add_notice(store_id: int, notice_data: StoreUpdateNoticeSchema, db:Session = Depends(get_db)):
  # 해당 사장님
  # if current_user.role != 2:
  #   raise HTTPException(status_code=403, detail="해당 작업을 수행할 권한이 없습니다.")
  
  new_notice = StoreNotice(
    title=notice_data.title,
    store_id=store_id,
    content=notice_data.content,
    created_at=get_skt_time(),
    updated_at=get_skt_time(),
  )
  
  db.add(new_notice)
  db.commit()
  db.refresh(new_notice)
    
  return JSONResponse(status_code=200, content={'success' : True, 'message' : '정상적으로 생성되었습니다!'})



@store_router.get('/{store_id}/notice/{notice_id}', summary="각 매장의 해당하는 공지사항 하나 조회")
async def get_notice(store_id: int, notice_id: int, db: Session = Depends(get_db)):
  
  notice = db.query(StoreNotice).filter(StoreNotice.store_id == store_id, StoreNotice.id == notice_id).first()
  
  if not notice:
    raise HTTPException(status_code=400, detail="해당 공지사항이 존재하지 않습니다!")
  
  
  return notice

@store_router.put('/{store_id}/notice/{notice_id}', summary="각 매장의 해당하는 공지사항 하나 수정")
async def update_notice(store_id: int, notice_id: int, notice_data: StoreUpdateNoticeSchema, db: Session = Depends(get_db)):
  
  notice = db.query(StoreNotice).filter(StoreNotice.store_id == store_id, StoreNotice.id == notice_id).first()
  
  if not notice:
    raise HTTPException(status_code=400, detail="해당 공지사항이 존재하지 않습니다!")

  notice.title = notice_data.title
  notice.content = notice_data.content,
  notice.updated_at = get_skt_time()
  
  db.commit()
  
  return JSONResponse(status_code=200, content={'success' : True, 'message' : '정상적으로 수정되었습니다!'})
  

@store_router.delete('/{store_id}/notice/{notice_id}', summary="각 매장 공지사항 삭제")
async def delete_notice(store_id: int, notice_id:int, db:Session = Depends(get_db)):

  # 사장님이 이 매장에 해당하는 사장님인지 체크하는 로직도 짜야할 것
  
  # if current_user.role != 2:
  #   raise HTTPException(status_code=403, detail="해당 작업을 수행할 권한이 없습니다.")
  
  notice = db.query(StoreNotice).filter(StoreNotice.store_id == store_id, StoreNotice.id == notice_id).first()
  
  if not notice:
    raise HTTPException(status_code=400, detail='해당 공지사항이 존재하지 않습니다!')
  
  
  db.delete(notice)
  db.commit()
  
  return JSONResponse(status_code=200, content={'success' : True, 'message' : '정상적으로 삭제되었습니다!'})
  
  