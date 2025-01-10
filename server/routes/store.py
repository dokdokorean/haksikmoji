from sqlalchemy import or_, and_, distinct
from fastapi import APIRouter, HTTPException, Depends, Response, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session, aliased
from sqlalchemy import desc
from server.schemas import StoreDetailSchema, StoreListSchema, StoreUpdateSchema, StoreUpdateNoticeSchema, StoreSearchSchema
from server.models import Store, DayOfWeek, StoreHours, StoreNotice, User, StoreCategory, UserFavoriteStore
from fastapi.security.api_key import APIKeyHeader
from server.db import get_db
from server.auth import verify_jwt_token
from server.utils import get_skt_time


store_router = APIRouter(
  prefix="/v1/store"
)


# 전체 매장 조회 API
@store_router.get('', response_model=list[StoreListSchema],summary="전체 매장 조회")
async def get_store_all(db: Session = Depends(get_db)):
  
  store_all = db.query(Store).filter(Store.school_id == 1).all()
  
  return store_all


# *검색어 자동완성 관련*
@store_router.get('/search-keyword', response_model=list[StoreSearchSchema], summary="검색 자동 완성 키워드 10개 조회")
async def search_keyword_store(query: str, db: Session = Depends(get_db), limit: int = 10):
  
  if not query:
      raise HTTPException(status_code=400, detail="")

  category_alias = aliased(StoreCategory)
  
  stores = db.query(Store).join(category_alias, Store.category).filter(
      and_(
          Store.school_id == 1,
          or_(
              Store.store_name.ilike(f"%{query}%")
          )
      )
  ).group_by(Store.store_name).limit(limit).all()

  return stores

# 매장 키워드 검색하여 매장 조회
@store_router.get('/search', response_model=list[StoreListSchema], summary="검색한 매장 조회")
async def search_keyword_store(query: str, db: Session = Depends(get_db)):
  
  if not query:
      raise HTTPException(status_code=400, detail="")

  category_alias = aliased(StoreCategory)
  
  stores = db.query(Store).join(category_alias, Store.category).filter(
    and_(
      Store.school_id == 1,
      or_(
          Store.store_name.ilike(f"%{query}%"),
          category_alias.main_category.ilike(f"%{query}%"),
      )
    )
  ).all()

  return stores

# 음식점 카테고라 매장 조회
@store_router.get('/food', response_model=list[StoreListSchema], summary="음식점 매장 조회")
async def get_cafe_store_list(db: Session = Depends(get_db)):
  # 연세대 미래
  store_list = db.query(Store).filter(Store.school_id == 1, Store.category_id == 1).all()
    
  return store_list

# 카페 카테고리 매장 조회
@store_router.get('/cafe', response_model=list[StoreListSchema], summary="카페 매장 조회")
async def get_cafe_store_list(db: Session = Depends(get_db)):
  # 연세대 미래
  store_list = db.query(Store).filter(Store.school_id == 1, Store.category_id == 2).all()
    
  return store_list

# 편의점 카테고리 매장 조회
@store_router.get('/convenience', response_model=list[StoreListSchema], summary="편의점 매장 조회")
async def get_con_store_list(db: Session = Depends(get_db)):
  # 연세대 미래
  store_list = db.query(Store).filter(Store.school_id == 1, Store.category_id == 3).all()
    
  return store_list

# 편의시설 카테고리 매장 조회
@store_router.get('/facilities', response_model=list[StoreListSchema], summary="편의시설 매장 조회")
async def get_con_store_list(db: Session = Depends(get_db)):
  # 연세대 미래
  store_list = db.query(Store).filter(Store.school_id == 1, Store.category_id.in_([4,5,6,7,8])).all()
    
  return store_list

# 매장 id로 상세정보 조회
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
  
  categories = []
  for category in store.menu_categories:
    menus = []
    for menu in category.menus:
      options=[]
      for option in menu.options:
        options.append({
          'option_name': option.option_name,
          'price': option.price
        })
      
      menus.append({
        'menu_name': menu.menu_name,
        'menu_image_url': menu.menu_image_url,
        'options': options
      })
    
    categories.append({
      'category_name': category.category_name,
      'menus': menus
    })
  
  sorted_notices = sorted(store.store_notice, key=lambda notice: (notice.is_pinned, notice.created_at), reverse=True)
  
  result_store = {
    'sid': store.sid,
    'store_name': store.store_name,
    'store_number': store.store_number,
    'store_location': store.store_location,
    'is_open': store.is_open,
    'store_thumb_url': store.store_thumb_url,
    'store_banner_url': store.store_banner_url,
    'category': store.category,
    'store_hours': store_hours_dict,
    'store_notice': sorted_notices,
    'menu': categories
  }
  
  return result_store

