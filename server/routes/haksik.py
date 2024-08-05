from fastapi import APIRouter
from fastapi.responses import JSONResponse

haksik_router = APIRouter(
  prefix="/haksik"
)

@haksik_router.get('')
async def get_haksik():
  haksikData = {
    'menu' : {
      # 앞에서부터 중식, A, B, C, D, E, F
      'MON' : ['참치마요', '사골우거지해장국', '청국장찌개', '소불고기덮밥', '가츠동', '마제소바', '제육덮밥'],
      'TUE' : ['참치마요', '비지찌개', '소고기무국', '고추참치마요덮밥', '후랑크갈릭볶음밥', '낙불새덮밥 *(낙지, 불고기, 새우)', '닭개장'],
      'WED' : ['참치마요', '돼지고기김치찌개', '우삼겹된장찌개', '', '', '소고기유부볶음밥', ''],
      'THU' : ['', '짬뽕', '해물우동', '돼지순두부찌개', '일식카레*가라아게', '갈비찜', ''],
      'FRI': ['', '차슈덮밥', '오꼬노미야끼+미니소바', '사케동', '명란마요덮밥', '', ''],
    }
  }
  return JSONResponse(status_code=200, content={'success' : True, 'body' : haksikData})