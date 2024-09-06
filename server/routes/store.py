from fastapi import APIRouter, HTTPException, Depends, Response
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from server.models import Store
from server.schemas import StoreSchema
# from server.db import get_haksik_db_connection
from server.db import get_db


store_router = APIRouter(
  prefix="/store"
)


@store_router.get('/1', response_model=list[StoreSchema], summary="전체 매장 조회")
async def get_store_list(db: Session = Depends(get_db)):
  # 연세대 미래
  store_list = db.query(Store).filter(Store.school_id == 1).all()
    
  return store_list