# 매장 정보 수정 (현재는 매장 시간만 수정 가능)
# TODO : 전화번호, 배너이미지, 썸네일 이미지 수정가능하게
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

# TODO : 매장 메뉴 수정 API 개발 예정

# *공지 관련*

# 매장 id에 따른 각 매장 공지사항 조회
@store_router.get('/{store_id}/notice', summary="각 매장 공지사항 조회")
async def get_notice_store(store_id: int, db: Session = Depends(get_db)):
    notice_list = (
        db.query(StoreNotice)
        .filter(StoreNotice.store_id == store_id)
        .order_by(desc(StoreNotice.is_pinned), desc(StoreNotice.created_at))
        .all()
    )
    return notice_list


# 매장 id에 따른 각 매장 공지사항 등록
@store_router.post('/{store_id}/notice', summary="각 매장 공지사항 등록")
async def add_notice(store_id: int, notice_data: StoreUpdateNoticeSchema, confirm: bool = Query(False), db:Session = Depends(get_db), token: str = Depends(verify_jwt_token)):
  
  # 사장님이 아닐 때
  if token.role != 2:
    raise HTTPException(status_code=403, detail="해당 작업을 수행할 권한이 없습니다.")
  
  user_store = db.query(User).filter(User.uid == token.uid).first()
  
  # 해당 매장 사장님이 아닐 때
  if not user_store or user_store.store_id != store_id:
    raise HTTPException(status_code=403, detail="해당 매장에 대한 접근 권한이 없습니다.")
  
  # 해당 공지사항을 고정하려고하는데 이미 고정된 공지사항이 있을 경우
  if notice_data.is_pinned:
    pinned_notice = db.query(StoreNotice).filter(StoreNotice.store_id == store_id, StoreNotice.is_pinned == True).first()
    # 기존 고정 공지가 있고, 확인 요청(confirm)이 없는 경우 사용자에게 선택 요청
    if pinned_notice and not confirm:
      return JSONResponse(
        status_code=409,
        content={
          'success': False,
          'message': '이미 고정된 공지사항이 있습니다. 기존 공지를 해제하고 새 공지를 고정하시겠습니까?',
        }
      )

    # confirm이 True인 경우 기존 공지 해제
    if pinned_notice and confirm:
      pinned_notice.is_pinned = False
      db.add(pinned_notice)
  
  new_notice = StoreNotice(
    title=notice_data.title,
    store_id=store_id,
    is_pinned=notice_data.is_pinned,
    content=notice_data.content,
    created_at=get_skt_time(),
    updated_at=get_skt_time(),
  )
  
  db.add(new_notice)
  db.commit()
  db.refresh(new_notice)
    
  return JSONResponse(status_code=200, content={'success' : True, 'message' : '정상적으로 생성되었습니다!'})


# 매장 id와 공지사항 id에 따른 공지사항 조회
@store_router.get('/{store_id}/notice/{notice_id}', summary="각 매장의 해당하는 공지사항 하나 조회")
async def get_notice(store_id: int, notice_id: int, db: Session = Depends(get_db)):
  
  notice = db.query(StoreNotice).filter(StoreNotice.store_id == store_id, StoreNotice.id == notice_id).first()
  
  if not notice:
    raise HTTPException(status_code=400, detail="해당 공지사항이 존재하지 않습니다!")
  
  
  return notice


# 공지사항 id에 따른 공지사항 수정
@store_router.put('/{store_id}/notice/{notice_id}', summary="각 매장의 해당하는 공지사항 하나 수정")
async def update_notice(store_id: int, notice_id: int, notice_data: StoreUpdateNoticeSchema, confirm: bool = Query(False), db: Session = Depends(get_db), token: str = Depends(verify_jwt_token)):
  
  # 사장님이 아닐 때
  if token.role != 2:
    raise HTTPException(status_code=403, detail="해당 작업을 수행할 권한이 없습니다.")
  
  user_store = db.query(User).filter(User.uid == token.uid).first()
  
  # 해당 매장 사장님이 아닐 때
  if not user_store or user_store.store_id != store_id:
    raise HTTPException(status_code=403, detail="해당 매장에 대한 접근 권한이 없습니다.")
  
  notice = db.query(StoreNotice).filter(StoreNotice.store_id == store_id, StoreNotice.id == notice_id).first()
  
  if not notice:
    raise HTTPException(status_code=400, detail="해당 공지사항이 존재하지 않습니다!")

  # 공지사항을 고정하려는 경우, 이미 고정된 공지가 있는지 확인
  if notice_data.is_pinned:
    pinned_notice = db.query(StoreNotice).filter(StoreNotice.store_id == store_id, StoreNotice.is_pinned == True, StoreNotice.id != notice_id).first()
    
    # 기존 고정 공지가 있고, 확인 요청이 없는 경우
    if pinned_notice and not confirm:
      return JSONResponse(
        status_code=409,
        content={
          'success': False,
          'message': '이미 고정된 공지사항이 있습니다. 기존 공지를 해제하고 새 공지를 고정하시겠습니까?',
        }
      )
    
    # confirm이 True인 경우 기존 고정 공지 해제
    if pinned_notice and confirm:
      pinned_notice.is_pinned = False
      db.add(pinned_notice)

  notice.title = notice_data.title
  notice.content = notice_data.content
  notice.is_pinned = notice_data.is_pinned
  notice.updated_at = get_skt_time()
  
  db.commit()
  
  return JSONResponse(status_code=200, content={'success' : True, 'message' : '정상적으로 수정되었습니다!'})
  
