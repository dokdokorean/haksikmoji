from fastapi import APIRouter
from fastapi.responses import JSONResponse


ad_router = APIRouter(
  prefix="/v1/ad"
)


@ad_router.get('', summary="메인 광고 배너")
async def get_main_adbanner():
  
  banner_list = [
    {
      'id': 1,
      'imageUrl': '/images/advertisement/main/banner/ad-1.png',
      'path': 'https://veil-value-ae4.notion.site/7a20e6e093d94887a4b438fb3ec5c9e1',
    }
  ]
  
  return JSONResponse(status_code=200, content={'success' : True, 'body' : banner_list})