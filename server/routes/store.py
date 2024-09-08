from fastapi import APIRouter, HTTPException, Depends, Response
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from server.models import Store
from server.schemas import StoreSchema, StoreListSchema
# from server.db import get_haksik_db_connection
from server.db import get_db


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
  
  return store
  