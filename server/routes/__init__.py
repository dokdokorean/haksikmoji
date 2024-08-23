from fastapi import APIRouter
from .haksik import haksik_router
from .users import users_router

router = APIRouter()

@router.get('')
async def get_root():
  return {'message' : 'API Connected'}

router.include_router(haksik_router, tags=["학식 API"])
router.include_router(users_router, tags=["로그인/회원가입 API"])