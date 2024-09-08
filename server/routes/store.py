from fastapi import APIRouter, HTTPException, Depends, Response
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from server.models import Store, Notice, User, get_skt_time
from server.schemas import StoreSchema, StoreListSchema, StoreNoticeSchema, StoreUpdateNoticeSchema
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

@store_router.get('/{store_id}', response_model=StoreSchema, summary="각 매장 상세 정보 조회")
async def get_store(store_id: int, db:Session = Depends(get_db)):
  store = db.query(Store).filter(Store.sid == store_id).first()
  
  if not store:
    raise HTTPException(status_code=400, detail='없는 매장입니다')
  
  return store


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
  
  