# 공지사항 id에 따른 공지사항 삭제
@store_router.delete('/{store_id}/notice/{notice_id}', summary="각 매장 공지사항 삭제")
async def delete_notice(store_id: int, notice_id:int, db:Session = Depends(get_db), token: str = Depends(verify_jwt_token)):

  # 사장님이 아닐 때
  if token.role != 2:
    raise HTTPException(status_code=403, detail="해당 작업을 수행할 권한이 없습니다.")
  
  user_store = db.query(User).filter(User.uid == token.uid).first()
  
  # 해당 매장 사장님이 아닐 때
  if not user_store or user_store.store_id != store_id:
    raise HTTPException(status_code=403, detail="해당 매장에 대한 접근 권한이 없습니다.")
  
  notice = db.query(StoreNotice).filter(StoreNotice.store_id == store_id, StoreNotice.id == notice_id).first()
  
  if not notice:
    raise HTTPException(status_code=400, detail='해당 공지사항이 존재하지 않습니다!')
  
  
  db.delete(notice)
  db.commit()
  
  return JSONResponse(status_code=200, content={'success' : True, 'message' : '정상적으로 삭제되었습니다!'})
  

# 매장 즐겨찾기 추가
@store_router.post('/{store_id}/favorite', summary="매장 즐겨찾기 추가")
async def create_favorite_store(store_id: int, db: Session = Depends(get_db), token: str = Depends(verify_jwt_token)):
    # JWT 토큰을 통해 유저 확인
    current_user = db.query(User).filter(User.uid == token.uid).first()

    if not current_user:
        raise HTTPException(status_code=400, detail="유효하지 않은 사용자입니다.")
    
    # print(current_user.std_id)

    # 해당 매장이 존재하는지 확인
    store = db.query(Store).filter(Store.sid == store_id).first()

    if not store:
        raise HTTPException(status_code=400, detail="해당 매장이 존재하지 않습니다.")

    # 이미 즐겨찾기에 추가된 매장인지 확인
    existing_favorite = db.query(UserFavoriteStore).filter(
        UserFavoriteStore.uid == current_user.uid,
        UserFavoriteStore.store_id == store_id
    ).first()

    if existing_favorite:
        raise HTTPException(status_code=400, detail="이미 즐겨찾기한 매장입니다.")

    # 즐겨찾기 추가
    favorite = UserFavoriteStore(uid=current_user.uid, store_id=store.sid, created_at=get_skt_time())
    db.add(favorite)
    db.commit()

    return JSONResponse(status_code=200, content={'success': True, 'message': '즐겨찾기에 추가되었습니다!'})

# 매장 즐겨찾기 삭제
@store_router.delete('/{store_id}/favorite', summary="매장 즐겨찾기 삭제")
async def delete_favorite_store(store_id: int, db: Session = Depends(get_db), token: str = Depends(verify_jwt_token)):
    # JWT 토큰을 통해 유저 확인
    current_user = db.query(User).filter(User.uid == token.uid).first()

    if not current_user:
        raise HTTPException(status_code=400, detail="유효하지 않은 사용자입니다.")
    
    # 해당 매장이 존재하는지 확인
    store = db.query(Store).filter(Store.sid == store_id).first()

    if not store:
        raise HTTPException(status_code=400, detail="해당 매장이 존재하지 않습니다.")

    # 즐겨찾기에 이미 등록된 매장인지 확인
    existing_favorite = db.query(UserFavoriteStore).filter(
        UserFavoriteStore.uid == current_user.uid,
        UserFavoriteStore.store_id == store_id
    ).first()

    if not existing_favorite:
        raise HTTPException(status_code=400, detail="즐겨찾기에 등록되지 않은 매장입니다.")

    # 즐겨찾기에서 매장 삭제
    db.delete(existing_favorite)
    db.commit()

    return JSONResponse(status_code=200, content={'success': True, 'message': '즐겨찾기에서 삭제되었습니다.'})